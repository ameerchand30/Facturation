from pydantic import BaseModel
from src.api.schemas.client import Client  # Import the Client schema

class EnterpriseBase(BaseModel):
    name: str
    address: str
    state: str
    postalCode: str
    city: str
    siretNo: str
    notes: str
    client_id: int

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseUpdate(EnterpriseBase):
    pass

class EnterpriseInDBBase(EnterpriseBase):
    id: int

    class Config:
        from_attributes = True  # Updated to use from_attributes

class Enterprise(EnterpriseInDBBase):
    client: Client

class EnterpriseInDB(EnterpriseInDBBase):
    pass