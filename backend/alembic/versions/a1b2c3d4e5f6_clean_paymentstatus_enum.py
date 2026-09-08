"""clean paymentstatus enum - remove orphaned CREATED value

Revision ID: a1b2c3d4e5f6
Revises: 0ba77f9ff88f
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0ba77f9ff88f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL does not support REMOVAL of enum values.
    # Recreate the enum type with only the intended values.
    # Both payments.status AND appointments.payment_status share this enum type.
    op.execute("ALTER TABLE payments ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("ALTER TABLE appointments ALTER COLUMN payment_status TYPE VARCHAR(20)")
    op.execute("DROP TYPE paymentstatus")
    op.execute(
        "CREATE TYPE paymentstatus AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED')"
    )
    op.execute(
        "ALTER TABLE payments ALTER COLUMN status TYPE paymentstatus USING status::paymentstatus"
    )
    op.execute(
        "ALTER TABLE appointments ALTER COLUMN payment_status TYPE paymentstatus USING payment_status::paymentstatus"
    )


def downgrade() -> None:
    # Recreate with the old CREATED value included
    op.execute("ALTER TABLE payments ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("ALTER TABLE appointments ALTER COLUMN payment_status TYPE VARCHAR(20)")
    op.execute("DROP TYPE paymentstatus")
    op.execute(
        "CREATE TYPE paymentstatus AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED', 'CREATED')"
    )
    op.execute(
        "ALTER TABLE payments ALTER COLUMN status TYPE paymentstatus USING status::paymentstatus"
    )
    op.execute(
        "ALTER TABLE appointments ALTER COLUMN payment_status TYPE paymentstatus USING payment_status::paymentstatus"
    )
