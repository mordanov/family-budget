#!/usr/bin/env bash
# ============================================================
# deploy.sh — Production deployment script for VPS
# Usage: ./scripts/deploy.sh
#
# Required environment variables:
#   VPS_HOST      — VPS IP or hostname
#   VPS_USER      — SSH user (e.g. deploy)
#   VPS_APP_DIR   — Remote app directory (e.g. /opt/family-budget)
#   DOCKER_IMAGE  — Full image name (e.g. ghcr.io/user/family-budget:latest)
#   SSH_PRIVATE_KEY — Path to SSH private key file
# ============================================================
set -euo pipefail

# ── Variables ─────────────────────────────────────────────────────────────
VPS_HOST="${VPS_HOST:?VPS_HOST not set}"
VPS_USER="${VPS_USER:?VPS_USER not set}"
VPS_APP_DIR="${VPS_APP_DIR:-/opt/family-budget}"
DOCKER_IMAGE="${DOCKER_IMAGE:-ghcr.io/username/family-budget:latest}"
SSH_PRIVATE_KEY="${SSH_PRIVATE_KEY:-~/.ssh/id_rsa}"
SSH_OPTS="-i ${SSH_PRIVATE_KEY} -o StrictHostKeyChecking=no -o ConnectTimeout=30"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
ssh_run() { ssh ${SSH_OPTS} "${VPS_USER}@${VPS_HOST}" "$@"; }
scp_run() { scp ${SSH_OPTS} "$@"; }

log "==> Starting deployment to ${VPS_HOST}"

# ── 1. Copy compose file ──────────────────────────────────────────────────
log "--> Uploading docker-compose.yml..."
scp_run "$(dirname "$0")/../docker-compose.yml" \
    "${VPS_USER}@${VPS_HOST}:${VPS_APP_DIR}/docker-compose.yml"

# ── 2. Pull latest image ──────────────────────────────────────────────────
log "--> Pulling ${DOCKER_IMAGE}..."
ssh_run "docker pull ${DOCKER_IMAGE}"

# ── 3. Run migrations ─────────────────────────────────────────────────────
log "--> Running database migrations..."
ssh_run "cd ${VPS_APP_DIR} && \
    DOCKER_IMAGE=${DOCKER_IMAGE} \
    docker compose run --rm migrate"

# ── 4. Restart app service ────────────────────────────────────────────────
log "--> Restarting app service..."
ssh_run "cd ${VPS_APP_DIR} && \
    DOCKER_IMAGE=${DOCKER_IMAGE} \
    docker compose up -d --no-deps --force-recreate app"

# ── 5. Health check ───────────────────────────────────────────────────────
log "--> Waiting for health check..."
MAX_RETRIES=12
RETRY=0
until ssh_run "curl -sf http://localhost:8501/_stcore/health" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ ${RETRY} -ge ${MAX_RETRIES} ]; then
        log "ERROR: Health check failed after ${MAX_RETRIES} attempts"
        log "--> Rolling back to previous version..."
        ssh_run "cd ${VPS_APP_DIR} && docker compose restart app" || true
        exit 1
    fi
    log "    Waiting... (${RETRY}/${MAX_RETRIES})"
    sleep 10
done

# ── 6. Prune old images ───────────────────────────────────────────────────
log "--> Pruning old Docker images..."
ssh_run "docker image prune -f --filter 'until=24h'" || true

log "==> Deployment completed successfully!"
