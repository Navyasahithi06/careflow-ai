from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.api import auth, health, admin, user, doctors, admin_doctors, appointments, admin_appointments, payments, admin_payments, tokens, admin_tokens, queue, ai
from app.api import admin_patients, admin_medical_records, admin_consultations, admin_reports, user_history
from app.api import attachments, notifications
from app.api import admin_settings
from app.seeds.admin import seed_admin
from app.seeds.doctors import seed_doctors
from app.services.notification import hub

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_doctors(db)
    finally:
        db.close()
    yield
    try:
        hub.set_loop(None)
    except Exception:
        pass


app = FastAPI(
    title="CareFlow AI",
    description="AI-powered Hospital Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(user_history.router)
app.include_router(doctors.router)
app.include_router(admin_doctors.router)
app.include_router(appointments.router)
app.include_router(admin_appointments.router)
app.include_router(payments.router)
app.include_router(admin_payments.router)
app.include_router(tokens.router)
app.include_router(admin_tokens.router)
app.include_router(queue.router)
app.include_router(ai.router)
app.include_router(admin_patients.router)
app.include_router(admin_medical_records.router)
app.include_router(admin_consultations.router)
app.include_router(admin_reports.router)
app.include_router(attachments.router)
app.include_router(notifications.router)
app.include_router(admin_settings.router)


@app.get("/")
def root():
    return {"message": "CareFlow AI API", "version": "1.0.0"}
