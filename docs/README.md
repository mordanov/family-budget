# Family Budget

Family budget app with split services:
- `budget-backend` (FastAPI + Alembic + seed)
- `budget-frontend` (React/Vite static build)

Production deployment uses shared infrastructure from `web-folders`:
- shared postgres (`recipes-db`)
- shared nginx + certbot

## Local development

Run backend + frontend only (DB/nginx are external in this model):

```bash
cd /Users/aleksandr/Local/web-projects/budget-site
docker compose up -d --build
```

For hot reload:

```bash
cd /Users/aleksandr/Local/web-projects/budget-site
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Tests

Backend:

```bash
cd /Users/aleksandr/Local/web-projects/budget-site/backend
pip install -r requirements.txt -r requirements-dev.txt -r requirements-test.txt
pytest -q --tb=short
```

Frontend:

```bash
cd /Users/aleksandr/Local/web-projects/budget-site/frontend
npm install
npm test
```

## Manual VPS steps (additional)

1. **Clone or update repositories on VPS**

```bash
cd "$HOME"
if [ ! -d web-folders/.git ]; then git clone <web-folders-repo-url> web-folders; fi
if [ ! -d family-budget/.git ]; then git clone <budget-site-repo-url> family-budget; fi

git -C "$HOME/web-folders" fetch --all --prune
git -C "$HOME/web-folders" pull --ff-only

git -C "$HOME/family-budget" fetch --all --prune
git -C "$HOME/family-budget" pull --ff-only
```

2. **Create runtime env in shared stack**

```bash
cd "$HOME/web-folders"
cp .env.example .env
```

Then edit `.env` and set at least:
- `BUDGET_PRIMARY_DOMAIN`, `BUDGET_SERVER_NAMES`
- `BUDGET_POSTGRES_DB`, `BUDGET_POSTGRES_USER`, `BUDGET_POSTGRES_PASSWORD`
- `BUDGET_SECRET_KEY`
- `BUDGET_DEFAULT_USER1_*`, `BUDGET_DEFAULT_USER2_*`
- existing vars for other sites already running in this shared stack

3. **Build and start shared stack**

```bash
cd "$HOME/web-folders"
docker compose up -d --build
```

4. **Issue certificates (first deployment or new domain)**

```bash
cd "$HOME/web-folders"
./issue-certificates.sh
```

5. **Validate budget routing through shared nginx**

```bash
cd "$HOME/web-folders"
curl -fsS -H "Host: <your-budget-domain>" http://localhost/health
```

6. **Configure GitHub secrets for auto-deploy workflow**

Required in `budget-site` repository:
- `VPS_HOST`
- `VPS_USER`
- `VPS_PORT` (optional, defaults to 22)
- `VPS_SSH_KEY`
- `VPS_BUDGET_DIR` (example: `/home/<user>/family-budget`)
- `VPS_WEB_FOLDERS_DIR` (example: `/home/<user>/web-folders`)

After this, pushes to `main` run backend+frontend tests and deploy by rebuilding `budget-backend`, `budget-frontend`, and shared `nginx` in `web-folders`.
