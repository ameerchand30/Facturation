from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from src.api.models.invoice import Invoice, InvoiceItem
from src.api.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceItemCreate



def get_invoice_with_details(db: Session, invoice_id: int):
    return (db.query(Invoice)
            .options(joinedload(Invoice.client))  # Load client
            .options(joinedload(Invoice.enterprises))  # Load enterprise
            .options(
                joinedload(Invoice.invoice_items)
                .joinedload(InvoiceItem.product)  # Load product details through invoice items
            )
            .order_by(Invoice.id.desc())
            .filter(Invoice.id == invoice_id)
            .first()) 
