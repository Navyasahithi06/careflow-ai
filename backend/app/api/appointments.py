from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime, date
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor, DoctorStatus
from app.models.appointment import Appointment, AppointmentStatus, PaymentStatus
from app.models.token import Token, TokenStatus
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.auth import require_role, get_current_user

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    doctor = db.query(Doctor).filter(
        Doctor.id == payload.doctor_id,
        Doctor.status == DoctorStatus.ACTIVE,
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or inactive")

    try:
        appt_date = date.fromisoformat(payload.appointment_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if appt_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past.")

    time_str = payload.appointment_time
    if len(time_str) != 5 or time_str[2] != ":":
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM.")

    hour, minute = map(int, time_str.split(":"))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise HTTPException(status_code=400, detail="Invalid time value.")

    start_h, start_m = map(int, doctor.start_time.split(":"))
    end_h, end_m = map(int, doctor.end_time.split(":"))
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    appt_minutes = hour * 60 + minute

    if appt_minutes < start_minutes or appt_minutes >= end_minutes:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor is available between {doctor.start_time} and {doctor.end_time}.",
        )

    day_name = appt_date.strftime("%a")
    available = [d.strip() for d in doctor.available_days.split(",")]
    if day_name not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor is not available on {day_name}. Available: {doctor.available_days}",
        )

    existing = db.query(Appointment).filter(
        Appointment.doctor_id == payload.doctor_id,
        Appointment.appointment_date == appt_date,
        Appointment.appointment_time == time_str,
        Appointment.status.in_([
            AppointmentStatus.PENDING_PAYMENT,
            AppointmentStatus.CONFIRMED,
        ]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This time slot is already booked.")

    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=payload.doctor_id,
        appointment_date=appt_date,
        appointment_time=time_str,
        status=AppointmentStatus.PENDING_PAYMENT,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return _to_response(appointment, doctor, current_user)


@router.get("/my", response_model=list[AppointmentResponse])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.created_at.desc()).all()
    results = []
    for a in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
        results.append(_to_response(a, doctor, current_user))
    return results


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if current_user.role == Role.PATIENT and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    patient = db.query(User).filter(User.id == appointment.patient_id).first()
    return _to_response(appointment, doctor, patient)


@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if appointment.status not in [AppointmentStatus.PENDING_PAYMENT, AppointmentStatus.CONFIRMED]:
        raise HTTPException(status_code=400, detail="Cannot cancel this appointment")
    appointment.status = AppointmentStatus.CANCELLED
    existing_token = db.query(Token).filter(Token.appointment_id == appointment.id).first()
    if existing_token and existing_token.status not in [TokenStatus.COMPLETED, TokenStatus.CANCELLED]:
        existing_token.status = TokenStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    return _to_response(appointment, doctor, current_user)


@router.get("/admin/all", response_model=list[AppointmentResponse])
def admin_list_appointments(
    search: Optional[str] = Query(None),
    doctor_id: Optional[int] = Query(None),
    date_filter: Optional[str] = Query(None, alias="date"),
    status_filter: Optional[str] = Query(None, alias="status"),
    payment_filter: Optional[str] = Query(None, alias="payment_status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(Appointment)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if date_filter:
        try:
            d = date.fromisoformat(date_filter)
            query = query.filter(Appointment.appointment_date == d)
        except ValueError:
            pass
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if payment_filter:
        query = query.filter(Appointment.payment_status == payment_filter)
    if search:
        query = query.join(User, Appointment.patient_id == User.id).filter(
            User.full_name.ilike(f"%{search}%")
        )
    appointments = query.order_by(Appointment.created_at.desc()).all()
    results = []
    for a in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
        patient = db.query(User).filter(User.id == a.patient_id).first()
        results.append(_to_response(a, doctor, patient))
    return results


def _to_response(a: Appointment, doctor: Doctor | None, patient: User | None) -> AppointmentResponse:
    return AppointmentResponse(
        id=a.id,
        patient_id=a.patient_id,
        doctor_id=a.doctor_id,
        appointment_date=str(a.appointment_date),
        appointment_time=a.appointment_time,
        status=a.status.value if isinstance(a.status, AppointmentStatus) else a.status,
        payment_status=a.payment_status.value if isinstance(a.payment_status, PaymentStatus) else a.payment_status,
        consultation_fee=float(doctor.consultation_fee) if doctor else 0.0,
        doctor_name=doctor.full_name if doctor else "Unknown",
        doctor_specialization=doctor.specialization if doctor else "Unknown",
        patient_name=patient.full_name if patient else "Unknown",
        created_at=str(a.created_at),
    )
