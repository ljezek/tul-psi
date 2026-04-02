"""add is_active to user

Revision ID: b6c7d8e9f0a1
Revises: a2b3c4d5e6f7
Create Date: 2026-04-02

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user", "is_active")
