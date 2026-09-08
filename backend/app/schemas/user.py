from pydantic import BaseModel
from typing import Optional, List


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AdminPatientUpdate(BaseModel):
    is_active: Optional[int] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AdminPatientResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: int
    created_at: str
    appointment_count: int = 0

    class Config:
        from_attributes = True
