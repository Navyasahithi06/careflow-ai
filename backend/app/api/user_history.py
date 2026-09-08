from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord, MedicalRecordType
from app.models.consultation_note import ConsultationNote
from app.schemas.medical_record import MedicalRecordResponse
from app.schemas.consultation import ConsultationNoteResponse
from app.schemas.user import ProfileUpdate
from app.services.auth import require_role

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/medical-records", response_model=list[MedicalRecordResponse])
def my_medical_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == current_user.id,
    ).order_by(MedicalRecord.created_at.desc()).all()

    results = []
    for r in records:
        doctor = db.query(Doctor).filter(Doctor.id == r.doctor_id).first() if r.doctor_id else None
        patient = current_user
        results.append(MedicalRecordResponse(
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
        ))
    return results


@router.get("/consultation-notes", response_model=list[ConsultationNoteResponse])
def my_consultation_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    notes = db.query(ConsultationNote).filter(
        ConsultationNote.patient_id == current_user.id,
    ).order_by(ConsultationNote.created_at.desc()).all()

    results = []
    for n in notes:
        doctor = db.query(Doctor).filter(Doctor.id == n.doctor_id).first()
        appt = db.query(Appointment).filter(Appointment.id == n.appointment_id).first()
        results.append(ConsultationNoteResponse(
            id=n.id,
            appointment_id=n.appointment_id,
            patient_id=n.patient_id,
            doctor_id=n.doctor_id,
            status=n.status.value if hasattr(n.status, 'value') else str(n.status),
            notes=n.notes,
            diagnosis=n.diagnosis,
            prescriptions=n.prescriptions,
            created_by=n.created_by,
            patient_name=current_user.full_name,
            doctor_name=doctor.full_name if doctor else "Unknown",
            doctor_specialization=doctor.specialization if doctor else "Unknown",
            appointment_date=str(appt.appointment_date) if appt else "",
            appointment_time=appt.appointment_time if appt else "",
            created_at=str(n.created_at),
            updated_at=str(n.updated_at) if n.updated_at else None,
        ))
    return results


@router.get("/history")
def my_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    medical_records = _my_records(db, current_user)
    consultation_notes = _my_notes(db, current_user)

    timeline = []
    for r in medical_records:
        timeline.append({
            "type": "medical_record",
            "id": r["id"],
            "title": r["title"],
            "record_type": r["record_type"],
            "doctor_name": r["doctor_name"],
            "diagnosis": r["diagnosis"],
            "prescriptions": r["prescriptions"],
            "notes": r["notes"],
            "created_at": r["created_at"],
        })
    for c in consultation_notes:
        timeline.append({
            "type": "consultation",
            "id": c["id"],
            "title": "Consultation",
            "record_type": "CONSULTATION",
            "doctor_name": c["doctor_name"],
            "diagnosis": c["diagnosis"],
            "prescriptions": c["prescriptions"],
            "notes": c["notes"],
            "created_at": c["created_at"],
        })

    timeline.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "medical_records": medical_records,
        "consultation_notes": consultation_notes,
        "timeline": timeline,
    }


def _my_records(db: Session, current_user: User) -> list:
    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == current_user.id,
    ).order_by(MedicalRecord.created_at.desc()).all()

    results = []
    for r in records:
        doctor = db.query(Doctor).filter(Doctor.id == r.doctor_id).first() if r.doctor_id else None
        results.append({
            "id": r.id,
            "title": r.title,
            "record_type": r.record_type.value if isinstance(r.record_type, MedicalRecordType) else str(r.record_type),
            "doctor_name": doctor.full_name if doctor else None,
            "diagnosis": r.diagnosis,
            "prescriptions": r.prescriptions,
            "notes": r.notes,
            "created_at": str(r.created_at),
        })
    return results


def _my_notes(db: Session, current_user: User) -> list:
    notes = db.query(ConsultationNote).filter(
        ConsultationNote.patient_id == current_user.id,
    ).order_by(ConsultationNote.created_at.desc()).all()
    results = []
    for n in notes:
        doctor = db.query(Doctor).filter(Doctor.id == n.doctor_id).first()
        results.append({
            "id": n.id,
            "title": "Consultation",
            "record_type": "CONSULTATION",
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "diagnosis": n.diagnosis,
            "prescriptions": n.prescriptions,
            "notes": n.notes,
            "created_at": str(n.created_at),
        })
    return results
