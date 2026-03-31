#!/usr/bin/env bash
# Run all SQL migrations in order against the target database.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="${SCRIPT_DIR}/../migrations"
DB_URL="${DATABASE_URL:-postgresql://budget_user:password@localhost:5432/family_budget}"

echo "==> Running migrations from: ${MIGRATIONS_DIR}"
echo "==> Target: ${DB_URL}"

# Ensure psql is available
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql not found. Install postgresql-client."
    exit 1
fi

for migration in "${MIGRATIONS_DIR}"/*.sql; do
    fname=$(basename "${migration}")
    echo "    Applying ${fname}..."
    psql "${DB_URL}" -f "${migration}" --single-transaction
    echo "    ✓ ${fname} applied"
done

echo "==> All migrations applied successfully."
