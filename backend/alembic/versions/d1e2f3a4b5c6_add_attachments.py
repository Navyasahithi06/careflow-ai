"""add attachments and record_attachments tables

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        attachmententitytype = ENUM(
            'medical_record', 'consultation',
            name='attachmententitytype',
            create_type=True,
        )
        attachmententitytype.create(bind, checkfirst=True)
        entity_type_col = ENUM(
            'medical_record', 'consultation',
            name='attachmententitytype',
            create_type=False,
        )
    else:
        entity_type_col = sa.String(20)

    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('stored_name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('mime_type', sa.String(length=120), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_attachments_uploaded_by', 'attachments', ['uploaded_by'])
    op.create_index('ix_attachments_created', 'attachments', ['created_at'])

    op.create_table(
        'record_attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attachment_id', sa.Integer(), sa.ForeignKey('attachments.id'), nullable=False),
        sa.Column('entity_type', entity_type_col, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('attachment_id', name='uq_record_attachments_attachment'),
    )
    op.create_index('ix_record_attachments_entity', 'record_attachments', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_index('ix_record_attachments_entity', table_name='record_attachments')
    op.drop_table('record_attachments')
    op.drop_index('ix_attachments_created', table_name='attachments')
    op.drop_index('ix_attachments_uploaded_by', table_name='attachments')
    op.drop_table('attachments')

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        ENUM(name='attachmententitytype').drop(bind, checkfirst=True)
