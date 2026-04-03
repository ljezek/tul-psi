"""make course_evaluation.rating nullable

Allow rating to be NULL so that students can save draft course evaluations
before they have chosen a rating.  The CHECK constraint is updated to only
apply when the column is non-null.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-03 00:00:00

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing strict constraint, make the column nullable, then add a
    # relaxed constraint that only enforces the range when the value is present.
    op.drop_constraint("ck_course_evaluation_rating", "course_evaluation", type_="check")
    op.alter_column("course_evaluation", "rating", existing_type=sa.Integer(), nullable=True)
    op.create_check_constraint(
        "ck_course_evaluation_rating",
        "course_evaluation",
        "rating IS NULL OR (rating >= 1 AND rating <= 5)",
    )


def downgrade() -> None:
    # Restore the original NOT NULL column.  Rows that have NULL rating cannot
    # be downgraded without data loss; callers must handle this manually.
    op.drop_constraint("ck_course_evaluation_rating", "course_evaluation", type_="check")
    op.alter_column("course_evaluation", "rating", existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(
        "ck_course_evaluation_rating",
        "course_evaluation",
        "rating >= 1 AND rating <= 5",
    )
