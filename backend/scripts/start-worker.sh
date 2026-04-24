#!/bin/sh
set -e

python /app/backend/scripts/run_migrations.py
exec python -m backend.app.worker.worker
