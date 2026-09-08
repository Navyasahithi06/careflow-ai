from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.reports import (
    ReportOverview,
    AppointmentTrendItem,
    RevenueTrendItem,
    DoctorStat,
    ReportAppointmentsResponse,
    ReportRevenueResponse,
)
from app.schemas.predictions import PredictionsResponse
from app.services.auth import require_role
from app.services.predictions import build_predictions

router = APIRouter(prefix="/api/admin/reports", tags=["admin-reports"])


def _parse_date(value: str, default: date) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


@router.get("/overview", response_model=ReportOverview)
def get_overview(
    start_date: Optional[str] = Query(None, alias="start"),
    end_date: Optional[str] = Query(None, alias="end"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    today = date.today()
    start = _parse_date(start_date, today - timedelta(days=30)) if start_date else today - timedelta(days=30)
    end = _parse_date(end_date, today) if end_date else today

    total_patients = db.query(func.count(User.id)).filter(User.role == Role.PATIENT).scalar() or 0
    total_doctors = db.query(func.count(Doctor.id)).scalar() or 0

    total_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date >= start,
        Appointment.appointment_date <= end,
    ).scalar() or 0

    total_confirmed = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date >= start,
        Appointment.appointment_date <= end,
        Appointment.status == AppointmentStatus.CONFIRMED,
    ).scalar() or 0

    total_completed = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date >= start,
        Appointment.appointment_date <= end,
        Appointment.status == AppointmentStatus.COMPLETED,
    ).scalar() or 0

    revenue_rows = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.PAID,
        func.date(Payment.created_at) >= start,
        func.date(Payment.created_at) <= end,
    ).scalar()
    total_revenue = float(revenue_rows or 0)

    today_revenue_rows = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.PAID,
        func.date(Payment.created_at) == today,
    ).scalar()
    collection_today = float(today_revenue_rows or 0)

    appointments_today = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date == today,
    ).scalar() or 0

    return ReportOverview(
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_confirmed_appointments=total_confirmed,
        total_completed_consultations=total_completed,
        total_revenue=total_revenue,
        collection_today=collection_today,
        appointments_today=appointments_today,
    )


@router.get("/appointments", response_model=ReportAppointmentsResponse)
def get_appointment_report(
    start_date: Optional[str] = Query(None, alias="start"),
    end_date: Optional[str] = Query(None, alias="end"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    today = date.today()
    start = _parse_date(start_date, today - timedelta(days=30)) if start_date else today - timedelta(days=30)
    end = _parse_date(end_date, today) if end_date else today

    appointments = db.query(Appointment).filter(
        Appointment.appointment_date >= start,
        Appointment.appointment_date <= end,
    ).all()

    trend_map: dict[date, dict] = {}
    doctor_map: dict[int, dict] = {}

    for a in appointments:
        d = a.appointment_date
        if d not in trend_map:
            trend_map[d] = {"total": 0, "confirmed": 0, "completed": 0}
        trend_map[d]["total"] += 1
        status = a.status.value if isinstance(a.status, AppointmentStatus) else str(a.status)
        if status == "CONFIRMED":
            trend_map[d]["confirmed"] += 1
        elif status == "COMPLETED":
            trend_map[d]["completed"] += 1

        if a.doctor_id not in doctor_map:
            doctor_map[a.doctor_id] = {"appointments": 0, "completed": 0}
        doctor_map[a.doctor_id]["appointments"] += 1
        if status == "COMPLETED":
            doctor_map[a.doctor_id]["completed"] += 1

    trends = []
    cursor = start
    while cursor <= end:
        entry = trend_map.get(cursor, {"total": 0, "confirmed": 0, "completed": 0})
        trends.append(AppointmentTrendItem(
            date=str(cursor),
            total=entry["total"],
            confirmed=entry["confirmed"],
            completed=entry["completed"],
        ))
        cursor += timedelta(days=1)

    by_doctor = []
    for doctor_id, stats in doctor_map.items():
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        by_doctor.append(DoctorStat(
            doctor_id=doctor_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            specialization=doctor.specialization if doctor else "Unknown",
            appointment_count=stats["appointments"],
            completed_count=stats["completed"],
        ))
    by_doctor.sort(key=lambda s: s.appointment_count, reverse=True)

    return ReportAppointmentsResponse(trends=trends, by_doctor=by_doctor)


@router.get("/revenue", response_model=ReportRevenueResponse)
def get_revenue_report(
    start_date: Optional[str] = Query(None, alias="start"),
    end_date: Optional[str] = Query(None, alias="end"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    today = date.today()
    start = _parse_date(start_date, today - timedelta(days=30)) if start_date else today - timedelta(days=30)
    end = _parse_date(end_date, today) if end_date else today

    payments = db.query(Payment).filter(
        Payment.status == PaymentStatus.PAID,
        func.date(Payment.created_at) >= start,
        func.date(Payment.created_at) <= end,
    ).all()

    revenue_map: dict[date, float] = {}
    for p in payments:
        day = p.created_at.date() if hasattr(p.created_at, "date") else date.today()
        revenue_map[day] = revenue_map.get(day, 0.0) + float(p.amount)

    trends = []
    cursor = start
    while cursor <= end:
        trends.append(RevenueTrendItem(
            date=str(cursor),
            revenue=round(revenue_map.get(cursor, 0.0), 2),
        ))
        cursor += timedelta(days=1)

    return ReportRevenueResponse(trends=trends)


@router.get("/predictions", response_model=PredictionsResponse)
def get_predictions(
    start_date: Optional[str] = Query(None, alias="start"),
    end_date: Optional[str] = Query(None, alias="end"),
    horizon_days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    today = date.today()
    start = _parse_date(start_date, today - timedelta(days=30)) if start_date else today - timedelta(days=30)
    end = _parse_date(end_date, today) if end_date else today
    if start > end:
        raise HTTPException(status_code=400, detail="start must be on or before end")
    return build_predictions(db, start, end, horizon_days)
