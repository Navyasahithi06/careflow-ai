import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ConsultationStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ConsultationNote(Base):
    __tablename__ = "consultation_notes"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.IN_PROGRESS, nullable=False)
    notes = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    prescriptions = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointment = relationship("Appointment", backref="consultation_note")
    patient = relationship("User", foreign_keys=[patient_id], backref="consultation_notes")
    doctor = relationship("Doctor", backref="consultation_notes")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_consultation_notes_patient", "patient_id"),
        Index("ix_consultation_notes_doctor", "doctor_id"),
        Index("ix_consultation_notes_created", "created_at"),
    )
