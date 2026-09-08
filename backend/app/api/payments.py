import json
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor, DoctorStatus
from app.models.appointment import Appointment, AppointmentStatus, PaymentStatus as ApptPaymentStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    CreateOrderRequest, CreateOrderResponse, VerifyPaymentRequest,
    PaymentResponse, ReceiptResponse,
)
from app.services.auth import require_role, get_current_user
from app.services.payment import create_razorpay_order, verify_razorpay_signature, verify_webhook_signature
from app.services.token import generate_token_for_appointment
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_payment_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if appointment.status != AppointmentStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="Appointment is not awaiting payment")
    if appointment.payment_status != ApptPaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Payment is not pending for this appointment")

    existing = db.query(Payment).filter(
        Payment.appointment_id == appointment.id,
        Payment.status == PaymentStatus.PENDING,
    ).first()
    if existing:
        return CreateOrderResponse(
            payment_id=existing.id,
            appointment_id=existing.appointment_id,
            gateway_order_id=existing.gateway_order_id or "",
            amount=float(existing.amount),
            currency=existing.currency,
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
        )

    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    amount = doctor.consultation_fee
    receipt = f"cf_appt_{appointment.id}_{int(datetime.utcnow().timestamp())}"

    try:
        order = await create_razorpay_order(amount, "INR", receipt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment gateway error: {str(e)}")

    payment = Payment(
        appointment_id=appointment.id,
        patient_id=current_user.id,
        doctor_id=appointment.doctor_id,
        amount=amount,
        currency="INR",
        gateway="razorpay",
        gateway_order_id=order["id"],
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return CreateOrderResponse(
        payment_id=payment.id,
        appointment_id=appointment.id,
        gateway_order_id=order["id"],
        amount=float(amount),
        currency="INR",
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not verify_razorpay_signature(payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    payment = db.query(Payment).filter(
        Payment.appointment_id == payload.appointment_id,
        Payment.gateway_order_id == payload.razorpay_order_id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if payment.status == PaymentStatus.PAID:
        doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
        patient = db.query(User).filter(User.id == payment.patient_id).first()
        return _payment_to_response(payment, doctor, patient, appointment)

    if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
        payment.status = PaymentStatus.FAILED
        db.commit()
        raise HTTPException(status_code=400, detail="Cannot confirm payment for this appointment")

    payment.gateway_payment_id = payload.razorpay_payment_id
    payment.gateway_signature = payload.razorpay_signature
    payment.status = PaymentStatus.PAID

    appointment.payment_status = ApptPaymentStatus.PAID
    appointment.status = AppointmentStatus.CONFIRMED

    generate_token_for_appointment(
        db=db,
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        queue_date=appointment.appointment_date,
    )

    db.commit()
    db.refresh(payment)

    doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
    patient = db.query(User).filter(User.id == payment.patient_id).first()
    _notify_payment_success(db, payment, appointment, doctor, patient)
    return _payment_to_response(payment, doctor, patient, appointment)


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if settings.RAZORPAY_WEBHOOK_SECRET and not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event", "")

    if event_type == "payment.captured":
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        razorpay_payment_id = payment_entity.get("id")

        if razorpay_order_id:
            payment = db.query(Payment).filter(Payment.gateway_order_id == razorpay_order_id).first()
            if payment and payment.status != PaymentStatus.PAID:
                payment.gateway_payment_id = razorpay_payment_id
                payment.status = PaymentStatus.PAID

                appointment = db.query(Appointment).filter(Appointment.id == payment.appointment_id).first()
                if appointment and appointment.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
                    appointment.payment_status = ApptPaymentStatus.PAID
                    appointment.status = AppointmentStatus.CONFIRMED

                    generate_token_for_appointment(
                        db=db,
                        appointment_id=appointment.id,
                        patient_id=appointment.patient_id,
                        doctor_id=appointment.doctor_id,
                        queue_date=appointment.appointment_date,
                    )
                db.commit()
                doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
                patient = db.query(User).filter(User.id == payment.patient_id).first()
                _notify_payment_success(db, payment, appointment, doctor, patient)

    elif event_type == "payment.failed":
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        if razorpay_order_id:
            payment = db.query(Payment).filter(Payment.gateway_order_id == razorpay_order_id).first()
            if payment and payment.status not in [PaymentStatus.PAID, PaymentStatus.REFUNDED]:
                payment.status = PaymentStatus.FAILED
                db.commit()

    elif event_type == "refund.created":
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        if razorpay_order_id:
            payment = db.query(Payment).filter(Payment.gateway_order_id == razorpay_order_id).first()
            if payment:
                payment.status = PaymentStatus.REFUNDED
                appointment = db.query(Appointment).filter(Appointment.id == payment.appointment_id).first()
                if appointment:
                    appointment.payment_status = ApptPaymentStatus.REFUNDED
                db.commit()

    return {"status": "ok"}


@router.get("/my", response_model=list[PaymentResponse])
def my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    payments = db.query(Payment).filter(Payment.patient_id == current_user.id).order_by(Payment.created_at.desc()).all()
    results = []
    for p in payments:
        doctor = db.query(Doctor).filter(Doctor.id == p.doctor_id).first()
        patient = db.query(User).filter(User.id == p.patient_id).first()
        appointment = db.query(Appointment).filter(Appointment.id == p.appointment_id).first()
        results.append(_payment_to_response(p, doctor, patient, appointment))
    return results


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if current_user.role == Role.PATIENT and payment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
    patient = db.query(User).filter(User.id == payment.patient_id).first()
    appointment = db.query(Appointment).filter(Appointment.id == payment.appointment_id).first()
    return _payment_to_response(payment, doctor, patient, appointment)


@router.get("/{payment_id}/receipt", response_model=ReceiptResponse)
def get_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if current_user.role == Role.PATIENT and payment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    doctor = db.query(Doctor).filter(Doctor.id == payment.doctor_id).first()
    patient = db.query(User).filter(User.id == payment.patient_id).first()
    appointment = db.query(Appointment).filter(Appointment.id == payment.appointment_id).first()

    return ReceiptResponse(
        receipt_number=f"CF-REC-{payment.id:06d}",
        patient_name=patient.full_name if patient else "Unknown",
        patient_email=patient.email if patient else "",
        doctor_name=doctor.full_name if doctor else "Unknown",
        doctor_specialization=doctor.specialization if doctor else "Unknown",
        appointment_id=appointment.id if appointment else 0,
        appointment_date=str(appointment.appointment_date) if appointment else "",
        appointment_time=appointment.appointment_time if appointment else "",
        consultation_fee=float(doctor.consultation_fee) if doctor else 0.0,
        payment_id=payment.id,
        payment_date=str(payment.created_at),
        payment_status=payment.status.value if isinstance(payment.status, PaymentStatus) else payment.status,
        currency=payment.currency,
    )


def _payment_to_response(p, doctor, patient, appointment) -> PaymentResponse:
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


def _notify_payment_success(db: Session, payment, appointment, doctor, patient):
    """Best-effort notification triggers for a successful payment. Never raises."""
    try:
        from app.services.notification import (
            _admin_ids, notify_appointment_confirmed, notify_payment_success,
            notify_admin_payment_received,
        )
        ap_date = str(appointment.appointment_date) if appointment else ""
        ap_time = appointment.appointment_time if appointment else ""
        doc_name = doctor.full_name if doctor else "Unknown"
        pat_name = patient.full_name if patient else "Unknown"
        amount = float(payment.amount)
        currency = payment.currency or "INR"
        appt_id = appointment.id if appointment else None

        notify_payment_success(
            patient_id=payment.patient_id,
            amount=amount,
            currency=currency,
            doctor_name=doc_name,
            appointment_date=ap_date,
            appointment_time=ap_time,
            reference_id=payment.appointment_id,
        )
        notify_appointment_confirmed(
            patient_id=payment.patient_id,
            doctor_name=doc_name,
            appointment_date=ap_date,
            appointment_time=ap_time,
            reference_id=appt_id,
        )
        notify_admin_payment_received(
            admin_ids=_admin_ids(db),
            amount=amount,
            currency=currency,
            patient_name=pat_name,
            doctor_name=doc_name,
            reference_id=appt_id,
        )
    except Exception:
        pass
