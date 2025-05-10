from fastapi import APIRouter, Depends, HTTPException, Query,Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from sqlalchemy.orm import Session

from src.database import get_db
from src.api.models.public.user import EnterpriseProfile
from src.api.models.invoice import Invoice
from src.api.dependencies.auth import get_current_user

from src.core.shared import templates

client_invoices_router = APIRouter(prefix="/client_", tags=["client"])

@client_invoices_router.get("/invoices", name="get_client_invoices", response_class=HTMLResponse)
async def get_client_invoices(request: Request,db: Session = Depends(get_db),  current_user = Depends(get_current_user)):
    print("Current user:",  current_user["sub"])
    """Get all invoices for the logged-in client"""
    invoices = db.query(Invoice).filter(Invoice.client_id ==  current_user["sub"]).all()
    enterprises = (
        db.query(EnterpriseProfile)
        .join(Invoice, Invoice.enterprise_id == EnterpriseProfile.id)
        .filter(Invoice.client_id == current_user["sub"])
        .distinct()
        .all()
    )
    print("Enterprises:", enterprises)
    
    # return invoices, enterprises

    if not invoices:
        return templates.TemplateResponse("pages/User/client_view_inovices.html", {"request": Request, "invoices": [], "enterprises": [] })
    return templates.TemplateResponse(
        "pages/User/client_view_inovices.html",
        {
            "request": request,
            "invoices": invoices,
            "enterprises": enterprises
        }
    )

@client_invoices_router.get("/invoices/search")
async def search_client_invoices(
    invoice_number: Optional[str] = Query(None),
    enterprise_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search invoices by invoice number or enterprise"""
    query = db.query(Invoice).filter(Invoice.client_id ==  current_user["sub"])

    if invoice_number:
        query = query.filter(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    
    if enterprise_id:
        query = query.filter(Invoice.enterprise_id == enterprise_id)

    invoices = query.all()
    return {"invoices": invoices}
