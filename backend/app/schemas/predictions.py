from pydantic import BaseModel
from typing import List, Optional


class ForecastDayItem(BaseModel):
    date: str
    weekday: str
    forecast: int
    low: int
    high: int


class HistoryDayItem(BaseModel):
    date: str
    count: int


class DemandForecast(BaseModel):
    sufficient_historical_data: bool
    data_points: int
    total_appointments: int
    history_start: str
    history_end: str
    history: List[HistoryDayItem]
    forecast: List[ForecastDayItem]
    notice: Optional[str] = None


class DoctorUtilizationItem(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    avg_daily_booked: float
    worked_days: int
    capacity_per_day: int
    historical_utilization_pct: float
    predicted_utilization_pct: float
    forecast_appointments: float
    status: str
    notice: Optional[str] = None


class UtilizationForecast(BaseModel):
    consultation_slot_minutes: int
    capacity_formula: str
    doctors: List[DoctorUtilizationItem]
    notice: Optional[str] = None


class MethodologyInfo(BaseModel):
    demand_model: str
    demand_description: str
    utilization_formula: str
    disclaimer: str


class PredictionsResponse(BaseModel):
    generated_at: str
    methodology: MethodologyInfo
    demand: DemandForecast
    doctor_utilization: UtilizationForecast