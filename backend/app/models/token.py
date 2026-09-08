import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Date, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class TokenStatus(str, enum.Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class QueueStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    queue_date = Column(Date, nullable=False)
    token_number = Column(Integer, nullable=False)
    status = Column(Enum(TokenStatus), default=TokenStatus.WAITING, nullable=False)
    called_at = Column(DateTime, nullable=True)
    consultation_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointment = relationship("Appointment", backref="token")
    patient = relationship("User", backref="tokens")
    doctor = relationship("Doctor", backref="tokens")

    __table_args__ = (
        UniqueConstraint("doctor_id", "queue_date", "token_number", name="uq_token_doctor_date_number"),
        Index("ix_tokens_doctor_date", "doctor_id", "queue_date"),
        Index("ix_tokens_patient", "patient_id"),
        Index("ix_tokens_status", "status"),
        Index("ix_tokens_queue_date", "queue_date"),
    )
