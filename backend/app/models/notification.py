import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, enum.Enum):
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    PAYMENT_SUCCESS = "payment_success"
    TOKEN_CALLED = "token_called"
    CONSULTATION_COMPLETED = "consultation_completed"
    NEW_PATIENT_REGISTERED = "new_patient_registered"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    reference_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        Index("ix_notifications_recipient", "recipient_id", "created_at"),
    )