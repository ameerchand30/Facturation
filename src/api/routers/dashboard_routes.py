from sqlalchemy.orm import Session
from sqlalchemy import func,cast, Date, and_, distinct
from typing import Optional, List, Dict, Any
from datetime import datetime,timedelta
from fastapi import APIRouter, Depends, Request, HTTPException,Query

from src.core.shared import templates
from src.database import get_db

from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType,ClientProfile,User
from src.api.models.invoice import Invoice, InvoiceItem
from src.api.models.product import ProductModel
from src.api.models.client import Clients

from src.api.dependencies.auth import get_current_user, require_user_type

# to show dashboard with each enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile



dashboard_router = APIRouter(tags=["Dashboard"])

# Client dashboard
@dashboard_router.get("/client/dashboard", name="client_dashboard")
async def client_dashboard(request: Request, user: dict = Depends(require_user_type(UserType.CLIENT))):
    return templates.TemplateResponse(
        "pages/User/dashboard.html",
        {
            "request": request,
            "current_page": "dashboard",
            "user": user
        }
    )
@dashboard_router.get("/client/dashboard/data", name="client_dashboard_data")
async def client_dashboard_data(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.CLIENT)),
    date_from: str = Query(None),
    date_to: str = Query(None),
    enterprise_id: Optional[int] = Query(None),
    period: str = Query('month', enum=['day', 'week', 'month'])
):
    # Get client profile
    user = db.query(User).filter(User.id == user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Client profile not found")

    client_profile = db.query(Clients).filter(Clients.email == user.email).first()
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")
    

    # Parse dates
    end_date = datetime.strptime(date_to, "%Y-%m-%d") if date_to else datetime.now()
    start_date = datetime.strptime(date_from, "%Y-%m-%d") if date_from else end_date - timedelta(days=30)

    # Base query filters
    base_filters = [
        Invoice.client_id == client_profile.id,
        Invoice.creation_date.between(start_date, end_date)
    ]
    if enterprise_id:
        base_filters.append(Invoice.enterprise_profile_id == enterprise_id)

    # Get associated enterprises
    enterprises = (
        db.query(EnterpriseProfile)
        .join(Invoice, Invoice.enterprise_profile_id == EnterpriseProfile.id)
        .filter(Invoice.client_id == client_profile.id)
        .distinct()
        .all()
    )

    # Calculate basic metrics
    metrics = db.query(
        func.count(distinct(Invoice.id)).label('total_transactions'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('total_expenditure'),
        func.avg(InvoiceItem.quantity * InvoiceItem.unit_price).label('avg_transaction')
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        *base_filters
    ).first()

    # Calculate expenditure trends
    if period == 'day':
        group_by = func.date(Invoice.creation_date)
        date_format = '%Y-%m-%d'
    elif period == 'week':
        group_by = func.date_trunc('week', Invoice.creation_date)
        date_format = '%Y-W%W'
    else:  # month
        group_by = func.date_trunc('month', Invoice.creation_date)
        date_format = '%Y-%m'

    expenditure_trend = (
        db.query(
            group_by.label('date'),
            func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('amount')
        )
        .join(InvoiceItem, Invoice.id == InvoiceItem.invoice_id)
        .filter(*base_filters)
        .group_by('date')
        .order_by('date')
        .all()
    )

    # Calculate enterprise distribution
    enterprise_distribution = (
        db.query(
            EnterpriseProfile.company_name,
            func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('amount')
        )
        .join(Invoice, Invoice.enterprise_profile_id == EnterpriseProfile.id)
        .join(InvoiceItem, Invoice.id == InvoiceItem.invoice_id)
        .filter(*base_filters)
        .group_by(EnterpriseProfile.company_name)
        .order_by(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).desc())
        .all()
    )

    # Calculate transaction activity by day of week
    transaction_activity = (
        db.query(
            func.extract('dow', Invoice.creation_date).label('day_of_week'),
            func.count(distinct(Invoice.id)).label('count')
        )
        .filter(*base_filters)
        .group_by('day_of_week')
        .order_by('day_of_week')
        .all()
    )

    # Calculate top expenses by category (assuming you have a category field)
    top_expenses = (
        db.query(
            InvoiceItem.product_id,
            func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('amount')
        )
        .join(Invoice)
        .filter(*base_filters)
        .group_by(InvoiceItem.product_id)
        .order_by(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).desc())
        .limit(5)
        .all()
    )

        # Get top products by usage
    top_products = (
        db.query(
            ProductModel.name.label('product_name'),  # Changed from Product to ProductModel
            func.count(InvoiceItem.id).label('count')
        )
        .join(InvoiceItem, InvoiceItem.product_id == ProductModel.id)  # Changed from Product to ProductModel
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .filter(
            Invoice.client_id == client_profile.id,
            Invoice.creation_date.between(start_date, end_date)
        )
        .group_by(ProductModel.name)  # Changed from Product to ProductModel
        .order_by(func.count(InvoiceItem.id).desc())
        .limit(8)
        .all()
    )

    # Calculate growth percentages
    previous_start = start_date - (end_date - start_date)
    previous_metrics = db.query(
        func.count(distinct(Invoice.id)).label('prev_transactions'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('prev_expenditure')
    ).join(
        InvoiceItem
    ).filter(
        Invoice.client_id == client_profile.id,
        Invoice.creation_date.between(previous_start, start_date)
    ).first()

    # Prepare chart data
    chart_data = {
        'expenditure_trend': {
            'labels': [str(row.date.strftime(date_format)) for row in expenditure_trend],
            'datasets': [{
                'label': 'Expenditure',
                'data': [float(row.amount) for row in expenditure_trend],
                'borderColor': '#3498db',
                'backgroundColor': 'rgba(52, 152, 219, 0.1)'
            }]
        },
        'enterprise_distribution': {
            'labels': [row.company_name for row in enterprise_distribution],
            'datasets': [{
                'data': [float(row.amount) for row in enterprise_distribution],
                'backgroundColor': [
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(243, 156, 18, 0.7)',
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(149, 165, 166, 0.7)',
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(52, 73, 94, 0.7)',
                    'rgba(26, 188, 156, 0.7)'
                ]
            }]
        },
        'transaction_activity': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'datasets': [{
                'label': 'Transactions',
                'data': [next((row.count for row in transaction_activity if row.day_of_week == i), 0) 
                        for i in range(7)],
                'backgroundColor': 'rgba(52, 152, 219, 0.7)'
            }]
        },
        'top_expenses': {
            'labels': [row.product_id for row in top_expenses],
            'datasets': [{
                'data': [float(row.amount) for row in top_expenses],
                'backgroundColor': [
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(243, 156, 18, 0.7)',
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(149, 165, 166, 0.7)'
                ]
            }]
        }
    }

    return {
        "enterprises": enterprises,
        "top_products": [
            {
                "product_name": product.product_name,
                "count": product.count
            }
            for product in top_products
        ],
        "metrics": {
            "total_transactions": metrics.total_transactions or 0,
            "total_expenditure": float(metrics.total_expenditure or 0),
            "avg_transaction": float(metrics.avg_transaction or 0),
            "transaction_growth": calculate_growth(
                previous_metrics.prev_transactions, 
                metrics.total_transactions
            ),
            "expenditure_growth": calculate_growth(
                previous_metrics.prev_expenditure, 
                metrics.total_expenditure
            )
        },
        "chart_data": chart_data
    }

