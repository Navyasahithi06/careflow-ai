from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, Role
from app.schemas.settings import (
    AISettingsResponse,
    NotificationPreferencesResponse,
    SettingsResponse,
    SettingsUpdate,
    SystemInfoResponse,
)
from app.services.ai import ai_service
from app.services.auth import require_role
from app.services.settings import database_available, get_settings_row

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])

settings = get_settings()

APPLICATION_NAME = "CareFlow AI"
APPLICATION_VERSION = "1.0.0"


def _notification_preferences_response(row) -> NotificationPreferencesResponse:
    return NotificationPreferencesResponse(
        new_patient_registered=bool(row.notify_new_patient_registered),
        payment_received=bool(row.notify_payment_received),
        appointment_confirmed=bool(row.notify_appointment_confirmed),
        consultation_completed=bool(row.notify_consultation_completed),
        token_called=bool(row.notify_token_called),
    )


def _ai_settings_response(row, ollama_available: bool) -> AISettingsResponse:
    return AISettingsResponse(
        symptom_analysis_enabled=bool(row.ai_symptom_analysis_enabled),
        model=settings.OLLAMA_MODEL,
        ollama_available=ollama_available,
    )


def _system_info_response() -> SystemInfoResponse:
    return SystemInfoResponse(
        application=APPLICATION_NAME,
        environment=settings.ENVIRONMENT,
        api_version=APPLICATION_VERSION,
        database="ok" if database_available() else "unreachable",
        utc_time=datetime.now(timezone.utc).isoformat(),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    row = get_settings_row(db)
    ollama_available = await ai_service.health_check()
    return SettingsResponse(
        notification_preferences=_notification_preferences_response(row),
        ai=_ai_settings_response(row, ollama_available),
        system=_system_info_response(),
    )


@router.put("", response_model=SettingsResponse)
async def update_settings_view(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    row = get_settings_row(db)
    pref = payload.notification_preferences
    row.notify_new_patient_registered = pref.new_patient_registered
    row.notify_payment_received = pref.payment_received
    row.notify_appointment_confirmed = pref.appointment_confirmed
    row.notify_consultation_completed = pref.consultation_completed
    row.notify_token_called = pref.token_called
    row.ai_symptom_analysis_enabled = payload.ai.symptom_analysis_enabled
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    ollama_available = await ai_service.health_check()
    return SettingsResponse(
        notification_preferences=_notification_preferences_response(row),
        ai=_ai_settings_response(row, ollama_available),
        system=_system_info_response(),
    )