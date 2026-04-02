"""Rename published→submitted and submitted_at→updated_at on evaluation tables.

Unifies terminology across both evaluation tables:

* ``course_evaluation.published``   → ``submitted``   (matches ``project_evaluation``)
* ``course_evaluation.submitted_at`` → ``updated_at``  (field is refreshed on every save)
* ``project_evaluation.submitted_at`` → ``updated_at`` (same semantic change)

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-02
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename course_evaluation.published → submitted.
    op.alter_column("course_evaluation", "published", new_column_name="submitted")
    # Rename course_evaluation.submitted_at → updated_at.
    op.alter_column("course_evaluation", "submitted_at", new_column_name="updated_at")
    # Rename project_evaluation.submitted_at → updated_at.
    op.alter_column("project_evaluation", "submitted_at", new_column_name="updated_at")


def downgrade() -> None:
    op.alter_column("project_evaluation", "updated_at", new_column_name="submitted_at")
    op.alter_column("course_evaluation", "updated_at", new_column_name="submitted_at")
    op.alter_column("course_evaluation", "submitted", new_column_name="published")
