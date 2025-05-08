from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
from src.api.schemas.enterprise import Enterprise
from src.api.schemas.client import Client
from src.api.schemas.product import Product

class PaymentMethodEnum(str, Enum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    BANK_TRANSFER = "Bank Transfer"
    PAYPAL = "PayPal"

class InvoiceItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemUpdate(InvoiceItemBase):
    pass

class InvoiceItemInDBBase(InvoiceItemBase):
    id: int

    class Config:
        from_attributes = True

class InvoiceItem(InvoiceItemInDBBase):
    pass

class InvoiceItemInDB(InvoiceItemInDBBase):
    pass

class InvoiceBase(BaseModel):
    client_id: int
    enterprise_id: int
    creation_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    partial_amount: Optional[float] = None
    total_amount: Optional[float] = None
    special_invoice_no: Optional[str] = None
    description: Optional[str] = None
    tax: Optional[float] = None
    payment_method: PaymentMethodEnum

class InvoiceCreate(InvoiceBase):
    invoice_items: List[InvoiceItemCreate]

class InvoiceUpdate(InvoiceBase):
    invoice_items: List[InvoiceItemUpdate]

class InvoiceInDBBase(InvoiceBase):
    id: int
    invoice_items: List[InvoiceItem]

    class Config:
        from_attributes = True

class Invoice(InvoiceInDBBase):
    pass

class InvoiceInDB(InvoiceInDBBase):
    pass