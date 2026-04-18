# Start script for the Student Projects Catalogue backend.
#
# 1. Applies any pending Alembic database migrations using the migration
#    connection URL (DATABASE_MIGRATION_URL).  This keeps the schema in sync
#    every time the backend starts without requiring a separate migration step.
#
# 2. Starts the Uvicorn ASGI server, replacing the current process so that
#    Ctrl+C is forwarded directly to Uvicorn.
#
# Usage (from the backend/ directory):
#   .\start.ps1                        # production-style (no auto-reload)
#   .\start.ps1 --reload               # development with auto-reload
#   .\start.ps1 --host 0.0.0.0        # override any uvicorn option
#
# Environment variables (see .env.example):
#   DATABASE_MIGRATION_URL   admin DB URL used by Alembic (DDL+DML)
#   DATABASE_URL             application DB URL used by FastAPI (DML only)
#
# All arguments passed to this script are forwarded verbatim to uvicorn.

$ErrorActionPreference = "Stop"

Write-Host "==> Running database migrations..."
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Error "Alembic migration failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "==> Seeding database..."
python seed.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Database seeding failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "==> Starting application server..."
uvicorn main:app @args
exit $LASTEXITCODE
