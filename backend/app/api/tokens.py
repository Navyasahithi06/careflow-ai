from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from app.models.token import Token, TokenStatus
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.schemas.token import TokenResponse, QueueStatusResponse
from app.services.auth import require_role
from app.services.token import get_queue_for_doctor
from datetime import date

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("/my", response_model=list[TokenResponse])
def my_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    tokens = db.query(Token).filter(
        Token.patient_id == current_user.id,
    ).order_by(Token.created_at.desc()).all()
    return [_to_response(t, db) for t in tokens]


@router.get("/appointment/{appointment_id}", response_model=TokenResponse)
def get_token_by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    token = db.query(Token).filter(Token.appointment_id == appointment_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found for this appointment")
    if token.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _to_response(token, db)


@router.get("/{token_id}", response_model=TokenResponse)
def get_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if token.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _to_response(token, db)


def _to_response(t: Token, db: Session) -> TokenResponse:
    doctor = db.query(Doctor).filter(Doctor.id == t.doctor_id).first()
    patient = db.query(User).filter(User.id == t.patient_id).first()
    appointment = db.query(Appointment).filter(Appointment.id == t.appointment_id).first()
    return TokenResponse(
        id=t.id,
        appointment_id=t.appointment_id,
        patient_id=t.patient_id,
        doctor_id=t.doctor_id,
        queue_date=str(t.queue_date),
        token_number=t.token_number,
        status=t.status.value if isinstance(t.status, TokenStatus) else t.status,
        doctor_name=doctor.full_name if doctor else "Unknown",
        doctor_specialization=doctor.specialization if doctor else "Unknown",
        patient_name=patient.full_name if patient else "Unknown",
        appointment_time=appointment.appointment_time if appointment else "",
        called_at=str(t.called_at) if t.called_at else None,
        consultation_started_at=str(t.consultation_started_at) if t.consultation_started_at else None,
        completed_at=str(t.completed_at) if t.completed_at else None,
        created_at=str(t.created_at),
    )
