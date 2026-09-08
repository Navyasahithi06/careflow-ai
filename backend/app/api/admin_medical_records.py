from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord, MedicalRecordType
from app.schemas.medical_record import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse,
)
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/medical-records", tags=["admin-medical-records"])


def _to_response(r, patient, doctor) -> MedicalRecordResponse:
    return MedicalRecordResponse(
        id=r.id,
        patient_id=r.patient_id,
        doctor_id=r.doctor_id,
        record_type=r.record_type.value if isinstance(r.record_type, MedicalRecordType) else str(r.record_type),
        title=r.title,
        diagnosis=r.diagnosis,
        prescriptions=r.prescriptions,
        notes=r.notes,
        created_by=r.created_by,
        patient_name=patient.full_name if patient else "Unknown",
        doctor_name=doctor.full_name if doctor else None,
        created_at=str(r.created_at),
        updated_at=str(r.updated_at) if r.updated_at else None,
    )


@router.get("", response_model=list[MedicalRecordResponse])
def list_medical_records(
    search: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    record_type: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(MedicalRecord)
    if patient_id:
        query = query.filter(MedicalRecord.patient_id == patient_id)
    if doctor_id:
        query = query.filter(MedicalRecord.doctor_id == doctor_id)
    if record_type:
        try:
            query = query.filter(MedicalRecord.record_type == MedicalRecordType(record_type))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid record type")
    if search:
        query = query.join(User, MedicalRecord.patient_id == User.id).filter(
            User.full_name.ilike(f"%{search}%")
        )
    records = query.order_by(MedicalRecord.created_at.desc()).all()

    results = []
    for r in records:
        patient = db.query(User).filter(User.id == r.patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == r.doctor_id).first() if r.doctor_id else None
        results.append(_to_response(r, patient, doctor))
    return results


@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    payload: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    patient = db.query(User).filter(
        User.id == payload.patient_id,
        User.role == Role.PATIENT,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if payload.doctor_id is not None:
        doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        record_type = MedicalRecordType(payload.record_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record type")

    record = MedicalRecord(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        record_type=record_type,
        title=payload.title,
        diagnosis=payload.diagnosis,
        prescriptions=payload.prescriptions,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    patient = db.query(User).filter(User.id == record.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == record.doctor_id).first() if record.doctor_id else None
    return _to_response(record, patient, doctor)


@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    patient = db.query(User).filter(User.id == record.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == record.doctor_id).first() if record.doctor_id else None
    return _to_response(record, patient, doctor)


@router.put("/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    record_id: int,
    payload: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "record_type" in update_data and update_data["record_type"] is not None:
        try:
            update_data["record_type"] = MedicalRecordType(update_data["record_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid record type")
    if "doctor_id" in update_data and update_data["doctor_id"] is not None:
        doctor = db.query(Doctor).filter(Doctor.id == update_data["doctor_id"]).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

    for key, value in update_data.items():
        setattr(record, key, value)
    record.created_by = current_user.id
    db.commit()
    db.refresh(record)

    patient = db.query(User).filter(User.id == record.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == record.doctor_id).first() if record.doctor_id else None
    return _to_response(record, patient, doctor)


@router.delete("/{record_id}")
def delete_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    db.delete(record)
    db.commit()
    return {"message": "Medical record deleted"}
