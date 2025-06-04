from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy import or_, String, cast
from sqlalchemy.orm import Session, joinedload
from typing import List,Optional
from datetime import date
from src.core.shared import templates

from src.database import get_db
from src.api.models.client import Clients
from src.api.models.enterprise import Enterprise
from src.api.models.product import ProductModel
from src.api.models.invoice import Invoice, InvoiceItem
from src.api.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceItemCreate,Invoice as InvoiceSchema
from src.api.routers.crud import crud_invoice
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType

from datetime import datetime
from zoneinfo import ZoneInfo  # For Python 3.9+

# to add client with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile
from src.api.utils.auth_utils import check_authorization


invoice_router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    responses={404: {"description": "Not found"}},
)
# to show enterprise and customer data while creating inovice
@invoice_router.get("/create", response_class=HTMLResponse, name="create_invoice_form")
async def create_invoice_form(request: Request, db: Session = Depends(get_db)):

    user = {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "type": "ENTERPRISE"
    }
    customers = db.query(Clients).filter(Clients.enterprise_profile_id == 1).all()
    # Get the current date and time in the local timezone
    local_time = datetime.now(ZoneInfo("Europe/Paris"))
    products = db.query(ProductModel).filter(ProductModel.enterprise_profile_id == 1).all()
    enterprise_data = [{"id": enterprise.id, "name": enterprise.name} for enterprise in db.query(Enterprise).filter(Enterprise.enterprise_profile_id == 1).all()]
    customer_data = {customer.name: {"id": customer.id,"email":customer.email } for customer in customers}
    product_data = {product.name: {"id": product.id, "unit_price": product.price,"description":product.description} for product in products}

        # Dummy enterprise_profile data for testing/demo purposes
    enterprise_profile = EnterpriseProfile(
        id=1,
        user_id=1,
        company_name="Acme Corp",
        registration_number="REG123456",
        address="123 Main St",
        state="California",
        postal_code="90001",
        city="Los Angeles",
        logo="https://picsum.photos/200/300",
        notes=None,
        website="https://acme.com",
        phone="123-456-7890",
        email="info@acme.com",
        business_type="Technology",
        tax_id="TAX987654",
    )

    return templates.TemplateResponse("pages/createInvoice.html", {"request": request,
    "enterprise_profile": enterprise_profile, "customer_data": customer_data, "product_data": product_data, "enterprise_data": enterprise_data, "current_page": "create_invoices","user": user, "mode": "create", "rowCounter": 1,"today": local_time}) # Add rowCounter to the context

# to show invoices
@invoice_router.get("/", response_class=HTMLResponse, name="read_invoices")
async def read_invoices(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 10,
    search: str = None,
    sort: str = "id",
    order: str = "desc"
):
    try:

        user = {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "type": "ENTERPRISE"
        }
        # Ensure valid pagination parameters
        page = max(1, page)
        per_page = min(max(10, per_page), 100)
        skip = (page - 1) * per_page

        # Base query with joins
        query = (db.query(Invoice)
                .options(joinedload(Invoice.client))
                .options(joinedload(Invoice.enterprises))
                .options(joinedload(Invoice.invoice_items))
                .filter(Invoice.enterprise_profile_id == 1))

        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.join(Invoice.client).filter(
                or_(
                    Invoice.id.cast(String).ilike(search_term),
                    Invoice.special_invoice_no.ilike(search_term),
                    Invoice.client.has(Client.name.ilike(search_term)),
                    Invoice.payment_method.ilike(search_term)
                )
            )

        # Get total count for pagination
        total_items = query.count()
        total_pages = max(1, (total_items + per_page - 1) // per_page)

        # Apply sorting
        if sort == "invoice_number":
            query = query.order_by(Invoice.special_invoice_no.desc() if order == "desc" else Invoice.special_invoice_no.asc())
        elif sort == "customer_name":
            query = query.join(Invoice.client).order_by(Client.name.desc() if order == "desc" else Client.name.asc())
        elif sort == "amount":
            query = query.order_by(Invoice.items_total.desc() if order == "desc" else Invoice.items_total.asc())
        else:
            query = query.order_by(Invoice.id.desc() if order == "desc" else Invoice.id.asc())

        # Apply pagination
        invoices = query.offset(skip).limit(per_page).all()

        response = templates.TemplateResponse(
            "pages/invoices.html",
            {
                "request": request,
                "invoices": invoices,
                "current_page": "view_invoices",
                "page_number": page,
                "total_pages": total_pages,
                "per_page": per_page,
                "total_items": total_items,
                "search": search,
                "sort": sort,
                "order": order,
                "user": user,
                "enterprise_id": 1
            }
        )
        return response

    except Exception as e:
        print(f"Error fetching invoices: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": f"Error loading invoices: {str(e)}",
                "current_page": "error",
                "user": user
            },
            status_code=500
        )

