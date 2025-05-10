from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
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
from src.api.routers.crud import crud_report

from weasyprint import HTML,CSS
from pathlib import Path
from bs4 import BeautifulSoup
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
# to add client with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile


report_router = APIRouter(
    prefix="/report",
    tags=["Reposts"],
    responses={404: {"description": "page Not found"}},
)

@report_router.get("/invoiceNumber/{invoice_id}", response_class=HTMLResponse, name="getReportForm")
async def create_report_form(invoice_id: int  ,request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    invoice_data = get_invoice_details(db, invoice_id)
    print("enterprise_profile in get",enterprise_profile)
    return templates.TemplateResponse("pages/generateReport.html", {
        "request": request,
        **invoice_data,
        "user": user,
        "current_page": "generate_report",
        "enterprise_profile": enterprise_profile
    })

# to genraet PDF
@report_router.get("/pdf/{invoice_id}")
async def generate_pdf(
    invoice_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile) # Add this line to get the enterprise profile
):
    try:
        invoice_data = get_invoice_details(db, invoice_id)
        html_content = templates.TemplateResponse(
            "pages/pdf.html",
            {
                "request": request,
                **invoice_data,
                "pdf_mode": True,
                "enterprise_profile": enterprise_profile,  # Pass the enterprise profile to the template
            }
        ).body.decode()
        # Get CSS file path
        css_file = Path("static/css/pdf.css")
        # Generate PDF
        html = HTML(string=html_content, base_url=str(request.base_url))
        css = CSS(filename=css_file)
        pdf = html.write_pdf(stylesheets=[css])
        
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=invoice_{invoice_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_invoice_details(db: Session, invoice_id: int):
    """Get invoice and calculate totals"""
    invoice = crud_report.get_invoice_with_details(db=db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    total_ht = sum(item.unit_price * item.quantity for item in invoice.invoice_items)
    tva = total_ht * 0.20
    total_ttc = total_ht + tva
    
    return {
        "invoice": invoice,
        "total_ht": total_ht,
        "tva": tva,
        "total_ttc": total_ttc
    }

