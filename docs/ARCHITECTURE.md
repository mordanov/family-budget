# Architecture

## Overview

Family Budget follows a **Clean Architecture / Layered Architecture** pattern with clear separation of concerns.

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                      │
│  Streamlit Pages + Reusable Components          │
│  (app/ui/)                                      │
└──────────────────────┬──────────────────────────┘
                       │ calls
┌──────────────────────▼──────────────────────────┐
│               Service Layer                     │
│  Business logic, validation, orchestration      │
│  (app/services/)                                │
└──────────────────────┬──────────────────────────┘
                       │ calls
┌──────────────────────▼──────────────────────────┐
│             Repository Layer                    │
│  Async DB access, query building                │
│  (app/repositories/)                            │
└──────────────────────┬──────────────────────────┘
                       │ uses
┌──────────────────────▼──────────────────────────┐
│               Database Layer                    │
│  asyncpg pool, connection management            │
│  (app/db/)                                      │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │   PostgreSQL    │
              └─────────────────┘
```

## Layer Responsibilities

### UI Layer (`app/ui/`)

- Streamlit page modules (`pages/`)
- Reusable components: charts, forms, tables (`components/`)
- Calls service layer only — never repositories directly
- Handles `run_async()` wrapper for async service calls
- Manages `st.session_state` for UI state

### Service Layer (`app/services/`)

- Contains all business logic
- Input validation via `app/utils/validators.py`
- Calls repositories
- Writes to audit log
- Raises `ValidationError` for invalid input
- Never imports UI or Streamlit

### Repository Layer (`app/repositories/`)

- Pure data access — no business logic
- All methods are `async`
- Uses `asyncpg.Connection` or pool
- Supports optional `conn=` parameter for transaction sharing
- Soft-delete pattern: sets `deleted_at` instead of `DELETE`

### Model Layer (`app/models/`)

- Python `dataclass` objects
- No database dependencies
- `from_record()` factory classmethod
- `to_dict()` for serialization
- Enums for type-safe constants

## Async Design

Streamlit is synchronous but `asyncpg` is async. Bridge pattern:

```python
# app/db/connection.py
import nest_asyncio
nest_asyncio.apply()

def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)
```

UI pages use `run_async(service.method(...))` to call async code.

## Configuration

All configuration via environment variables using `pydantic-settings`:

```
app/config.py → Settings class → .env file
```

## Directory Structure

```
app/
├── __init__.py
├── config.py            # pydantic-settings config
├── main.py              # Streamlit entry point + navigation
│
├── models/
│   ├── enums.py         # OperationType, PaymentType, Currency
│   ├── user.py          # User dataclass + DTOs
│   ├── category.py      # Category dataclass + DTOs
│   ├── operation.py     # Operation dataclass + DTOs + Filter
│   ├── attachment.py    # Attachment dataclass + DTO
│   └── balance.py       # MonthlyBalance + RecurringRule
│
├── db/
│   └── connection.py    # asyncpg pool, run_async helper
│
├── repositories/
│   ├── base_repository.py          # fetch_one, fetch_many, soft_delete
│   ├── user_repository.py
│   ├── category_repository.py
│   ├── operation_repository.py     # filter builder, aggregate queries
│   ├── attachment_repository.py
│   ├── balance_repository.py       # upsert, history
│   └── audit_repository.py
│
├── services/
│   ├── user_service.py
│   ├── category_service.py
│   ├── operation_service.py       # payment type validation
│   ├── balance_service.py         # auto-calculation from prev month
│   ├── report_service.py          # aggregation + forecast
│   ├── attachment_service.py      # file I/O + DB record
│   └── forecast_service.py        # recurring rule projection
│
├── ui/
│   ├── pages/
│   │   ├── dashboard.py           # KPIs + charts + navigation
│   │   ├── operations.py          # CRUD with filter
│   │   ├── categories.py          # CRUD
│   │   ├── reports.py             # 7 report tabs
│   │   └── attachments.py         # upload + browse + delete
│   └── components/
│       ├── charts.py              # Plotly chart builders
│       ├── forms.py               # Reusable input widgets
│       └── tables.py              # DataFrame renderers
│
└── utils/
    ├── logger.py                  # Rotating file + console logger
    ├── validators.py              # Pure validation functions
    └── formatters.py              # Display formatting helpers
```

## SOLID Principles Applied

- **S** — Each module has one responsibility (repo for DB, service for logic, UI for display)
- **O** — `BaseRepository` is open for extension without modification
- **L** — All repositories are substitutable via their interface
- **I** — Services and repositories are separate; UI never touches DB directly
- **D** — Services depend on repository abstractions, injected at construction
