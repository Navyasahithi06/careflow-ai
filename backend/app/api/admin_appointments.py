from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, PaymentStatus
from app.schemas.appointment import AppointmentResponse
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/appointments", tags=["admin-appointments"])


@router.get("", response_model=list[AppointmentResponse])
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
        from datetime import date
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


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def admin_get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    patient = db.query(User).filter(User.id == appointment.patient_id).first()
    return _to_response(appointment, doctor, patient)


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
