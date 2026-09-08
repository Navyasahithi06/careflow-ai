from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.token import Token, TokenStatus
from app.schemas.token import QueueStatusResponse, TokenResponse
from app.services.auth import get_current_user
from app.services.token import get_queue_for_doctor

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("/doctor/{doctor_id}", response_model=QueueStatusResponse)
def get_doctor_queue(
    doctor_id: int,
    queue_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        q_date = date.fromisoformat(queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, doctor_id, q_date)

    tokens_response = []
    for t in queue["tokens"]:
        patient = db.query(User).filter(User.id == t.patient_id).first()
        appt = db.query(Appointment).filter(Appointment.id == t.appointment_id).first()
        tokens_response.append(TokenResponse(
            id=t.id,
            appointment_id=t.appointment_id,
            patient_id=t.patient_id,
            doctor_id=t.doctor_id,
            queue_date=str(t.queue_date),
            token_number=t.token_number,
            status=t.status.value if isinstance(t.status, TokenStatus) else t.status,
            doctor_name=doctor.full_name,
            doctor_specialization=doctor.specialization,
            patient_name=patient.full_name if patient else "Unknown",
            appointment_time=appt.appointment_time if appt else "",
            called_at=str(t.called_at) if t.called_at else None,
            consultation_started_at=str(t.consultation_started_at) if t.consultation_started_at else None,
            completed_at=str(t.completed_at) if t.completed_at else None,
            created_at=str(t.created_at),
        ))

    avg_consultation_minutes = 15
    patients_ahead = len(queue["waiting"])
    estimated_wait = patients_ahead * avg_consultation_minutes

    return QueueStatusResponse(
        doctor_id=doctor_id,
        doctor_name=doctor.full_name,
        queue_date=queue_date,
        current_token=queue["current_token"],
        currently_called=queue["currently_called"],
        total_waiting=len(queue["waiting"]),
        total_completed=len(queue["completed"]),
        total_in_consultation=len(queue["in_consultation"]),
        total_skipped=len(queue["skipped"]),
        total_cancelled=len(queue["cancelled"]),
        queue_status="IN_PROGRESS" if queue["tokens"] else "NOT_STARTED",
        estimated_wait_minutes=estimated_wait,
        tokens=tokens_response,
    )
