from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentResponse
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/payments", tags=["admin-payments"])


@router.get("", response_model=list[PaymentResponse])
def admin_list_payments(
    search: Optional[str] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_filter: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(Payment)
    if doctor_id:
        query = query.filter(Payment.doctor_id == doctor_id)
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    if date_filter:
        from datetime import date
        try:
            d = date.fromisoformat(date_filter)
            query = query.filter(Payment.created_at >= d)
        except ValueError:
            pass
    if search:
        query = query.join(User, Payment.patient_id == User.id).filter(
            User.full_name.ilike(f"%{search}%")
        )
    payments = query.order_by(Payment.created_at.desc()).all()
    results = []
    for p in payments:
        doctor = db.query(Doctor).filter(Doctor.id == p.doctor_id).first()
        patient = db.query(User).filter(User.id == p.patient_id).first()
        appointment = db.query(Appointment).filter(Appointment.id == p.appointment_id).first()
        results.append(_to_response(p, doctor, patient, appointment))
    return results


@router.get("/{payment_id}", response_model=PaymentResponse)
def admin_get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
    patient = db.query(User).filter(User.id == payment.patient_id).first()
    appointment = db.query(Appointment).filter(Appointment.id == payment.appointment_id).first()
    return _to_response(payment, doctor, patient, appointment)


def _to_response(p, doctor, patient, appointment) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        appointment_id=p.appointment_id,
        patient_id=p.patient_id,
        doctor_id=p.doctor_id,
        amount=float(p.amount),
        currency=p.currency,
        gateway=p.gateway,
        gateway_order_id=p.gateway_order_id,
        gateway_payment_id=p.gateway_payment_id,
        status=p.status.value if isinstance(p.status, PaymentStatus) else p.status,
        doctor_name=doctor.full_name if doctor else "Unknown",
        doctor_specialization=doctor.specialization if doctor else "Unknown",
        patient_name=patient.full_name if patient else "Unknown",
        appointment_date=str(appointment.appointment_date) if appointment else "",
        appointment_time=appointment.appointment_time if appointment else "",
        created_at=str(p.created_at),
    )
