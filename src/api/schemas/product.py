from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ProductBase(BaseModel):
    name: str
    ref_number: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode: True