-- ============================================================
-- Migration 001: Initial Schema
-- Family Budget Application
-- ============================================================

BEGIN;

-- ── EXTENSIONS ────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── USERS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(deleted_at);

-- ── CATEGORIES ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    color       VARCHAR(20) DEFAULT '#808080',
    icon        VARCHAR(10) DEFAULT '📁',
    created_by  INT REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,
    deleted_at  TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name_unique
    ON categories(LOWER(name)) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_categories_deleted ON categories(deleted_at);

-- ── RECURRING RULES ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recurring_rules (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    amount          NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    operation_type  VARCHAR(20) NOT NULL CHECK (operation_type IN ('expense', 'income')),
    payment_type    VARCHAR(30) NOT NULL,
    category_id     INT NOT NULL REFERENCES categories(id),
    user_id         INT NOT NULL REFERENCES users(id),
    description     TEXT,
    frequency       VARCHAR(20) NOT NULL DEFAULT 'monthly'
                    CHECK (frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    end_date        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_recurring_rules_active
    ON recurring_rules(deleted_at, end_date);
CREATE INDEX IF NOT EXISTS idx_recurring_rules_category ON recurring_rules(category_id);
CREATE INDEX IF NOT EXISTS idx_recurring_rules_user ON recurring_rules(user_id);

-- ── OPERATIONS ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS operations (
    id                  SERIAL PRIMARY KEY,
    amount              NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    operation_type      VARCHAR(20) NOT NULL
                        CHECK (operation_type IN ('expense', 'income')),
    payment_type        VARCHAR(30) NOT NULL
                        CHECK (payment_type IN (
                            'cash', 'debit_card', 'credit_card',
                            'refund_to_debit', 'refund_to_credit'
                        )),
    category_id         INT NOT NULL REFERENCES categories(id),
    user_id             INT NOT NULL REFERENCES users(id),
    operation_date      TIMESTAMPTZ NOT NULL,
    description         TEXT,
    recurring_rule_id   INT REFERENCES recurring_rules(id) ON DELETE SET NULL,
    forecast_end_date   DATE,
    is_recurring        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_operations_date
    ON operations(operation_date) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_operations_type
    ON operations(operation_type) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_operations_category
    ON operations(category_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_operations_user
    ON operations(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_operations_deleted ON operations(deleted_at);
CREATE INDEX IF NOT EXISTS idx_operations_recurring
    ON operations(is_recurring) WHERE deleted_at IS NULL AND is_recurring = TRUE;
CREATE INDEX IF NOT EXISTS idx_operations_date_type
    ON operations(operation_date DESC, operation_type) WHERE deleted_at IS NULL;

-- ── ATTACHMENTS ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attachments (
    id              SERIAL PRIMARY KEY,
    operation_id    INT NOT NULL REFERENCES operations(id) ON DELETE CASCADE,
    file_name       VARCHAR(255) NOT NULL,
    file_path       TEXT NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    file_size       INT NOT NULL CHECK (file_size > 0),
    upload_date     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_attachments_operation
    ON attachments(operation_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_attachments_deleted ON attachments(deleted_at);

-- ── MONTHLY BALANCES ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS monthly_balances (
    id                  SERIAL PRIMARY KEY,
    year                SMALLINT NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    month               SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    debit_balance       NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (debit_balance >= 0),
    credit_balance      NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (credit_balance >= 0),
    is_manual           BOOLEAN NOT NULL DEFAULT FALSE,
    previous_month_id   INT REFERENCES monthly_balances(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ,
    CONSTRAINT uq_monthly_balances_year_month UNIQUE (year, month)
);

CREATE INDEX IF NOT EXISTS idx_monthly_balances_period
    ON monthly_balances(year DESC, month DESC);

-- ── AUDIT LOG ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    table_name  VARCHAR(100) NOT NULL,
    record_id   INT NOT NULL,
    action      VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    old_values  JSONB,
    new_values  JSONB,
    user_id     INT REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
    ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);

COMMIT;
