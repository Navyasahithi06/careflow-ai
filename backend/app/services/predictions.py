"""Prediction service.

Forecasts are intentionally generated with a deterministic, dependency-free
statistical baseline rather than a heavyweight ML library:

- Demand (appointment volume) uses a seasonal-naive level forecast built from
  exponentially-smoothed historical daily booking counts combined with a
  per-weekday seasonal factor. It is genuinely computed from real historical
  appointments, is fully reproducible (no randomness), and is explicitly
  labelled as a FORECAST -- not a medical prediction or guarantee.

- Doctor utilization uses actual historical bookings against each doctor's
  daily appointment capacity (shift length / slot length). It is a transparent,
  documented calculation rather than a learnt model.

A real ML library would add no accuracy at the current data volume (the system
retains only a few weeks of appointments), so it is deliberately avoided.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import mean, pstdev

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor, DoctorStatus
from app.schemas.predictions import (
    DemandForecast,
    DoctorUtilizationItem,
    ForecastDayItem,
    HistoryDayItem,
    MethodologyInfo,
    PredictionsResponse,
    UtilizationForecast,
)

MIN_DISTINCT_HISTORY_DAYS = 7
MIN_TOTAL_APPOINTMENTS = 10
DEFAULT_CONSULTATION_SLOT_MINUTES = 15
SES_ALPHA = 0.3
TREND_WINDOW_DAYS = 7
CONFIDENCE_Z = 1.65  # ~90% interval

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DEMAND_MODEL_NAME = "statistical_baseline"
DEMAND_MODEL_DESCRIPTION = (
    "Daily appointment volume is forecast with a seasonal-naive statistical baseline: "
    "an exponentially-smoothed level of historical daily bookings is combined with a "
    "per-weekday seasonal factor and a damped short-term linear trend. Forecasts are "
    "deterministic (no random values) and are NOT medical predictions."
)
UTILIZATION_FORMULA = (
    "utilization% = 100 x (average daily bookings for the doctor) / (daily capacity). "
    "Daily capacity = (shift end - start in minutes) / consultation slot length (15 min). "
    "Average daily bookings = non-cancelled bookings / unique working days with bookings."
)
DISCLAIMER = (
    "These figures are statistical forecasts based on available historical booking data. "
    "They are for planning purposes only, are not medically accurate or guaranteed, and "
    "should not be used for clinical decisions."
)


def _daily_counts(db: Session, start: date, end: date) -> list[tuple[date, int]]:
    rows = (
        db.query(Appointment.appointment_date, func.count(Appointment.id))
        .filter(
            Appointment.appointment_date >= start,
            Appointment.appointment_date <= end,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        .group_by(Appointment.appointment_date)
        .all()
    )
    counts = {d: int(c) for d, c in rows}
    series = []
    cursor = start
    while cursor <= end:
        series.append((cursor, counts.get(cursor, 0)))
        cursor += timedelta(days=1)
    return series


def _ses_level_and_trace(values: list[int], alpha: float) -> tuple[float, list[float]]:
    if not values:
        return 0.0, []
    level = float(values[0])
    trace = [level]
    for v in values[1:]:
        level = alpha * float(v) + (1 - alpha) * level
        trace.append(level)
    return level, trace


def _weekday_factors(series: list[tuple[date, int]]) -> dict[int, float]:
    by_wd: dict[int, list[int]] = {i: [] for i in range(7)}
    for d, c in series:
        by_wd[d.weekday()].append(c)
    total = sum(c for _, c in series)
    n = len(series)
    global_avg = total / n if n else 0.0
    factors = {}
    for wd in range(7):
        if by_wd[wd]:
            wd_avg = sum(by_wd[wd]) / len(by_wd[wd])
            factors[wd] = (wd_avg / global_avg) if global_avg > 0 else 1.0
        else:
            factors[wd] = 1.0
    return {wd: max(0.4, min(2.5, f)) for wd, f in factors.items()}


def _recent_trend(series: list[tuple[date, int]], window: int = TREND_WINDOW_DAYS) -> float:
    recent = series[-window:]
    if len(recent) < 2:
        return 0.0
    xs = [float(i) for i in range(len(recent))]
    ys = [float(c) for _, c in recent]
    mx = mean(xs)
    my = mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return num / denom


def _residual_sigma(values: list[int], trace: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    residuals = [float(v) - t for v, t in zip(values, trace)]
    return pstdev(residuals)


def forecast_demand(db: Session, start: date, end: date, horizon: int) -> DemandForecast:
    series = _daily_counts(db, start, end)
    distinct = len([1 for _, c in series if c > 0])
    total = sum(c for _, c in series)

    if distinct < MIN_DISTINCT_HISTORY_DAYS or total < MIN_TOTAL_APPOINTMENTS:
        return DemandForecast(
            sufficient_historical_data=False,
            data_points=distinct,
            total_appointments=total,
            history_start=str(start),
            history_end=str(end),
            history=[],
            forecast=[],
            notice=(
                f"Insufficient historical data for a meaningful forecast "
                f"({distinct} distinct days / {total} appointments; need at least "
                f"{MIN_DISTINCT_HISTORY_DAYS} distinct days and {MIN_TOTAL_APPOINTMENTS} appointments)."
            ),
        )

    values = [c for _, c in series]
    level, trace = _ses_level_and_trace(values, SES_ALPHA)
    factors = _weekday_factors(series)
    trend = _recent_trend(series)
    sigma = _residual_sigma(values, trace)

    items = []
    cursor = end + timedelta(days=1)
    for _ in range(1, horizon + 1):
        factor = factors[cursor.weekday()]
        point = max(0.0, (level + trend * (cursor - end).days) * factor)
        forecast = round(point)
        band = CONFIDENCE_Z * sigma * factor
        low = max(0, round(point - band))
        high = max(forecast, round(point + band))
        items.append(ForecastDayItem(
            date=str(cursor),
            weekday=WEEKDAY_NAMES[cursor.weekday()],
            forecast=forecast,
            low=low,
            high=high,
        ))
        cursor += timedelta(days=1)

    history = [HistoryDayItem(date=str(d), count=c) for d, c in series if c > 0]
    return DemandForecast(
        sufficient_historical_data=True,
        data_points=distinct,
        total_appointments=total,
        history_start=str(start),
        history_end=str(end),
        history=history,
        forecast=items,
    )


def _daily_capacity(start_time: str, end_time: str, slot_minutes: int) -> int:
    try:
        sh, sm = map(int, start_time.split(":")[:2])
        eh, em = map(int, end_time.split(":")[:2])
    except (ValueError, AttributeError):
        return 0
    mins = (eh * 60 + em) - (sh * 60 + sm)
    if mins <= 0:
        return 0
    return max(1, mins // slot_minutes)


def _is_working_day(available_days: str, weekday: int) -> bool:
    if not available_days:
        return False
    tokens = {t.strip().lower() for t in available_days.split(",") if t.strip()}
    return WEEKDAY_NAMES[weekday].lower() in tokens


def forecast_doctor_utilization(
    db: Session, start: date, end: date, horizon: int
) -> UtilizationForecast:
    doctors = db.query(Doctor).filter(Doctor.status == DoctorStatus.ACTIVE).all()
    items = []

    for doc in doctors:
        rows = db.query(Appointment).filter(
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date >= start,
            Appointment.appointment_date <= end,
            Appointment.status != AppointmentStatus.CANCELLED,
        ).all()

        worked_days_map: dict[date, int] = {}
        for a in rows:
            worked_days_map[a.appointment_date] = worked_days_map.get(a.appointment_date, 0) + 1
        worked_days = len(worked_days_map)
        booked = len(rows)
        capacity = _daily_capacity(doc.start_time, doc.end_time, DEFAULT_CONSULTATION_SLOT_MINUTES)

        if worked_days == 0 or capacity == 0:
            avg_daily = 0.0
            hist_pct = 0.0
            pred_pct = 0.0
            forecast_appts = 0.0
            status = "NO_ACTIVITY"
            notice = "No booked appointments for this doctor in the historical window."
        else:
            avg_daily = round(booked / worked_days, 2)
            hist_pct = round(100 * avg_daily / capacity, 1)
            forecast_days_in_window = 0
            cursor = end + timedelta(days=1)
            for _ in range(1, horizon + 1):
                if _is_working_day(doc.available_days, cursor.weekday()):
                    forecast_days_in_window += 1
                cursor += timedelta(days=1)
            forecast_appts = round(avg_daily * forecast_days_in_window, 1)
            pred_pct = hist_pct if forecast_days_in_window > 0 else 0.0
            status = (
                "OVERBOOKED"
                if pred_pct >= 100
                else "HIGH"
                if pred_pct >= 70
                else "MODERATE"
                if pred_pct >= 40
                else "LOW"
                if pred_pct > 0
                else "NO_ACTIVITY"
            )
            notice = "Predicted utilization assumes the historical booking rate persists."

        items.append(DoctorUtilizationItem(
            doctor_id=doc.id,
            doctor_name=doc.full_name,
            specialization=doc.specialization,
            avg_daily_booked=avg_daily,
            worked_days=worked_days,
            capacity_per_day=capacity,
            historical_utilization_pct=hist_pct,
            predicted_utilization_pct=pred_pct,
            forecast_appointments=forecast_appts,
            status=status,
            notice=notice,
        ))

    items.sort(key=lambda i: i.historical_utilization_pct, reverse=True)
    return UtilizationForecast(
        consultation_slot_minutes=DEFAULT_CONSULTATION_SLOT_MINUTES,
        capacity_formula=UTILIZATION_FORMULA,
        doctors=items,
    )


def build_predictions(db: Session, start: date, end: date, horizon: int) -> PredictionsResponse:
    return PredictionsResponse(
        generated_at=datetime.utcnow().isoformat(timespec="seconds"),
        methodology=MethodologyInfo(
            demand_model=DEMAND_MODEL_NAME,
            demand_description=DEMAND_MODEL_DESCRIPTION,
            utilization_formula=UTILIZATION_FORMULA,
            disclaimer=DISCLAIMER,
        ),
        demand=forecast_demand(db, start, end, horizon),
        doctor_utilization=forecast_doctor_utilization(db, start, end, horizon),
    )