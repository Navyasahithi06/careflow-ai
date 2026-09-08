import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class UrgencyLevel(str, enum.Enum):
    ROUTINE = "ROUTINE"
    PRIORITY = "PRIORITY"
    URGENT = "URGENT"


class SymptomAnalysis(Base):
    __tablename__ = "symptom_analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    input_text = Column(Text, nullable=False)
    detected_symptoms = Column(Text, nullable=True)
    recommended_specialization = Column(String(255), nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    urgency = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE, nullable=False)
    ai_model = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", backref="symptom_analyses")

    __table_args__ = (
        Index("ix_symptom_analyses_patient", "patient_id"),
        Index("ix_symptom_analyses_created", "created_at"),
    )
