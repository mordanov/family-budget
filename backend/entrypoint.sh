#!/bin/bash
set -e

echo "⏳ Running Alembic migrations..."
MIGRATION_ACTION=$(python -m scripts.migration_bootstrap)

if [ "$MIGRATION_ACTION" = "stamp" ]; then
  echo "ℹ️ Legacy schema detected without alembic_version, stamping head..."
  alembic stamp head
fi

alembic upgrade head

echo "🌱 Running database seed..."
python -m scripts.seed

echo "🚀 Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
