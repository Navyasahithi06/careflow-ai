from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy.sql import text
from app.database import Base

SYSTEM_SETTINGS_ROW_ID = 1


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    ai_symptom_analysis_enabled = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_new_patient_registered = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_payment_received = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_appointment_confirmed = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_consultation_completed = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    notify_token_called = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )