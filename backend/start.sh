#!/usr/bin/env bash
# Start script for the Student Projects Catalogue backend.
#
# 1. Applies any pending Alembic database migrations using the admin
#    connection URL (DATABASE_ADMIN_URL).  This keeps the schema in sync
#    every time the backend starts without requiring a separate migration step.
#
# 2. Replaces this shell process with the Uvicorn ASGI server (exec) so that
#    signals (SIGTERM, SIGINT) are forwarded directly to Uvicorn.
#
# Usage (from the backend/ directory):
#   ./start.sh                       # production-style (no auto-reload)
#   ./start.sh --reload              # development with auto-reload
#   ./start.sh --host 0.0.0.0        # override any uvicorn option
#
# Environment variables (see .env.example):
#   DATABASE_ADMIN_URL   admin DB URL used by Alembic (DDL+DML)
#   DATABASE_URL         application DB URL used by FastAPI (DML only)
#
# All positional arguments are forwarded verbatim to uvicorn.

set -euo pipefail

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting application server..."
exec uvicorn main:app "$@"
