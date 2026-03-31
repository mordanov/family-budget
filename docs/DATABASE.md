# Database Schema

## Overview

PostgreSQL 16 with 7 tables. All user-generated records use **soft delete** (`deleted_at` column).

## Entity Relationship Diagram

```
users ──────────────────────────────────────────────────────┐
  │ id, name, email, created_at, updated_at, deleted_at     │
  │                                                         │
  ├──< categories (created_by)                              │
  │       id, name, description, color, icon,               │
  │       created_by(FK), created_at, ...                   │
  │                                                         │
  ├──< recurring_rules                                      │
  │       id, name, amount, currency, operation_type,       │
  │       payment_type, category_id(FK), user_id(FK),       │
  │       frequency, end_date, ...                          │
  │                                                         │
  └──< operations ─────────────────────────────────────────┤
          id, amount, currency, operation_type,             │
          payment_type, category_id(FK), user_id(FK),       │
          operation_date, description,                      │
          recurring_rule_id(FK), forecast_end_date,         │
          is_recurring, created_at, updated_at, deleted_at  │
          │                                                 │
          └──< attachments                                  │
                  id, operation_id(FK), file_name,          │
                  file_path, mime_type, file_size,          │
                  upload_date, created_at, deleted_at       │
                                                            │
monthly_balances                                            │
  id, year, month (UNIQUE), debit_balance, credit_balance,  │
  is_manual, previous_month_id(self-FK), ...                │
                                                            │
audit_log                                                   │
  id, table_name, record_id, action, old_values(JSONB),     │
  new_values(JSONB), user_id(FK), created_at               ─┘
```

## Tables

### users

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | Soft delete |

### categories

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name | VARCHAR(100) | UNIQUE (case-insensitive) |
| description | TEXT | |
| color | VARCHAR(20) | Hex color code |
| icon | VARCHAR(10) | Emoji |
| created_by | INT FK | → users.id |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | Soft delete |

### operations

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| amount | NUMERIC(14,2) | CHECK > 0 |
| currency | VARCHAR(3) | USD, EUR, RUB, GBP |
| operation_type | VARCHAR(20) | `expense` or `income` |
| payment_type | VARCHAR(30) | See enum values |
| category_id | INT FK | → categories.id |
| user_id | INT FK | → users.id |
| operation_date | TIMESTAMPTZ | |
| description | TEXT | |
| recurring_rule_id | INT FK | → recurring_rules.id |
| forecast_end_date | DATE | For recurring forecast |
| is_recurring | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | Soft delete |

**payment_type values:**
- `cash`
- `debit_card`
- `credit_card`
- `refund_to_debit`
- `refund_to_credit`

**Constraint:** `refund_to_debit` and `refund_to_credit` are only valid for income operations (enforced in service layer).

### attachments

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| operation_id | INT FK | → operations.id ON DELETE CASCADE |
| file_name | VARCHAR(255) | Original filename |
| file_path | TEXT | Absolute path on volume |
| mime_type | VARCHAR(100) | image/jpeg, application/pdf, etc. |
| file_size | INT | Bytes, CHECK > 0 |
| upload_date | TIMESTAMPTZ | DEFAULT NOW() |
| created_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | Soft delete (file kept on disk) |

### monthly_balances

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| year | SMALLINT | CHECK 2000-2100 |
| month | SMALLINT | CHECK 1-12 |
| debit_balance | NUMERIC(14,2) | Opening debit balance |
| credit_balance | NUMERIC(14,2) | Opening credit balance |
| is_manual | BOOLEAN | TRUE = user-set |
| previous_month_id | INT FK | → monthly_balances.id |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| **UNIQUE** | (year, month) | |

### recurring_rules

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name | VARCHAR(255) | |
| amount | NUMERIC(14,2) | CHECK > 0 |
| currency | VARCHAR(3) | |
| operation_type | VARCHAR(20) | expense/income |
| payment_type | VARCHAR(30) | |
| category_id | INT FK | → categories.id |
| user_id | INT FK | → users.id |
| description | TEXT | |
| frequency | VARCHAR(20) | daily/weekly/monthly/yearly |
| end_date | TIMESTAMPTZ | NULL = no end |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | Soft delete |

### audit_log

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| table_name | VARCHAR(100) | |
| record_id | INT | |
| action | VARCHAR(20) | CREATE/UPDATE/DELETE |
| old_values | JSONB | Previous state |
| new_values | JSONB | New state |
| user_id | INT FK | → users.id |
| created_at | TIMESTAMPTZ | |

## Indexes

All major query patterns are indexed:
- `operations(operation_date)` — date range filters
- `operations(operation_type)` — type filters
- `operations(category_id)` — category reports
- `operations(user_id)` — user reports
- `operations(is_recurring)` — forecast queries
- `categories(LOWER(name))` — case-insensitive name lookup
- `monthly_balances(year, month)` — period lookup
- `audit_log(table_name, record_id)` — audit history lookup

## Migrations

Applied in order from the `migrations/` directory:
1. `001_initial_schema.sql` — creates all tables, indexes, constraints
2. `002_seed_data.sql` — inserts default users, categories, initial balance

Migration state tracked in `schema_migrations` table (managed by `run_migrations.py`).
