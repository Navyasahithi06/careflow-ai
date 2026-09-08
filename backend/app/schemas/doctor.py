from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class DoctorCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    specialization: str = Field(..., min_length=1, max_length=255)
    qualification: Optional[str] = None
    experience_years: int = Field(default=0, ge=0)
    consultation_fee: Decimal = Field(..., gt=0)
    available_days: str = Field(default="Mon,Tue,Wed,Thu,Fri")
    start_time: str = Field(default="09:00")
    end_time: str = Field(default="17:00")
    status: str = Field(default="active")


class DoctorUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    specialization: Optional[str] = Field(None, min_length=1, max_length=255)
    qualification: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    consultation_fee: Optional[Decimal] = Field(None, gt=0)
    available_days: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None


class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialization: str
    qualification: Optional[str] = None
    experience_years: int
    consultation_fee: float
    available_days: str
    start_time: str
    end_time: str
    status: str
    created_at: str

    class Config:
        from_attributes = True
