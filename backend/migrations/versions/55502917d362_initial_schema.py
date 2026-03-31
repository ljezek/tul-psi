"""initial schema

Revision ID: 55502917d362
Revises:
Create Date: 2026-03-31 19:08:38

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "55502917d362"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables are created in foreign-key dependency order so that every
    # referenced table exists before the referencing table is created.

    # ------------------------------------------------------------------ user --
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("github_alias", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    # ---------------------------------------------------------------- course --
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("syllabus", sa.String(), nullable=True),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("project_type", sa.String(), nullable=False),
        sa.Column("min_score", sa.Integer(), nullable=False),
        sa.Column("peer_bonus_budget", sa.Integer(), nullable=True),
        sa.Column("evaluation_criteria", JSONB(), nullable=False),
        sa.Column("links", JSONB(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_code"), "course", ["code"], unique=True)

    # --------------------------------------------------------- otp_token --
    op.create_table(
        "otp_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otp_token_token_hash"), "otp_token", ["token_hash"], unique=False)

    # ------------------------------------------------------ course_lecturer --
    op.create_table(
        "course_lecturer",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("course_id", "user_id"),
    )

    # ---------------------------------------------------------------- project --
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("live_url", sa.String(length=500), nullable=True),
        sa.Column("technologies", JSONB(), nullable=False),
        sa.Column("results_unlocked", sa.Boolean(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --------------------------------------------------------- project_member --
    op.create_table(
        "project_member",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=True),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["invited_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_member_project_user"),
    )

    # --------------------------------------------------- project_evaluation --
    op.create_table(
        "project_evaluation",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), nullable=False),
        sa.Column("scores", JSONB(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lecturer_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("project_id", "lecturer_id"),
    )

    # ---------------------------------------------------- course_evaluation --
    op.create_table(
        "course_evaluation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column(
            "rating",
            sa.Integer(),
            sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_course_evaluation_rating"),
            nullable=False,
        ),
        sa.Column("strengths", sa.String(), nullable=True),
        sa.Column("improvements", sa.String(), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "student_id",
            name="uq_course_evaluation_project_student",
        ),
    )

    # ------------------------------------------------------ peer_feedback --
    op.create_table(
        "peer_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_evaluation_id", sa.Integer(), nullable=False),
        sa.Column("receiving_student_id", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.String(), nullable=True),
        sa.Column("improvements", sa.String(), nullable=True),
        sa.Column("bonus_points", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_evaluation_id"], ["course_evaluation.id"]),
        sa.ForeignKeyConstraint(["receiving_student_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop in reverse dependency order.
    op.drop_table("peer_feedback")
    op.drop_table("course_evaluation")
    op.drop_table("project_evaluation")
    op.drop_table("project_member")
    op.drop_table("project")
    op.drop_table("course_lecturer")
    op.drop_index(op.f("ix_otp_token_token_hash"), table_name="otp_token")
    op.drop_table("otp_token")
    op.drop_index(op.f("ix_course_code"), table_name="course")
    op.drop_table("course")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
