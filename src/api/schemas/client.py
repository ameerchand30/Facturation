from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class GenderEnum(str, Enum):
    M = "M"
    F = "F"
    O = "O"

class ClientBase(BaseModel):
    name: str
    nationality: Optional[str] = None
    idNumber: Optional[str] = None
    gender: Optional[GenderEnum] = None
    Billing_Street: Optional[str] = None
    City: Optional[str] = None
    Postal_Code: Optional[str] = None
    Country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode: True