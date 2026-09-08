from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.user import User, Role
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.consultation_note import ConsultationNote, ConsultationStatus
from app.schemas.consultation import (
    ConsultationNoteCreate, ConsultationNoteUpdate, ConsultationNoteResponse, ConsultationListItem,
)
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin/consultations", tags=["admin-consultations"])

VALID_APPOINTMENT_STATUSES = [
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.COMPLETED,
]


def _note_to_response(n, patient, doctor, appt) -> ConsultationNoteResponse:
    return ConsultationNoteResponse(
        id=n.id,
        appointment_id=n.appointment_id,
        patient_id=n.patient_id,
        doctor_id=n.doctor_id,
        status=n.status.value if isinstance(n.status, ConsultationStatus) else str(n.status),
        notes=n.notes,
        diagnosis=n.diagnosis,
        prescriptions=n.prescriptions,
        created_by=n.created_by,
        patient_name=patient.full_name if patient else "Unknown",
        doctor_name=doctor.full_name if doctor else "Unknown",
        doctor_specialization=doctor.specialization if doctor else "Unknown",
        appointment_date=str(appt.appointment_date) if appt else "",
        appointment_time=appt.appointment_time if appt else "",
        created_at=str(n.created_at),
        updated_at=str(n.updated_at) if n.updated_at else None,
    )


@router.get("/appointments", response_model=list[ConsultationListItem])
def list_consultation_appointments(
    search: Optional[str] = Query(None),
    doctor_id: Optional[int] = Query(None),
    date_filter: Optional[str] = Query(None, alias="date"),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(Appointment).filter(
        Appointment.status.in_(VALID_APPOINTMENT_STATUSES),
    )
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if date_filter:
        try:
            d = date.fromisoformat(date_filter)
            query = query.filter(Appointment.appointment_date == d)
        except ValueError:
            pass
    if status_filter:
        try:
            query = query.filter(Appointment.status == AppointmentStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid appointment status")
    if search:
        query = query.join(User, Appointment.patient_id == User.id).filter(
            User.full_name.ilike(f"%{search}%")
        )
    appointments = query.order_by(Appointment.appointment_date.desc()).all()

    results = []
    for a in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
        patient = db.query(User).filter(User.id == a.patient_id).first()
        note = db.query(ConsultationNote).filter(ConsultationNote.appointment_id == a.id).first()
        results.append(ConsultationListItem(
            appointment_id=a.id,
            patient_id=a.patient_id,
            doctor_id=a.doctor_id,
            patient_name=patient.full_name if patient else "Unknown",
            doctor_name=doctor.full_name if doctor else "Unknown",
            doctor_specialization=doctor.specialization if doctor else "Unknown",
            appointment_date=str(a.appointment_date),
            appointment_time=a.appointment_time,
            appointment_status=a.status.value if isinstance(a.status, AppointmentStatus) else str(a.status),
            payment_status=a.payment_status.value if hasattr(a.payment_status, 'value') else str(a.payment_status),
            has_notes=note is not None,
            note_id=note.id if note else None,
            note_status=note.status.value if note and isinstance(note.status, ConsultationStatus) else (str(note.status) if note else None),
        ))
    return results


@router.get("/notes", response_model=list[ConsultationNoteResponse])
def list_consultation_notes(
    doctor_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(ConsultationNote)
    if doctor_id:
        query = query.filter(ConsultationNote.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(ConsultationNote.patient_id == patient_id)
    notes = query.order_by(ConsultationNote.created_at.desc()).all()

    results = []
    for n in notes:
        patient = db.query(User).filter(User.id == n.patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == n.doctor_id).first()
        appt = db.query(Appointment).filter(Appointment.id == n.appointment_id).first()
        results.append(_note_to_response(n, patient, doctor, appt))
    return results


@router.post("/appointments/{appointment_id}/notes", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
def create_consultation_note(
    appointment_id: int,
    payload: ConsultationNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status not in VALID_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Cannot add notes to this appointment")

    existing = db.query(ConsultationNote).filter(ConsultationNote.appointment_id == appointment_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Consultation note already exists for this appointment")

    note = ConsultationNote(
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        status=ConsultationStatus.IN_PROGRESS,
        notes=payload.notes,
        diagnosis=payload.diagnosis,
        prescriptions=payload.prescriptions,
        created_by=current_user.id,
    )
    db.add(note)

    if appointment.status == AppointmentStatus.CONFIRMED:
        appointment.status = AppointmentStatus.COMPLETED

    db.commit()
    db.refresh(note)

    patient = db.query(User).filter(User.id == note.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == note.doctor_id).first()
    appt = db.query(Appointment).filter(Appointment.id == note.appointment_id).first()
    try:
        from app.services.notification import notify_consultation_completed
        notify_consultation_completed(
            patient_id=note.patient_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            appointment_date=str(appt.appointment_date) if appt else "",
            appointment_time=appt.appointment_time if appt else "",
            reference_id=appt.id if appt else None,
        )
    except Exception:
        pass
    return _note_to_response(note, patient, doctor, appt)


@router.put("/notes/{note_id}", response_model=ConsultationNoteResponse)
def update_consultation_note(
    note_id: int,
    payload: ConsultationNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    note = db.query(ConsultationNote).filter(ConsultationNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Consultation note not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        try:
            update_data["status"] = ConsultationStatus(update_data["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    for key, value in update_data.items():
        setattr(note, key, value)
    note.created_by = current_user.id
    db.commit()
    db.refresh(note)

    patient = db.query(User).filter(User.id == note.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == note.doctor_id).first()
    appt = db.query(Appointment).filter(Appointment.id == note.appointment_id).first()
    return _note_to_response(note, patient, doctor, appt)


@router.get("/notes/{note_id}", response_model=ConsultationNoteResponse)
def get_consultation_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    note = db.query(ConsultationNote).filter(ConsultationNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Consultation note not found")
    patient = db.query(User).filter(User.id == note.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == note.doctor_id).first()
    appt = db.query(Appointment).filter(Appointment.id == note.appointment_id).first()
    return _note_to_response(note, patient, doctor, appt)
