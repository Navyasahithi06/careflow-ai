from pydantic import BaseModel
from typing import List, Optional


class ReportOverview(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    total_confirmed_appointments: int
    total_completed_consultations: int
    total_revenue: float
    collection_today: float
    appointments_today: int


class AppointmentTrendItem(BaseModel):
    date: str
    total: int
    confirmed: int
    completed: int


class RevenueTrendItem(BaseModel):
    date: str
    revenue: float


class DoctorStat(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    appointment_count: int
    completed_count: int


class ReportAppointmentsResponse(BaseModel):
    trends: List[AppointmentTrendItem]
    by_doctor: List[DoctorStat]


class ReportRevenueResponse(BaseModel):
    trends: List[RevenueTrendItem]
