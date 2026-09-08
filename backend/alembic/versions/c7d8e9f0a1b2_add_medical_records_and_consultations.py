"""add medical records and consultation notes tables

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # PostgreSQL uses native enums; SQLite falls back to VARCHAR.
    # We create the enum types explicitly (checkfirst), then reference them
    # in the table column definitions with create_type=False to avoid
    # duplicate-type DDL.
    if bind.dialect.name == "postgresql":
        medicalrecordtype = ENUM(
            'DIAGNOSIS', 'PRESCRIPTION', 'LAB_REPORT', 'GENERAL',
            name='medicalrecordtype',
            create_type=True,
        )
        medicalrecordtype.create(bind, checkfirst=True)

        consultationstatus = ENUM(
            'IN_PROGRESS', 'COMPLETED',
            name='consultationstatus',
            create_type=True,
        )
        consultationstatus.create(bind, checkfirst=True)

        medical_records_enum = ENUM(
            'DIAGNOSIS', 'PRESCRIPTION', 'LAB_REPORT', 'GENERAL',
            name='medicalrecordtype',
            create_type=False,
        )
        consultation_notes_enum = ENUM(
            'IN_PROGRESS', 'COMPLETED',
            name='consultationstatus',
            create_type=False,
        )
    else:
        medical_records_enum = sa.String(20)
        consultation_notes_enum = sa.String(20)

    op.create_table(
        'medical_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=True),
        sa.Column('record_type', medical_records_enum, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('prescriptions', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_medical_records_patient', 'medical_records', ['patient_id'])
    op.create_index('ix_medical_records_created', 'medical_records', ['created_at'])

    op.create_table(
        'consultation_notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id'), nullable=False, unique=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('status', consultation_notes_enum, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('prescriptions', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_consultation_notes_patient', 'consultation_notes', ['patient_id'])
    op.create_index('ix_consultation_notes_doctor', 'consultation_notes', ['doctor_id'])
    op.create_index('ix_consultation_notes_created', 'consultation_notes', ['created_at'])


def downgrade() -> None:
    op.drop_table('consultation_notes')
    op.drop_table('medical_records')

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        ENUM(name='consultationstatus').drop(bind, checkfirst=True)
        ENUM(name='medicalrecordtype').drop(bind, checkfirst=True)