def calculate_growth(previous, current):
    if not previous or not current:
        return 0
    return ((current - previous) / previous) * 100

# Enterprise dashboard
@dashboard_router.get("/enterprise/dashboard", name="enterprise_dashboard")
async def enterprise_dashboard(
    request: Request,
    period: str = "monthly",
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    # # Get date ranges based on period

    today = datetime.now()
    if period == "today":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)  # Changed from subtraction to addition
    elif period == "monthly":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today  # Use today as end date for current month
    else:  # annual
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today  # Use today as end date for current year
    print('start date',start_date)
    print('end date',end_date)  
    # Calculate metrics
    metrics = db.query(
        func.count(Invoice.id).label('total_orders'),
        func.sum(
            InvoiceItem.quantity * InvoiceItem.unit_price
        ).label('total_income')
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        and_(
            Invoice.enterprise_profile_id == enterprise_profile.id,
            Invoice.creation_date.between(start_date, end_date)
        )
    ).first()

    # Get chart data
    chart_data = db.query(
        func.date(Invoice.creation_date).label('date'),
        func.count(Invoice.id).label('orders'),
        func.sum(
            InvoiceItem.quantity * InvoiceItem.unit_price
        ).label('income')
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        and_(
            Invoice.enterprise_profile_id == enterprise_profile.id,
            Invoice.creation_date.between(start_date, end_date)
        )
    ).group_by(
        func.date(Invoice.creation_date)
    ).all()

    # Prepare the response data
    
    response_data = {
        "enterprise": enterprise_profile,
        "metrics": {
            "total_orders": metrics.total_orders or 0,
            "total_income": float(metrics.total_income or 0),
            "period": period
        },
        "chart_data": [
            {
                "date": str(row.date),
                "orders": row.orders,
                "income": float(row.income or 0)
            } for row in chart_data
        ]
    }

    # Check if the request wants JSON
    if request.headers.get("accept") == "application/json":
        return response_data
    
    # Otherwise return HTML template

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "user": user,
            "current_page": "dashboard",
            **response_data
        }
    )   
