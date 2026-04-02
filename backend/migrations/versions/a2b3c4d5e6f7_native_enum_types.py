"""Convert enum-backed VARCHAR columns to native PostgreSQL enum types.

The ``user.role``, ``course.term``, and ``course.project_type`` columns were
initially created as plain VARCHAR.  Switching them to native PG enums gives
the database a type-level constraint equivalent to the Python enums, and
ensures that asyncpg binds enum filter values without needing an explicit cast.

Revision ID: a2b3c4d5e6f7
Revises: 55502917d362
Create Date: 2026-04-01
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "55502917d362"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the native PostgreSQL enum types.  Using raw SQL gives full control
    # over the USING clause required when casting existing VARCHAR values.
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'LECTURER', 'STUDENT')")
    op.execute("CREATE TYPE courseterm AS ENUM ('SUMMER', 'WINTER')")
    op.execute("CREATE TYPE projecttype AS ENUM ('TEAM', 'INDIVIDUAL')")

    # Alter the columns; the USING clause casts each existing string value to
    # the newly created enum type.  All stored values already match the enum
    # members exactly, so no data loss or conversion errors are possible.
    op.execute('ALTER TABLE "user" ALTER COLUMN role TYPE userrole USING role::userrole')
    op.execute("ALTER TABLE course ALTER COLUMN term TYPE courseterm USING term::courseterm")
    op.execute(
        "ALTER TABLE course ALTER COLUMN project_type"
        " TYPE projecttype USING project_type::projecttype"
    )


def downgrade() -> None:
    # Revert the columns back to VARCHAR before dropping the enum types.
    # PG does not allow dropping a type that is still referenced by a column.
    op.execute('ALTER TABLE "user" ALTER COLUMN role TYPE VARCHAR USING role::VARCHAR')
    op.execute("ALTER TABLE course ALTER COLUMN term TYPE VARCHAR USING term::VARCHAR")
    op.execute(
        "ALTER TABLE course ALTER COLUMN project_type TYPE VARCHAR USING project_type::VARCHAR"
    )

    op.execute("DROP TYPE userrole")
    op.execute("DROP TYPE courseterm")
    op.execute("DROP TYPE projecttype")
