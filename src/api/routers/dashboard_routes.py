from sqlalchemy.orm import Session
from sqlalchemy import func,cast, Date, and_
from typing import Optional, List, Dict, Any
from datetime import datetime,timedelta
from fastapi import APIRouter, Depends, Request, HTTPException

from src.core.shared import templates
from src.database import get_db

from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
from src.api.models.invoice import Invoice, InvoiceItem

from src.api.dependencies.auth import get_current_user, require_user_type

# to show dashboard with each enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile



dashboard_router = APIRouter()

# Client dashboard
@dashboard_router.get("/client/dashboard")
async def client_dashboard(request: Request, user: dict = Depends(require_user_type(UserType.CLIENT))):
    return templates.TemplateResponse(
        "pages/Client/dashboard.html",
        {
            "request": request,
            "current_page": "dashboard",
            "user": user
        }
    )

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