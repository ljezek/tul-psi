"""fix_announcement_datetime_timezone

Revision ID: f1a2b3c4d5e6
Revises: ec57489786a6
Create Date: 2026-05-07 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "ec57489786a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: convert announcement timestamps to timezone-aware columns.

    The initial migration created these as TIMESTAMP WITHOUT TIME ZONE.  The
    application uses UTC-aware datetimes, which asyncpg rejects for tz-naive
    columns. This migration converts the column types, interpreting any existing
    stored values as UTC.
    """
    op.alter_column(
        "announcement",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "announcement",
        "updated_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    """Downgrade schema: revert announcement timestamps to timezone-naive columns."""
    op.alter_column(
        "announcement",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "announcement",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
