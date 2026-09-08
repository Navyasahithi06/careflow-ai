from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.database import get_db
from app.models.user import User, Role
from app.models.token import Token, TokenStatus
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.schemas.token import TokenResponse, QueueStatusResponse, AdminQueueActionRequest
from app.services.auth import require_role
from app.services.token import get_queue_for_doctor

router = APIRouter(prefix="/api/admin/tokens", tags=["admin-tokens"])


def _to_response(t, doctor, patient, appt) -> TokenResponse:
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
        appointment_time=appt.appointment_time if appt else "",
        called_at=str(t.called_at) if t.called_at else None,
        consultation_started_at=str(t.consultation_started_at) if t.consultation_started_at else None,
        completed_at=str(t.completed_at) if t.completed_at else None,
        created_at=str(t.created_at),
    )


@router.get("/queue", response_model=QueueStatusResponse)
def get_queue(
    doctor_id: int,
    queue_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
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
        tokens_response.append(_to_response(t, doctor, patient, appt))

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


@router.post("/call-next", response_model=TokenResponse)
def call_next_token(
    payload: AdminQueueActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(payload.queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, payload.doctor_id, q_date)

    if queue["called"] or queue["in_consultation"]:
        raise HTTPException(status_code=400, detail="A token is already called or in consultation. Complete it first.")

    if not queue["waiting"]:
        raise HTTPException(status_code=400, detail="No waiting tokens in queue.")

    token = queue["waiting"][0]
    token.status = TokenStatus.CALLED
    token.called_at = datetime.utcnow()
    db.commit()
    db.refresh(token)

    doctor = db.query(Doctor).filter(Doctor.id == token.doctor_id).first()
    patient = db.query(User).filter(User.id == token.patient_id).first()
    appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
    try:
        from app.services.notification import notify_token_called
        notify_token_called(
            patient_id=token.patient_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            token_number=token.token_number,
            reference_id=token.id,
        )
    except Exception:
        pass
    return _to_response(token, doctor, patient, appt)


@router.post("/start-consultation", response_model=TokenResponse)
def start_consultation(
    payload: AdminQueueActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(payload.queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, payload.doctor_id, q_date)

    if not queue["called"]:
        raise HTTPException(status_code=400, detail="No called token to start consultation.")

    token = queue["called"][0]
    token.status = TokenStatus.IN_CONSULTATION
    token.consultation_started_at = datetime.utcnow()
    db.commit()
    db.refresh(token)

    doctor = db.query(Doctor).filter(Doctor.id == token.doctor_id).first()
    patient = db.query(User).filter(User.id == token.patient_id).first()
    appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
    return _to_response(token, doctor, patient, appt)


@router.post("/complete", response_model=TokenResponse)
def complete_consultation(
    payload: AdminQueueActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(payload.queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, payload.doctor_id, q_date)

    if not queue["in_consultation"]:
        raise HTTPException(status_code=400, detail="No token in consultation to complete.")

    token = queue["in_consultation"][0]
    token.status = TokenStatus.COMPLETED
    token.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(token)

    doctor = db.query(Doctor).filter(Doctor.id == token.doctor_id).first()
    patient = db.query(User).filter(User.id == token.patient_id).first()
    appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
    try:
        from app.services.notification import notify_consultation_completed
        notify_consultation_completed(
            patient_id=token.patient_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            appointment_date=str(appt.appointment_date) if appt else "",
            appointment_time=appt.appointment_time if appt else "",
            reference_id=appt.id if appt else None,
        )
    except Exception:
        pass
    return _to_response(token, doctor, patient, appt)


@router.post("/skip", response_model=TokenResponse)
def skip_token(
    payload: AdminQueueActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(payload.queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, payload.doctor_id, q_date)

    target = None
    if queue["called"]:
        target = queue["called"][0]
    elif queue["waiting"]:
        target = queue["waiting"][0]
    else:
        raise HTTPException(status_code=400, detail="No token to skip.")

    target.status = TokenStatus.SKIPPED
    db.commit()
    db.refresh(target)

    doctor = db.query(Doctor).filter(Doctor.id == target.doctor_id).first()
    patient = db.query(User).filter(User.id == target.patient_id).first()
    appt = db.query(Appointment).filter(Appointment.id == target.appointment_id).first()
    return _to_response(target, doctor, patient, appt)


@router.post("/recall", response_model=TokenResponse)
def recall_token(
    payload: AdminQueueActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(payload.queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    queue = get_queue_for_doctor(db, payload.doctor_id, q_date)

    if not queue["called"]:
        raise HTTPException(status_code=400, detail="No called token to recall.")

    token = queue["called"][0]
    token.status = TokenStatus.WAITING
    token.called_at = None
    db.commit()
    db.refresh(token)

    doctor = db.query(Doctor).filter(Doctor.id == token.doctor_id).first()
    patient = db.query(User).filter(User.id == token.patient_id).first()
    appt = db.query(Appointment).filter(Appointment.id == token.appointment_id).first()
    return _to_response(token, doctor, patient, appt)


@router.get("/all", response_model=list[TokenResponse])
def admin_all_tokens(
    doctor_id: int,
    queue_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    try:
        q_date = date.fromisoformat(queue_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    tokens = db.query(Token).filter(
        Token.doctor_id == doctor_id,
        Token.queue_date == q_date,
    ).order_by(Token.token_number).all()

    results = []
    for t in tokens:
        doctor = db.query(Doctor).filter(Doctor.id == t.doctor_id).first()
        patient = db.query(User).filter(User.id == t.patient_id).first()
        appt = db.query(Appointment).filter(Appointment.id == t.appointment_id).first()
        results.append(_to_response(t, doctor, patient, appt))
    return results
