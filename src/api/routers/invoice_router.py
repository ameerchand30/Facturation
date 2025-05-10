from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
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


invoice_router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    responses={404: {"description": "Not found"}},
)
# to show enterprise and customer data while creating inovice
@invoice_router.get("/create", response_class=HTMLResponse, name="create_invoice_form")
async def create_invoice_form(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    customers = db.query(Clients).filter(Clients.enterprise_profile_id == enterprise_profile.id).all()
    # Get the current date and time in the local timezone
    local_time = datetime.now(ZoneInfo("Europe/Paris"))
    products = db.query(ProductModel).filter(ProductModel.enterprise_profile_id == enterprise_profile.id).all()
    enterprise_data = [{"id": enterprise.id, "name": enterprise.name} for enterprise in db.query(Enterprise).filter(Enterprise.enterprise_profile_id == enterprise_profile.id).all()]
    customer_data = {customer.name: {"id": customer.id,"email":customer.email } for customer in customers}
    product_data = {product.name: {"id": product.id, "unit_price": product.price,"description":product.description} for product in products}

    return templates.TemplateResponse("pages/createInvoice.html", {"request": request,
    "enterprise_profile": enterprise_profile, "customer_data": customer_data, "product_data": product_data, "enterprise_data": enterprise_data, "current_page": "create_invoices","user": user, "mode": "create", "rowCounter": 1,"today": local_time}) # Add rowCounter to the context

# to show invoices
@invoice_router.get("/read", response_class=HTMLResponse, name="read_invoices")
def read_invoices(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    invoices = crud_invoice.get_invoices(db,enterprise_profile)
    return templates.TemplateResponse("pages/invoices.html", {"request": request, "invoices": invoices, "current_page": "read_invoices","user": user})

# to edit the invocies form
@invoice_router.get("/edit/{invoice_id}", response_class=HTMLResponse, name="edit_invoice_form")
async def edit_invoice_form(invoice_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    invoice = crud_invoice.get_invoice(db=db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    local_time = datetime.now(ZoneInfo("Europe/Paris"))
    customers = db.query(Clients).filter(Clients.enterprise_profile_id == enterprise_profile.id).all()
    products = db.query(ProductModel).filter(ProductModel.enterprise_profile_id == enterprise_profile.id).all()
    enterprise_data = [{"id": enterprise.id, "name": enterprise.name} for enterprise in db.query(Enterprise).filter(Enterprise.enterprise_profile_id == enterprise_profile.id).all()] # Note method
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
    try:
        crud_invoice.create_invoice(db=db, db_invoice=invoice, enterprise_profile=enterprise_profile)
        return {"success": True, "message": "Client created successfully"}
    except Exception as e:
        print(e)
        db.rollback()
        return {"success": False, "message": str(e)}
# to update invoice
@invoice_router.post("/update/{invoice_id}", response_model=dict, name="update_invoice")
async def update_invoice(invoice_id: int, invoice_data: InvoiceUpdate, db: Session = Depends(get_db)):
    try:
        crud_invoice.update_invoice(db=db, invoice_id=invoice_id, invoice=invoice_data)
        return {"success": True, "message": "Enterprise created successfully"}
    except Exception as e:
        print(e)
        db.rollback()
        return {"success": False, "message": str(e)}

# to delete invoice
@invoice_router.delete("/delete/{invoice_id}", response_model=dict, name="delete_invoice")
async def delete_invoice(invoice_id: int,db: Session = Depends(get_db)):
    try:
        crud_invoice.delete_invoice(db=db ,invoice_id=invoice_id)
        return {"success": True, "message": "Client Delted successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}
