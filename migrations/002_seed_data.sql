-- ============================================================
-- Migration 002: Seed Data
-- Default users, categories, and initial balances
-- ============================================================

BEGIN;

-- ── DEFAULT USERS ─────────────────────────────────────────────────────────
INSERT INTO users (name, email) VALUES
    ('Alice', 'alice@family.local'),
    ('Bob',   'bob@family.local')
ON CONFLICT (email) DO NOTHING;

-- ── DEFAULT CATEGORIES ────────────────────────────────────────────────────
INSERT INTO categories (name, description, color, icon) VALUES
    ('Other',           'Default uncategorized',     '#808080', '📁'),
    ('Housing',         'Rent, mortgage, utilities',  '#3498db', '🏠'),
    ('Food & Dining',   'Groceries and restaurants',  '#2ecc71', '🍔'),
    ('Transport',       'Car, fuel, public transit',  '#e67e22', '🚗'),
    ('Healthcare',      'Medical and pharmacy',       '#e74c3c', '💊'),
    ('Education',       'Books, courses, tuition',    '#9b59b6', '📚'),
    ('Entertainment',   'Games, hobbies, leisure',    '#f39c12', '🎮'),
    ('Travel',          'Flights, hotels, vacation',  '#1abc9c', '✈️'),
    ('Clothing',        'Clothes and accessories',    '#e91e63', '👗'),
    ('Utilities',       'Electricity, water, gas',    '#34495e', '💡'),
    ('Salary',          'Monthly salary income',      '#27ae60', '💰'),
    ('Freelance',       'Contract and freelance work','#16a085', '💻'),
    ('Subscriptions',   'Netflix, Spotify, etc.',     '#8e44ad', '📱'),
    ('Savings',         'Savings and investments',    '#2980b9', '🏦'),
    ('Gifts',           'Gifts given and received',   '#c0392b', '🎁')
ON CONFLICT DO NOTHING;

-- ── INITIAL MONTHLY BALANCE (current month) ───────────────────────────────
DO $$
DECLARE
    curr_year  SMALLINT := EXTRACT(YEAR FROM NOW())::SMALLINT;
    curr_month SMALLINT := EXTRACT(MONTH FROM NOW())::SMALLINT;
BEGIN
    INSERT INTO monthly_balances (year, month, debit_balance, credit_balance, is_manual)
    VALUES (curr_year, curr_month, 0.00, 0.00, TRUE)
    ON CONFLICT (year, month) DO NOTHING;
END $$;

COMMIT;
