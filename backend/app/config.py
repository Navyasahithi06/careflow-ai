from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://careflow:careflow_secret@localhost:5432/careflow_ai"
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ADMIN_EMAIL: str = "admin@careflow.ai"
    ADMIN_PASSWORD: str = "admin123"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
