from pydantic import BaseModel, Field
from typing import Optional


class ConsultationNoteCreate(BaseModel):
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None


class ConsultationNoteUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None


class ConsultationNoteResponse(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    doctor_id: int
    status: str
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None
    created_by: int
    patient_name: str = ""
    doctor_name: str = ""
    doctor_specialization: str = ""
    appointment_date: str = ""
    appointment_time: str = ""
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ConsultationListItem(BaseModel):
    appointment_id: int
    patient_id: int
    doctor_id: int
    patient_name: str = ""
    doctor_name: str = ""
    doctor_specialization: str = ""
    appointment_date: str = ""
    appointment_time: str = ""
    appointment_status: str = ""
    payment_status: str = ""
    has_notes: bool = False
    note_id: Optional[int] = None
    note_status: Optional[str] = None
