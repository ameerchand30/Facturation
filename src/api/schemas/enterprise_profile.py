from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

class EnterpriseProfileUpdate(BaseModel):
    company_name: str
    registration_number: str
    address: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    business_type: Optional[str] = None
    tax_id: Optional[str] = None

    class Config:
        from_attributes = True