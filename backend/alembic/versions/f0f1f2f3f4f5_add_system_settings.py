"""add system_settings table

Revision ID: f0f1f2f3f4f5
Revises: e5f6a7b8c9d0
Create Date: 2026-09-07 00:00:00.000000
"""
from typing import Sequence, Union
from datetime import datetime
from alembic import op
import sqlalchemy as sa

revision: str = "f0f1f2f3f4f5"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ai_symptom_analysis_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_new_patient_registered", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_payment_received", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_appointment_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_consultation_completed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_token_called", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        sa.table(
            "system_settings",
            sa.column("id", sa.Integer()),
            sa.column("ai_symptom_analysis_enabled", sa.Boolean()),
            sa.column("notify_new_patient_registered", sa.Boolean()),
            sa.column("notify_payment_received", sa.Boolean()),
            sa.column("notify_appointment_confirmed", sa.Boolean()),
            sa.column("notify_consultation_completed", sa.Boolean()),
            sa.column("notify_token_called", sa.Boolean()),
            sa.column("updated_at", sa.DateTime()),
        ),
        [
            {
                "id": 1,
                "ai_symptom_analysis_enabled": True,
                "notify_new_patient_registered": True,
                "notify_payment_received": True,
                "notify_appointment_confirmed": True,
                "notify_consultation_completed": True,
                "notify_token_called": True,
                "updated_at": datetime.utcnow(),
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("system_settings")