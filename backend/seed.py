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
    """Execute the environment-specific seed script against the database."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    # Determine which SQL file to use based on APP_ENV.
    # For local/dev we use the same rich seed data (seed_dev.sql).
    # For production we use the minimal seed data (seed_production.sql).
    # We look for seed_{app_env}.sql, falling back to seed_dev.sql for local/dev.
    env_name = settings.app_env
    sql_file = Path(__file__).parent / f"seed_{env_name}.sql"

    if env_name in ("local", "dev") and not sql_file.exists():
        sql_file = Path(__file__).parent / "seed_dev.sql"

    if not sql_file.exists():
        raise FileNotFoundError(
            f"No seed file found for environment '{settings.app_env}' at {sql_file}"
        )

    try:
        async with engine.connect() as conn:
            if reset:
                print("Resetting database …")
                for stmt in _RESET_STATEMENTS:
                    await conn.exec_driver_sql(stmt)
                await conn.commit()
                print("Reset complete.")
            else:
                # Check if seeding is already done (user table not empty).
                # This satisfies the "exactly once upon initialization" requirement.
                result = await conn.exec_driver_sql('SELECT COUNT(*) FROM "user"')
                count = result.scalar()
                if count > 0:
                    print(f"Database already contains {count} users. Skipping seeding.")
                    return

            print(f"Running {sql_file.name} …")
            sql = sql_file.read_text(encoding="utf-8")
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
