from pydantic import BaseModel
from typing import Optional, List


class TokenResponse(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    doctor_id: int
    queue_date: str
    token_number: int
    status: str
    doctor_name: str
    doctor_specialization: str
    patient_name: str
    appointment_time: str
    called_at: Optional[str] = None
    consultation_started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class QueueStatusResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    queue_date: str
    current_token: Optional[int] = None
    currently_called: Optional[int] = None
    total_waiting: int
    total_completed: int
    total_in_consultation: int
    total_skipped: int
    total_cancelled: int
    queue_status: str
    estimated_wait_minutes: int
    tokens: List[TokenResponse]


class AdminQueueActionRequest(BaseModel):
    doctor_id: int
    queue_date: str
