from pydantic import BaseModel, Field
from typing import Optional


class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    record_type: str = Field(default="GENERAL")
    title: str = Field(..., min_length=1, max_length=255)
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordUpdate(BaseModel):
    doctor_id: Optional[int] = None
    record_type: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    record_type: str
    title: str
    diagnosis: Optional[str] = None
    prescriptions: Optional[str] = None
    notes: Optional[str] = None
    created_by: int
    patient_name: str = ""
    doctor_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
