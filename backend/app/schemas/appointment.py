from pydantic import BaseModel, Field
from typing import Optional


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Time in HH:MM format")


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: str
    appointment_time: str
    status: str
    payment_status: str
    consultation_fee: float
    doctor_name: str
    doctor_specialization: str
    patient_name: str
    created_at: str

    class Config:
        from_attributes = True
