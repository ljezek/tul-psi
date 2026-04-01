"""Thin wrapper that executes seed.sql against the configured database.

Usage
-----
    # From backend/ with .env present:
    python seed.py           # idempotent — skips rows that already exist
    python seed.py --reset   # clears all data first, then re-seeds
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text
from sqlmodel import create_engine

from settings import get_settings

_SQL_FILE = Path(__file__).with_suffix(".sql")

# DELETE order respects FK dependencies — children before parents.
_RESET_STATEMENTS = [
    "DELETE FROM peer_feedback",
    "DELETE FROM course_evaluation",
    "DELETE FROM project_evaluation",
    "DELETE FROM project_member",
    "DELETE FROM course_lecturer",
    "DELETE FROM project",
    "DELETE FROM otp_token",
    "DELETE FROM course",
    'DELETE FROM "user"',
]


def _iter_statements(sql: str) -> list[str]:
    """Return non-empty SQL statements split from *sql* on semicolons."""
    stmts = []
    for raw in sql.split(";"):
        # Drop full-line comments, then keep the statement if anything remains.
        lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            stmts.append(stmt)
    return stmts


def main() -> None:
    """Execute seed.sql against the configured database."""
    parser = argparse.ArgumentParser(description="Seed the development database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing rows before seeding (full re-seed).",
    )
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)

    with engine.connect() as conn:
        if args.reset:
            print("Resetting database …")
            for stmt in _RESET_STATEMENTS:
                conn.execute(text(stmt))
            conn.commit()
            print("Reset complete.")

        print(f"Running {_SQL_FILE.name} …")
        sql = _SQL_FILE.read_text(encoding="utf-8")
        for stmt in _iter_statements(sql):
            conn.execute(text(stmt))
        conn.commit()

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
