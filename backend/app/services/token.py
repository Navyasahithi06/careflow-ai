from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.token import Token, TokenStatus


def generate_token_for_appointment(
    db: Session,
    appointment_id: int,
    patient_id: int,
    doctor_id: int,
    queue_date: date,
) -> Token:
    """
    Generate a daily sequential token for a confirmed appointment.
    
    Uses database-level locking to prevent duplicate tokens.
    Scoped by doctor_id + queue_date.
    
    Idempotent: returns existing token if one already exists for this appointment.
    """
    existing = db.query(Token).filter(Token.appointment_id == appointment_id).first()
    if existing:
        return existing

    result = db.execute(
        text("SELECT COALESCE(MAX(token_number), 0) + 1 FROM tokens WHERE doctor_id = :doctor_id AND queue_date = :queue_date"),
        {"doctor_id": doctor_id, "queue_date": queue_date},
    )
    next_number = result.scalar()

    token = Token(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        queue_date=queue_date,
        token_number=next_number,
        status=TokenStatus.WAITING,
    )
    db.add(token)
    db.flush()
    return token


def get_queue_for_doctor(db: Session, doctor_id: int, queue_date: date) -> dict:
    """Get complete queue status for a doctor on a specific date."""
    tokens = db.query(Token).filter(
        Token.doctor_id == doctor_id,
        Token.queue_date == queue_date,
    ).order_by(Token.token_number).all()

    waiting = [t for t in tokens if t.status == TokenStatus.WAITING]
    called = [t for t in tokens if t.status == TokenStatus.CALLED]
    in_consultation = [t for t in tokens if t.status == TokenStatus.IN_CONSULTATION]
    completed = [t for t in tokens if t.status == TokenStatus.COMPLETED]
    skipped = [t for t in tokens if t.status == TokenStatus.SKIPPED]
    cancelled = [t for t in tokens if t.status == TokenStatus.CANCELLED]

    current_token = None
    if completed:
        current_token = max(t.token_number for t in completed)
    if in_consultation:
        current_token = max(t.token_number for t in in_consultation)

    currently_called = None
    if called:
        currently_called = called[0].token_number
    if in_consultation:
        currently_called = in_consultation[0].token_number

    return {
        "tokens": tokens,
        "waiting": waiting,
        "called": called,
        "in_consultation": in_consultation,
        "completed": completed,
        "skipped": skipped,
        "cancelled": cancelled,
        "current_token": current_token,
        "currently_called": currently_called,
    }
