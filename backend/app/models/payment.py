import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    gateway = Column(String(50), default="razorpay", nullable=False)
    gateway_order_id = Column(String(255), nullable=True, unique=True)
    gateway_payment_id = Column(String(255), nullable=True)
    gateway_signature = Column(String(512), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointment = relationship("Appointment", backref="payments")
    patient = relationship("User", backref="payments")
    doctor = relationship("Doctor", backref="payments")

    __table_args__ = (
        Index("ix_payments_appointment", "appointment_id"),
        Index("ix_payments_patient", "patient_id"),
        Index("ix_payments_gateway_order", "gateway_order_id"),
        Index("ix_payments_status", "status"),
    )
