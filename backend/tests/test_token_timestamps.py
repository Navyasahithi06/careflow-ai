"""
Tests for Token lifecycle timestamps.

Verifies that called_at, consultation_started_at, and completed_at
are set correctly during token status transitions.

Run: python -m pytest tests/test_token_timestamps.py -v
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User, Role
from app.models.doctor import Doctor, DoctorStatus
from app.models.appointment import Appointment, AppointmentStatus, PaymentStatus
from app.models.token import Token, TokenStatus


engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def recreate_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_test_data():
    recreate_tables()
    db = TestSession()
    uid = uuid.uuid4().hex[:8]

    patient = User(
        email=f"patient_{uid}@test.com",
        full_name="Test Patient",
        hashed_password="fake_hash",
        role=Role.PATIENT,
    )
    db.add(patient)
    db.flush()

    doctor = Doctor(
        full_name=f"Dr. Test {uid}",
        specialization="General Physician",
        qualification="MBBS",
        experience_years=5,
        consultation_fee=500.00,
        available_days="Mon,Tue,Wed,Thu,Fri",
        start_time="09:00",
        end_time="17:00",
        status=DoctorStatus.ACTIVE,
    )
    db.add(doctor)
    db.flush()

    today = date.today()
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=today,
        appointment_time="10:00",
        status=AppointmentStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
    )
    db.add(appointment)
    db.flush()

    token = Token(
        appointment_id=appointment.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        queue_date=today,
        token_number=1,
        status=TokenStatus.WAITING,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return db, token, patient, doctor, appointment


def test_initial_token_has_no_timestamps():
    db, token, *_ = create_test_data()
    try:
        assert token.called_at is None
        assert token.consultation_started_at is None
        assert token.completed_at is None
        assert token.status == TokenStatus.WAITING
    finally:
        db.close()


def test_called_at_set_on_waiting_to_called():
    db, token, *_ = create_test_data()
    try:
        before = datetime.utcnow()
        token.status = TokenStatus.CALLED
        token.called_at = datetime.utcnow()
        db.commit()
        db.refresh(token)

        assert token.called_at is not None
        assert token.consultation_started_at is None
        assert token.completed_at is None
        assert token.called_at >= before
    finally:
        db.close()


def test_consultation_started_at_set_on_called_to_in_consultation():
    db, token, *_ = create_test_data()
    try:
        token.status = TokenStatus.CALLED
        token.called_at = datetime.utcnow()
        db.commit()

        before = datetime.utcnow()
        token.status = TokenStatus.IN_CONSULTATION
        token.consultation_started_at = datetime.utcnow()
        db.commit()
        db.refresh(token)

        assert token.called_at is not None
        assert token.consultation_started_at is not None
        assert token.completed_at is None
        assert token.consultation_started_at >= before
    finally:
        db.close()


def test_completed_at_set_on_in_consultation_to_completed():
    db, token, *_ = create_test_data()
    try:
        token.status = TokenStatus.CALLED
        token.called_at = datetime.utcnow()
        db.commit()

        token.status = TokenStatus.IN_CONSULTATION
        token.consultation_started_at = datetime.utcnow()
        db.commit()

        before = datetime.utcnow()
        token.status = TokenStatus.COMPLETED
        token.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(token)

        assert token.called_at is not None
        assert token.consultation_started_at is not None
        assert token.completed_at is not None
        assert token.completed_at >= before
    finally:
        db.close()


def test_full_lifecycle_timestamps():
    db, token, *_ = create_test_data()
    try:
        assert token.status == TokenStatus.WAITING
        assert token.called_at is None
        assert token.consultation_started_at is None
        assert token.completed_at is None

        token.status = TokenStatus.CALLED
        token.called_at = datetime.utcnow()
        db.commit()
        db.refresh(token)
        assert token.called_at is not None

        token.status = TokenStatus.IN_CONSULTATION
        token.consultation_started_at = datetime.utcnow()
        db.commit()
        db.refresh(token)
        assert token.consultation_started_at is not None

        token.status = TokenStatus.COMPLETED
        token.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(token)
        assert token.completed_at is not None

        assert token.called_at <= token.consultation_started_at <= token.completed_at
    finally:
        db.close()


def test_skipped_token_has_no_lifecycle_timestamps():
    db, token, *_ = create_test_data()
    try:
        token.status = TokenStatus.SKIPPED
        db.commit()
        db.refresh(token)

        assert token.called_at is None
        assert token.consultation_started_at is None
        assert token.completed_at is None
    finally:
        db.close()


def test_cancelled_token_has_no_lifecycle_timestamps():
    db, token, *_ = create_test_data()
    try:
        token.status = TokenStatus.CANCELLED
        db.commit()
        db.refresh(token)

        assert token.called_at is None
        assert token.consultation_started_at is None
        assert token.completed_at is None
    finally:
        db.close()


def test_recall_clears_called_at():
    db, token, *_ = create_test_data()
    try:
        token.status = TokenStatus.CALLED
        token.called_at = datetime.utcnow()
        db.commit()

        token.status = TokenStatus.WAITING
        token.called_at = None
        db.commit()
        db.refresh(token)

        assert token.called_at is None
        assert token.consultation_started_at is None
        assert token.completed_at is None
    finally:
        db.close()


def test_schema_includes_timestamp_fields():
    from app.schemas.token import TokenResponse
    fields = TokenResponse.model_fields
    assert "called_at" in fields
    assert "consultation_started_at" in fields
    assert "completed_at" in fields


def test_model_has_timestamp_columns():
    from app.models.token import Token
    columns = [c.name for c in Token.__table__.columns]
    assert "called_at" in columns
    assert "consultation_started_at" in columns
    assert "completed_at" in columns
