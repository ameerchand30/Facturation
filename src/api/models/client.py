from src.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum,DateTime,Date,func
from sqlalchemy.orm import relationship


class Clients(Base):
    __tablename__ = "clients"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    enterprise_profile_id = Column(Integer, ForeignKey('enterprise_profiles.id'))
    nationality = Column(String, nullable=True)
    idNumber = Column(String, nullable=True)
    gender = Column(Enum("M", "F", "O",name="gender_enum"), nullable=True)
    Billing_Street = Column(String)
    City = Column(String)
    State_Province = Column(String)
    Postal_Code = Column(String)
    Country = Column(String)
    email = Column(String)
    phone = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, default=func.now())


    enterprise = relationship("EnterpriseProfile", back_populates="clients")
    enterprises = relationship("Enterprise", back_populates="client")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
