from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from src.database import Base
import datetime
from .client import Clients
from .enterprise import Enterprise
from .product import ProductModel
from enum import Enum

class PaymentMethodEnum(str, Enum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    BANK_TRANSFER = "Bank Transfer"
    PAYPAL = "PayPal"

class Invoice(Base):
    __tablename__ = 'invoices'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'))
    enterprise_id = Column(Integer, ForeignKey('enterprises.id'))
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime, default=None)
    partial_amount = Column(Float)
    total_amount = Column(Float)
    special_invoice_no = Column(String)
    description = Column(String)
    tax = Column(Float)
    payment_method = Column(SQLAEnum(PaymentMethodEnum))
    enterprise_profile_id = Column(Integer, ForeignKey('enterprise_profiles.id'))
    
    # Relationships
    enterprise_profile = relationship("EnterpriseProfile", back_populates="invoices")
    client = relationship("Clients", back_populates="invoices")
    enterprises = relationship("Enterprise", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def items_total(self):
        return sum(item.quantity * item.unit_price for item in self.invoice_items)

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), index=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    quantity = Column(Integer)
    unit_price = Column(Float)
    
    invoice = relationship("Invoice", back_populates="invoice_items")
    product = relationship("ProductModel", back_populates="invoice_items")
    