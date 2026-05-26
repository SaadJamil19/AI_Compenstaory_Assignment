from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerProfile(BaseModel):
    customer: CustomerResponse
    tickets: List[dict]
    communication_history: List[dict]
    latest_ticket: Optional[dict] = None
