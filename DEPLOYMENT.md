# Deployment Guide

## VPS Deployment via GitHub Actions

### Required GitHub Secrets

Configure these secrets in your repository under **Settings → Secrets → Actions**:

| Secret | Description |
|--------|-------------|
| `VPS_HOST` | VPS IP address or hostname |
| `VPS_USER` | SSH username (e.g., `deploy`) |
| `VPS_SSH_PRIVATE_KEY` | Private SSH key for VPS access |
| `VPS_APP_DIR` | App directory on VPS (e.g., `/opt/family-budget`) |

### VPS Initial Setup

```bash
# 1. Create app directory
sudo mkdir -p /opt/family-budget
sudo chown $USER:$USER /opt/family-budget

# 2. Copy .env file to VPS
scp .env user@your-vps:/opt/family-budget/.env

# 3. Install Docker on VPS
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 4. Log in to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Deployment Flow

1. Push to `main` branch triggers `deploy.yml`
2. Workflow SSHes into VPS
3. Pulls latest Docker image from GHCR
4. Runs database migrations via `migrate` service
5. Restarts the `app` service with zero-downtime
6. Polls health check endpoint until healthy
7. Prunes old Docker images

### Manual Deployment

```bash
export VPS_HOST=your.vps.ip
export VPS_USER=deploy
export VPS_APP_DIR=/opt/family-budget
export DOCKER_IMAGE=ghcr.io/youruser/family-budget:latest
export SSH_PRIVATE_KEY=~/.ssh/deploy_key

./scripts/deploy.sh
```

### Rollback

If deployment fails, the script attempts an automatic restart of the previous container.
For manual rollback:

```bash
# On VPS: pull specific tag
docker pull ghcr.io/youruser/family-budget:sha-<previous-commit-sha>

# Update compose file tag and restart
DOCKER_IMAGE=ghcr.io/youruser/family-budget:sha-<previous-sha> \
  docker compose up -d --no-deps app
```

### Nginx Configuration

Assuming Nginx is already configured as a reverse proxy, add this server block:

```nginx
server {
    listen 80;
    server_name budget.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name budget.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/budget.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/budget.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Monitoring

```bash
# Container health
docker compose ps

# App logs
docker compose logs -f app --tail=100

# Database logs
docker compose logs -f db --tail=50

# Resource usage
docker stats family_budget_app family_budget_db
```

### Database Backup

```bash
# Manual backup
export DATABASE_URL=postgresql://...
./scripts/backup.sh

# Schedule with cron (run daily at 2 AM)
0 2 * * * /opt/family-budget/scripts/backup.sh >> /var/log/budget-backup.log 2>&1
```
