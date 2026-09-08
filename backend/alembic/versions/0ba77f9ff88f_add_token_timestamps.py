"""add_token_timestamps

Revision ID: 0ba77f9ff88f
Revises: 
Create Date: 2026-08-24 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ba77f9ff88f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tokens', sa.Column('called_at', sa.DateTime(), nullable=True))
    op.add_column('tokens', sa.Column('consultation_started_at', sa.DateTime(), nullable=True))
    op.add_column('tokens', sa.Column('completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tokens', 'completed_at')
    op.drop_column('tokens', 'consultation_started_at')
    op.drop_column('tokens', 'called_at')
