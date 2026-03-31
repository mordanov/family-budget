"""
Test configuration and shared fixtures.
Requires a running PostgreSQL instance or uses a dedicated test database.
Set TEST_DATABASE_URL environment variable to override default.
"""
import os
from decimal import Decimal
from datetime import datetime

import asyncpg
import pytest
import pytest_asyncio

# Override database URL for tests before importing app modules
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://budget_user:password@localhost:5432/family_budget_test",
)
os.environ["DATABASE_URL"] = TEST_DB_URL


@pytest_asyncio.fixture(scope="session")
async def db_pool():
    """Create a connection pool for the test session."""
    pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations(db_pool):
    """Apply schema migrations before tests run."""
    migrations_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "migrations"
    )
    migration_files = sorted(
        f for f in os.listdir(migrations_dir) if f.endswith(".sql")
    )
    async with db_pool.acquire() as conn:
        for fname in migration_files:
            fpath = os.path.join(migrations_dir, fname)
            with open(fpath) as f:
                sql = f.read()
            await conn.execute(sql)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(db_pool):
    """Truncate all tables before each test to ensure isolation."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            TRUNCATE TABLE
                audit_log,
                attachments,
                operations,
                recurring_rules,
                monthly_balances,
                categories,
                users
            RESTART IDENTITY CASCADE
        """)
    yield


# ── Data fixtures ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_user(db_pool) -> dict:
    async with db_pool.acquire() as conn:
        record = await conn.fetchrow(
            "INSERT INTO users(name, email) VALUES($1,$2) RETURNING *",
            "Test User", "test@example.com",
        )
    return dict(record)


@pytest_asyncio.fixture
async def sample_users(db_pool) -> list[dict]:
    async with db_pool.acquire() as conn:
        alice = await conn.fetchrow(
            "INSERT INTO users(name, email) VALUES($1,$2) RETURNING *",
            "Alice", "alice@test.com",
        )
        bob = await conn.fetchrow(
            "INSERT INTO users(name, email) VALUES($1,$2) RETURNING *",
            "Bob", "bob@test.com",
        )
    return [dict(alice), dict(bob)]


@pytest_asyncio.fixture
async def sample_category(db_pool) -> dict:
    async with db_pool.acquire() as conn:
        record = await conn.fetchrow(
            "INSERT INTO categories(name, color, icon) VALUES($1,$2,$3) RETURNING *",
            "Test Category", "#ff0000", "🧪",
        )
    return dict(record)


@pytest_asyncio.fixture
async def other_category(db_pool) -> dict:
    async with db_pool.acquire() as conn:
        record = await conn.fetchrow(
            "INSERT INTO categories(name) VALUES($1) RETURNING *",
            "Other",
        )
    return dict(record)


@pytest_asyncio.fixture
async def sample_operation(db_pool, sample_user, sample_category) -> dict:
    async with db_pool.acquire() as conn:
        record = await conn.fetchrow(
            """INSERT INTO operations(
                amount, currency, operation_type, payment_type,
                category_id, user_id, operation_date
            ) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING *""",
            Decimal("100.00"), "USD", "expense", "debit_card",
            sample_category["id"], sample_user["id"], datetime.now(),
        )
    return dict(record)
