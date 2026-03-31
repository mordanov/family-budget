# Family Budget

A production-ready family expense tracking web application built with Python, Streamlit, asyncpg, and PostgreSQL.

## Features

- **Monthly Opening Balances** — debit/credit balance tracking with auto-calculation and manual override
- **Financial Operations** — full CRUD for income and expenses with 5 payment types
- **Categories** — customizable categories with icons and colors
- **Multi-User** — two default users (Alice & Bob), fully extendable
- **Reports** — by category, user, payment type, month, income vs expense
- **Forecasting** — next month forecast based on recurring operations and historical averages
- **Attachments** — image and PDF uploads per operation, stored on volume
- **Dashboard** — KPI cards, balance trend chart, income/expense chart
- **Audit Log** — all changes to records are tracked

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your database credentials

# 2. Start with Docker Compose
docker compose up -d

# 3. Access the app
open http://localhost:8501
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit 1.35 |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| DB Driver | asyncpg 0.29 |
| Charts | Plotly |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## Project Structure

```
family-budget/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── config.py            # Environment-based configuration
│   ├── models/              # Data models (dataclasses + enums)
│   ├── repositories/        # Async database access layer
│   ├── services/            # Business logic layer
│   ├── ui/
│   │   ├── pages/           # Streamlit page modules
│   │   └── components/      # Reusable UI components
│   ├── db/                  # Connection pool management
│   └── utils/               # Validators, formatters, logger
├── migrations/              # SQL migration scripts
├── tests/
│   ├── backend/             # Repository and service tests
│   └── frontend/            # Chart and form unit tests
├── scripts/                 # Deployment and migration scripts
├── docs/                    # Full documentation
└── .github/workflows/       # CI/CD pipeline
```

## Documentation

- [Installation Guide](INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE.md)
- [Testing Guide](docs/TESTING.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Internal API](docs/API_INTERNAL.md)
- [Changelog](CHANGELOG.md)

## Running Tests

```bash
pip install -r requirements.txt
pytest                          # all tests with coverage
pytest tests/frontend/          # unit tests only (no DB)
pytest tests/backend/ -v        # integration tests
```

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

## License

MIT
