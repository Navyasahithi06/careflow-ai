from pydantic import BaseModel
from typing import Optional


class CreateOrderRequest(BaseModel):
    appointment_id: int


class CreateOrderResponse(BaseModel):
    payment_id: int
    appointment_id: int
    gateway_order_id: str
    amount: float
    currency: str
    razorpay_key_id: str


class VerifyPaymentRequest(BaseModel):
    appointment_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    doctor_id: int
    amount: float
    currency: str
    gateway: str
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    status: str
    doctor_name: str
    doctor_specialization: str
    patient_name: str
    appointment_date: str
    appointment_time: str
    created_at: str

    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    receipt_number: str
    patient_name: str
    patient_email: str
    doctor_name: str
    doctor_specialization: str
    appointment_id: int
    appointment_date: str
    appointment_time: str
    consultation_fee: float
    payment_id: int
    payment_date: str
    payment_status: str
    currency: str
