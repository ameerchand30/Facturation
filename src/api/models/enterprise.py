from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
#from .client import Clients  # Import the Clients model

class Enterprise(Base):
    __tablename__ = "enterprises"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    state = Column(String)
    postalCode = Column(String)
    city = Column(String)
    siretNo = Column(String)
    notes = Column(String)
    # Add foreign keys to link to the Clients and EnterpriseProfile tables
    client_id = Column(Integer, ForeignKey('clients.id'))
    enterprise_profile_id = Column(Integer, ForeignKey('enterprise_profiles.id'))

    client = relationship("Clients", back_populates="enterprises")
    invoices = relationship("Invoice", back_populates="enterprises")
    enterprise_profile = relationship("EnterpriseProfile", back_populates="enterprises")