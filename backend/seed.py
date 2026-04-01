"""Thin wrapper that executes seed.sql against the configured database.

Usage
-----
    # From backend/ with .env present:
    python seed.py           # idempotent — skips rows that already exist
    python seed.py --reset   # clears all data first, then re-seeds
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

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
    """Return non-empty SQL statements split from *sql* on semicolons.

    Comments are stripped before splitting so that semicolons inside
    comment text do not produce spurious empty or broken statements.
    """
    # Strip full-line comments first so their semicolons are never seen.
    stripped_lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    sql_no_comments = "\n".join(stripped_lines)

    stmts = []
    for raw in sql_no_comments.split(";"):
        stmt = raw.strip()
        if stmt:
            stmts.append(stmt)
    return stmts


async def _run(*, reset: bool) -> None:
    """Execute seed.sql against the configured database."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    try:
        async with engine.connect() as conn:
            if reset:
                print("Resetting database …")
                for stmt in _RESET_STATEMENTS:
                    await conn.exec_driver_sql(stmt)
                await conn.commit()
                print("Reset complete.")

            print(f"Running {_SQL_FILE.name} …")
            sql = _SQL_FILE.read_text(encoding="utf-8")
            for stmt in _iter_statements(sql):
                await conn.exec_driver_sql(stmt)
            await conn.commit()
    finally:
        await engine.dispose()

    print("Done.")


def main() -> None:
    """Parse arguments and run the seeding coroutine."""
    parser = argparse.ArgumentParser(description="Seed the development database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing rows before seeding (full re-seed).",
    )
    args = parser.parse_args()
    asyncio.run(_run(reset=args.reset))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
