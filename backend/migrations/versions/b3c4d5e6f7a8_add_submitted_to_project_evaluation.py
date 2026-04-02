"""Add submitted column to project_evaluation table.

The ``submitted`` boolean tracks whether a lecturer has finalised their
project evaluation.  ``False`` (the default) means the row is a draft that
can still be updated; ``True`` means the evaluation has been submitted and
triggers the automatic project-result unlock check.

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-02
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the submitted column with a server-side default of FALSE so existing
    # rows are treated as unsubmitted drafts after the migration runs.
    op.add_column(
        "project_evaluation",
        sa.Column("submitted", sa.Boolean(), nullable=False, server_default="false"),
    )
    # Remove the server default after backfilling so that new rows must be
    # explicit about the submitted state.
    op.alter_column("project_evaluation", "submitted", server_default=None)


def downgrade() -> None:
    op.drop_column("project_evaluation", "submitted")
