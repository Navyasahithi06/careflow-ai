from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor, DoctorStatus
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/doctors", tags=["admin-doctors"])


@router.get("", response_model=list[DoctorResponse])
def list_doctors(
    search: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(Doctor)
    if search:
        query = query.filter(Doctor.full_name.ilike(f"%{search}%"))
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if status_filter:
        query = query.filter(Doctor.status == status_filter)
    doctors = query.order_by(Doctor.created_at.desc()).all()
    return [_doctor_to_response(d) for d in doctors]


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    doctor = Doctor(
        full_name=payload.full_name,
        specialization=payload.specialization,
        qualification=payload.qualification,
        experience_years=payload.experience_years,
        consultation_fee=payload.consultation_fee,
        available_days=payload.available_days,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=DoctorStatus(payload.status),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return _doctor_to_response(doctor)


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return _doctor_to_response(doctor)


@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = DoctorStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return _doctor_to_response(doctor)


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    from app.models.appointment import Appointment, AppointmentStatus
    has_active = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_([
            AppointmentStatus.PENDING_PAYMENT,
            AppointmentStatus.CONFIRMED,
        ]),
    ).first()

    if has_active:
        doctor.status = DoctorStatus.INACTIVE
        db.commit()
        return {"message": "Doctor deactivated (has active appointments)", "deactivated": True}

    db.delete(doctor)
    db.commit()
    return {"message": "Doctor deleted", "deactivated": False}


def _doctor_to_response(d: Doctor) -> DoctorResponse:
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
        status=d.status.value if isinstance(d.status, DoctorStatus) else d.status,
        created_at=str(d.created_at),
    )
