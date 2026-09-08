import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class MedicalRecordType(str, enum.Enum):
    DIAGNOSIS = "DIAGNOSIS"
    PRESCRIPTION = "PRESCRIPTION"
    LAB_REPORT = "LAB_REPORT"
    GENERAL = "GENERAL"


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    record_type = Column(Enum(MedicalRecordType), default=MedicalRecordType.GENERAL, nullable=False)
    title = Column(String(255), nullable=False)
    diagnosis = Column(Text, nullable=True)
    prescriptions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("User", foreign_keys=[patient_id], backref="medical_records")
    doctor = relationship("Doctor", backref="medical_records")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_medical_records_patient", "patient_id"),
        Index("ix_medical_records_created", "created_at"),
    )
