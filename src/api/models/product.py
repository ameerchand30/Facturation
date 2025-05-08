from src.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum,DateTime,Date,func,Float
from sqlalchemy.orm import relationship

class ProductModel(Base):
    __tablename__ = "product"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    ref_number = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    enterprise_profile_id = Column(Integer, ForeignKey('enterprise_profiles.id'))
    
    # Relationships
    enterprise_profile = relationship("EnterpriseProfile", back_populates="products")
    invoice_items = relationship("InvoiceItem", back_populates="product")