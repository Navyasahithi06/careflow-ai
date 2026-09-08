from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import SessionLocal
from app.models.settings import SYSTEM_SETTINGS_ROW_ID, SystemSettings

PREFERENCE_TO_COLUMN = {
    "new_patient_registered": "notify_new_patient_registered",
    "payment_received": "notify_payment_received",
    "appointment_confirmed": "notify_appointment_confirmed",
    "consultation_completed": "notify_consultation_completed",
    "token_called": "notify_token_called",
}


def get_settings_row(db: Session) -> SystemSettings:
    """Fetch the single row of system settings, creating it with defaults if missing."""
    row = db.get(SystemSettings, SYSTEM_SETTINGS_ROW_ID)
    if row is None:
        row = SystemSettings(id=SYSTEM_SETTINGS_ROW_ID)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def is_ai_symptom_analysis_enabled(db: Session) -> bool:
    row = db.get(SystemSettings, SYSTEM_SETTINGS_ROW_ID)
    if row is None:
        return True
    return bool(row.ai_symptom_analysis_enabled)


def notification_enabled(preference_key: str) -> bool:
    """Best-effort preference check used by the notification service.

    Runs in its own short-lived session so a settings problem can never break
    a notification trigger. Unknown/missing preferences default to enabled.
    """
    if preference_key not in PREFERENCE_TO_COLUMN:
        return True
    try:
        db = SessionLocal()
        try:
            row = db.get(SystemSettings, SYSTEM_SETTINGS_ROW_ID)
            if row is None:
                return True
            return bool(getattr(row, PREFERENCE_TO_COLUMN[preference_key]))
        finally:
            db.close()
    except Exception:
        return True


def database_available() -> bool:
    try:
        from app.database import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False