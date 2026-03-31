# Changelog

All notable changes to Family Budget will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-03-31

### Added

#### Core Features
- Monthly opening balances with debit/credit tracking
- Auto-calculation from previous month with manual override
- Full CRUD for financial operations (income and expenses)
- 5 payment types: cash, debit card, credit card, refund to debit, refund to credit
- Validation: expense payment types restricted (no refunds), income payment types restricted (no credit card)
- Recurring expense/income flag with optional forecast end date

#### Categories
- Full CRUD for categories
- Default "Other" category (protected from deletion)
- Category properties: name, description, color (hex), icon (emoji)
- Preset colors and icons in UI

#### Users
- Pre-seeded default users: Alice and Bob
- Full CRUD via UserService
- Email uniqueness enforcement with case normalization

#### Reports
- By category (pie chart + table)
- By user (table)
- By payment type (horizontal bar chart + table)
- Monthly trend (grouped bar chart)
- Balance history (line chart + table)
- Income vs expense summary (KPI metrics + savings rate)
- Next-month forecast based on recurring ops + 3-month average

#### Dashboard
- Current month KPIs: debit balance, credit balance, total income, total expenses
- Forecast KPIs for next month
- Income/expense bar chart (12 months)
- Balance trend line chart (12 months)
- Quick navigation buttons

#### Attachments
- Upload images (JPEG, PNG, GIF, WebP) and PDF files
- Per-operation attachment list with preview
- File size validation (configurable max, default 10 MB)
- Files stored in Docker volume at `/app/uploads/{operation_id}/`
- Metadata stored in PostgreSQL

#### Infrastructure
- Full PostgreSQL schema with foreign keys, constraints, indexes
- Soft delete on all user-created records
- Audit log for all CREATE/UPDATE/DELETE operations
- asyncpg connection pool with configurable min/max connections
- Rotating file logger + console logger
- Environment-based configuration (pydantic-settings)
- Docker multi-stage build (builder + runtime)
- Docker Compose with health checks, restart policies, named volumes
- GitHub Actions CI: lint (ruff) + tests + Docker build
- GitHub Actions CD: SSH deploy with health check and rollback
- Migration runner with version tracking (`schema_migrations` table)

#### Testing
- 130+ tests across backend and frontend
- 85%+ code coverage target
- pytest-asyncio with session-scoped event loop
- Table-level isolation between tests (TRUNCATE after each test)
- Unit tests for all validators and formatters (no DB required)
- Integration tests for all repositories and services

#### Documentation
- README.md with quick start
- INSTALL.md with local and Docker setup
- DEPLOYMENT.md with VPS + Nginx + rollback guide
- ARCHITECTURE.md with layer diagram and SOLID principles
- DATABASE.md with full schema reference
- TESTING.md with test patterns and CI guide
- API_INTERNAL.md with service contracts

---

## [Unreleased]

### Planned
- User authentication (optional password protection)
- CSV/Excel export for reports
- Budget targets and alerts
- Mobile-friendly responsive layout tweaks
- Multi-currency conversion
- Email notifications for budget thresholds
- Dark mode theme toggle
