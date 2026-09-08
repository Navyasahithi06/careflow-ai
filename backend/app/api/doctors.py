from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.doctor import Doctor, DoctorStatus
from app.schemas.doctor import DoctorResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorResponse])
def list_active_doctors(
    search: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Doctor).filter(Doctor.status == DoctorStatus.ACTIVE)
    if search:
        query = query.filter(Doctor.full_name.ilike(f"%{search}%"))
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    doctors = query.order_by(Doctor.full_name).all()
    return [_to_response(d) for d in doctors]


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_active_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.status == DoctorStatus.ACTIVE,
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or inactive")
    return _to_response(doctor)


def _to_response(d: Doctor) -> DoctorResponse:
    return DoctorResponse(
        id=d.id,
        full_name=d.full_name,
        specialization=d.specialization,
        qualification=d.qualification,
        experience_years=d.experience_years,
        consultation_fee=float(d.consultation_fee),
        available_days=d.available_days,
        start_time=d.start_time,
        end_time=d.end_time,
        status=d.status.value,
        created_at=str(d.created_at),
    )
