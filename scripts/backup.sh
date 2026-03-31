#!/usr/bin/env bash
# ============================================================
# backup.sh — PostgreSQL database backup script
# Usage: ./scripts/backup.sh
# ============================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups/family-budget}"
DB_URL="${DATABASE_URL:-postgresql://budget_user:password@localhost:5432/family_budget}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

mkdir -p "${BACKUP_DIR}"

log "==> Starting backup to ${BACKUP_FILE}..."
pg_dump "${DB_URL}" | gzip > "${BACKUP_FILE}"
log "    Backup size: $(du -sh "${BACKUP_FILE}" | cut -f1)"

# Remove backups older than retention period
log "--> Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
log "    Done."

log "==> Backup completed: ${BACKUP_FILE}"
