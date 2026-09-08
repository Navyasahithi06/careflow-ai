"""add notifications table

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        notificationtype = ENUM(
            'appointment_confirmed', 'payment_success', 'token_called',
            'consultation_completed', 'new_patient_registered',
            name='notificationtype',
            create_type=True,
        )
        notificationtype.create(bind, checkfirst=True)
        type_col = ENUM(
            'appointment_confirmed', 'payment_success', 'token_called',
            'consultation_completed', 'new_patient_registered',
            name='notificationtype',
            create_type=False,
        )
    else:
        type_col = sa.String(50)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', type_col, nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_notifications_recipient', 'notifications', ['recipient_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_notifications_recipient', table_name='notifications')
    op.drop_table('notifications')

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        ENUM(name='notificationtype').drop(bind, checkfirst=True)