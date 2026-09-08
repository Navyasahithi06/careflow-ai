from pydantic import BaseModel, ConfigDict, StrictBool


PREFERENCE_KEYS = (
    "new_patient_registered",
    "payment_received",
    "appointment_confirmed",
    "consultation_completed",
    "token_called",
)


class NotificationPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_patient_registered: StrictBool
    payment_received: StrictBool
    appointment_confirmed: StrictBool
    consultation_completed: StrictBool
    token_called: StrictBool


class AISettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptom_analysis_enabled: StrictBool


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notification_preferences: NotificationPreferencesUpdate
    ai: AISettingsUpdate


class NotificationPreferencesResponse(BaseModel):
    new_patient_registered: bool
    payment_received: bool
    appointment_confirmed: bool
    consultation_completed: bool
    token_called: bool


class AISettingsResponse(BaseModel):
    symptom_analysis_enabled: bool
    model: str
    ollama_available: bool


class SystemInfoResponse(BaseModel):
    application: str
    environment: str
    api_version: str
    database: str
    utc_time: str


class SettingsResponse(BaseModel):
    notification_preferences: NotificationPreferencesResponse
    ai: AISettingsResponse
    system: SystemInfoResponse