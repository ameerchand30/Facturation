from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from src.api.models.invoice import Invoice, InvoiceItem
from src.api.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceItemCreate
from src.api.models.public.user import EnterpriseProfile

def get_invoice(db: Session, invoice_id: int):
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()

def get_invoices(db: Session,enterprise_profile: EnterpriseProfile, skip: int = 0, limit: int = 100):
    # return db.query(Invoice).offset(skip).limit(limit).all()
    return (db.query(Invoice)
            .options(joinedload(Invoice.client))  # Load the client relationship
            .options(joinedload(Invoice.enterprises))  # Load the enterprise relationship
            .options(joinedload(Invoice.invoice_items))  # Load invoice items
            .filter(Invoice.enterprise_profile_id == enterprise_profile.id)  # Filter by enterprise_profile
            .order_by(Invoice.id.desc())
            .offset(skip)
            .limit(limit)
            .all())

def create_invoice(db: Session, db_invoice: InvoiceCreate, enterprise_profile: EnterpriseProfile):
    # Extract invoice data without items
    invoice_data = db_invoice.model_dump(exclude={'invoice_items'})
    # Create invoice instance
    db_invoic = Invoice(
        client_id=invoice_data['client_id'],
        enterprise_id=invoice_data['enterprise_id'],
        creation_date=invoice_data.get('creation_date'),
        due_date=invoice_data.get('due_date'),
        special_invoice_no=invoice_data.get('special_invoice_no'),
        description=invoice_data.get('description'),
        tax=invoice_data.get('tax', 0),
        payment_method=invoice_data.get('payment_method'),
        enterprise_profile_id=enterprise_profile.id,
    )
    db.add(db_invoic)
    db.flush()
    # Create invoice items
    print(db_invoice.invoice_items)
    for item in db_invoice.invoice_items:
        print(item)
        item_data = item.model_dump()
        db_item = InvoiceItem(
            invoice_id=db_invoic.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price']
        )
        db.add(db_item)
    db.commit()

def update_invoice(db: Session, invoice_id: int, invoice: InvoiceUpdate):
    # Get existing invoice
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        return {"success": False, "message": "Invoice not found"}

    # Update invoice fields
    invoice_data = invoice.model_dump(exclude={'invoice_items'})
    for key, value in invoice_data.items():
        setattr(db_invoice, key, value)

    # Delete existing items
    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
    # Create new items
    for item in invoice.invoice_items:
        item_data = item.model_dump()
        db_item = InvoiceItem(
            invoice_id=invoice_id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price']
        )
        db.add(db_item)
    db.commit()
    
def delete_invoice(db: Session, invoice_id: int):
    db.query(Invoice).filter(Invoice.id == invoice_id).delete()
    db.commit()