# all about gmail listener and background tasks

from src.api.dependencies.gmail.background_task_handler import GmailListener
from src.api.dependencies.gmail.gmail_service_helper import GmailAIHelper
from src.database import get_db
from src.configDict import Setting

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

settings = Setting()
# Create a global listener instance
gmail_listener = GmailListener()


@dashboard_router.get("/process-emails")
async def process_emails(request: Request, user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    try:
        # Initialize Gmail AI helper
        gmail_helper = GmailAIHelper(
            oauth_token=user.get('google_access_token'),
            openai_key=settings.OPENAI_API_KEY
        )

        # Get unread messages
        unread_emails = await gmail_helper.get_unread_messages(max_results=5)
        print('unread msg in process_email',unread_emails)
        if not unread_emails:
             return JSONResponse(content={"responses": [], "user": user.dict()})
        responses = []
        for email in unread_emails:
            # Generate AI response
            ai_response = await gmail_helper.generate_ai_response(email)
            
            # Send the response
            if ai_response:
                success = await gmail_helper.send_ai_reply(email, ai_response)
                responses.append({
                    'email': email['subject'],
                    'success': success,
                    'response': ai_response
                })

        return templates.TemplateResponse(
            "pages/Client/email_responses.html",
            {
                "request": request,
                "responses": responses,
                "user": user
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@dashboard_router.post("/start-email-monitoring")
async def start_monitoring(request: Request,background_tasks: BackgroundTasks, user: dict = Depends(require_user_type(UserType.ENTERPRISE)),db: Session = Depends(get_db)):
    await gmail_listener.start_listening(
        user_email=user['email'],
        oauth_token=user['access_token'],
        openai_key=settings.OPENAI_API_KEY,
        db=db
    )
    return {"status": "success", "message": "Email monitoring started"}

@dashboard_router.post("/stop-email-monitoring")
async def stop_monitoring(request: Request, user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    await gmail_listener.stop_listening(user['email'])
    return {"status": "success", "message": "Email monitoring stopped"}

@dashboard_router.get("/monitoring-status")
async def get_monitoring_status(request: Request,user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    is_active = gmail_listener.active_listeners.get(user['email'], False)
    return {
        "status": "active" if is_active else "inactive",
        "last_check": gmail_listener.last_check_time.get(user['email'])
    }