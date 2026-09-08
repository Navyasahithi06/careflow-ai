import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.database import Base


class AppointmentStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(5), nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING_PAYMENT, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("User", backref="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
