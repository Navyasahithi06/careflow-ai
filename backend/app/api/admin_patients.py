from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import func
from app.database import get_db
from app.models.user import User, Role
from app.models.appointment import Appointment
from app.schemas.user import AdminPatientResponse, AdminPatientUpdate
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/patients", tags=["admin-patients"])


def _to_response(p, count) -> AdminPatientResponse:
    return AdminPatientResponse(
        id=p.id,
        email=p.email,
        full_name=p.full_name,
        phone=p.phone,
        is_active=p.is_active,
        created_at=str(p.created_at),
        appointment_count=count,
    )


@router.get("", response_model=list[AdminPatientResponse])
def list_patients(
    search: Optional[str] = Query(None),
    active_only: Optional[bool] = Query(None, alias="active"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(User).filter(User.role == Role.PATIENT)
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    if active_only is not None:
        query = query.filter(User.is_active == (1 if active_only else 0))

    patients = query.order_by(User.created_at.desc()).all()

    results = []
    for p in patients:
        count = db.query(func.count(Appointment.id)).filter(Appointment.patient_id == p.id).scalar() or 0
        results.append(_to_response(p, count))
    return results


@router.get("/{patient_id}", response_model=AdminPatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    patient = db.query(User).filter(
        User.id == patient_id,
        User.role == Role.PATIENT,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    count = db.query(func.count(Appointment.id)).filter(Appointment.patient_id == patient.id).scalar() or 0
    return _to_response(patient, count)


@router.put("/{patient_id}/status", response_model=AdminPatientResponse)
def update_patient_status(
    patient_id: int,
    payload: AdminPatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    patient = db.query(User).filter(
        User.id == patient_id,
        User.role == Role.PATIENT,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)

    count = db.query(func.count(Appointment.id)).filter(Appointment.patient_id == patient.id).scalar() or 0
    return _to_response(patient, count)