# to edit the invocies form
@invoice_router.get("/edit/{invoice_id}", response_class=HTMLResponse, name="edit_invoice_form")
async def edit_invoice_form(invoice_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    
    invoice = crud_invoice.get_invoice(db=db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    local_time = datetime.now(ZoneInfo("Europe/Paris"))
    customers = db.query(Clients).filter(Clients.enterprise_profile_id == 1).all()
    products = db.query(ProductModel).filter(ProductModel.enterprise_profile_id == 1).all()
    enterprise_data = [{"id": enterprise.id, "name": enterprise.name} for enterprise in db.query(Enterprise).filter(Enterprise.enterprise_profile_id == 1).all()] # Note method
    customer_data = {customer.name: {"id": customer.id,"email":customer.email } for customer in customers} # Another method 
    product_data = {product.name: {"id": product.id, "unit_price": product.price,"description":product.description} for product in products}
    
    return templates.TemplateResponse(
        "pages/createInvoice.html",
        {
            "request": request,
            "invoice": invoice,
            "customer_data": customer_data,
            "product_data": product_data,
            "enterprise_data": enterprise_data,
            "current_page": "create_invoices",
            "mode": "edit",
            "rowCounter": len(invoice.invoice_items),  # Add rowCounter
            "user": user,
            "enterprise_profile": enterprise_profile,
            "today": local_time  # Add the current date to the context
            
        }
    )
 
# to create new invoice
@invoice_router.post("/", response_model=dict, name="create_invoice")
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    print("Creating invoice with data:", invoice)
   
    auth_check = check_authorization(user)
    if auth_check:
        return auth_check
    try:
        crud_invoice.create_invoice(db=db, db_invoice=invoice, enterprise_profile=enterprise_profile)
        return {"success": True, "message": "Client created successfully"}
    except Exception as e:
        print(e)
        db.rollback()
        return {"success": False, "message": str(e)}
# to update invoice
@invoice_router.post("/update/{invoice_id}", response_model=dict, name="update_invoice")
async def update_invoice(invoice_id: int, invoice_data: InvoiceUpdate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user)
    if auth_check:
        return auth_check
    try:
        crud_invoice.update_invoice(db=db, invoice_id=invoice_id, invoice=invoice_data)
        return {"success": True, "message": "Enterprise created successfully"}
    except Exception as e:
        print(e)
        db.rollback()
        return {"success": False, "message": str(e)}

# to delete invoice
@invoice_router.delete("/delete/{invoice_id}", response_model=dict, name="delete_invoice")
async def delete_invoice(invoice_id: int,db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user)
    if auth_check:
        return auth_check
    try:
        crud_invoice.delete_invoice(db=db ,invoice_id=invoice_id)
        return {"success": True, "message": "Client Delted successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}


# to search clients for jQuery autocomplete
@invoice_router.get("/search_clients")
async def search_clients(
    term: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    try:
        # Search clients with name matching the term
        clients = db.query(Clients).filter(
            Clients.enterprise_profile_id == 1,
            Clients.name.ilike(f"%{term}%")
        ).all()

        # Format response for jQuery autocomplete
        results = [
            {
                "id": client.id,
                "label": client.name,  # This is what shows in the dropdown
                "value": client.name,  # This is what goes into the input
                "email": client.email
            }
            for client in clients
        ]

        return JSONResponse(content=results)

    except Exception as e:
        print(f"Error searching clients: {e}")
        return JSONResponse(
            content={"error": "Error searching clients"},
            status_code=500
        )
