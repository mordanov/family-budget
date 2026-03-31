# Installation Guide

## Prerequisites

- Python 3.12+
- PostgreSQL 14+ (or use Docker Compose to run it)
- Docker & Docker Compose (for containerized deployment)

## Local Development (without Docker)

### 1. Clone the repository

```bash
git clone <your-repo-url> family-budget
cd family-budget
```

### 2. Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL
```

### 5. Create database and apply migrations

```bash
# Create the database
createdb family_budget

# Apply migrations
./scripts/migrate.sh
# or manually:
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_seed_data.sql
```

### 6. Run the application

```bash
streamlit run app/main.py
# App available at http://localhost:8501
```

## Docker Compose (Recommended)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY
```

### 2. Start all services

```bash
docker compose up -d
```

This starts:
- `db` — PostgreSQL 16 with persistent volume
- `migrate` — runs migrations once then exits
- `app` — Streamlit application on port 8501

### 3. Access the application

```
http://localhost:8501
```

### 4. View logs

```bash
docker compose logs -f app      # application logs
docker compose logs -f db       # database logs
```

### 5. Stop

```bash
docker compose down             # stop containers, keep volumes
docker compose down -v          # stop and remove volumes (data loss!)
```

## Troubleshooting

### Database connection fails

```bash
# Check DB is running
docker compose ps db

# Test connection manually
psql $DATABASE_URL -c "SELECT 1"
```

### Port 8501 already in use

```bash
# Change port in docker-compose.yml
ports:
  - "127.0.0.1:8502:8501"
```

### Migrations fail

```bash
# Check migration output
docker compose logs migrate

# Re-run migrations manually
docker compose run --rm migrate
```

### Reset all data

```bash
docker compose down -v
docker compose up -d
```
