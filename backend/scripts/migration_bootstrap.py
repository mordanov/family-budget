import asyncio
import sys
from typing import Iterable, Set

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


APP_TABLES: Set[str] = {
    "users",
    "categories",
    "operations",
    "attachments",
    "monthly_balances",
}

LEGACY_PASSWORD_COLUMNS = ("password_hash", "password")


def decide_migration_action(table_names: Iterable[str]) -> str:
    tables = set(table_names)
    has_alembic_version = "alembic_version" in tables

    if has_alembic_version:
        return "upgrade"

    present_app_tables = tables & APP_TABLES
    if not present_app_tables:
        return "upgrade"

    if APP_TABLES.issubset(tables):
        return "stamp"

    missing = ", ".join(sorted(APP_TABLES - tables))
    raise RuntimeError(
        "Detected partially initialized legacy schema without alembic_version. "
        f"Missing tables: {missing}. Manual intervention is required."
    )


def resolve_password_column_action(column_names: Iterable[str]) -> str:
    cols = set(column_names)
    if "hashed_password" in cols:
        return "ok"

    for legacy_name in LEGACY_PASSWORD_COLUMNS:
        if legacy_name in cols:
            return f"rename:{legacy_name}"

    raise RuntimeError(
        "Users table is incompatible: expected 'hashed_password' column "
        "or a known legacy password column (password_hash/password)."
    )


def normalize_legacy_users_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names:
        return

    user_columns = [col["name"] for col in inspector.get_columns("users")]
    action = resolve_password_column_action(user_columns)
    if action.startswith("rename:"):
        old_name = action.split(":", 1)[1]
        sync_conn.exec_driver_sql(
            f"ALTER TABLE users RENAME COLUMN {old_name} TO hashed_password"
        )


async def detect_migration_action() -> str:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            def _inspect_and_normalize(sync_conn):
                normalize_legacy_users_columns(sync_conn)
                return inspect(sync_conn).get_table_names()

            table_names = await conn.run_sync(_inspect_and_normalize)
        return decide_migration_action(table_names)
    finally:
        await engine.dispose()


def main() -> int:
    action = asyncio.run(detect_migration_action())
    sys.stdout.write(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

