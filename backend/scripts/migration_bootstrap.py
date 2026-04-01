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


async def detect_migration_action() -> str:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        return decide_migration_action(table_names)
    finally:
        await engine.dispose()


def main() -> int:
    action = asyncio.run(detect_migration_action())
    sys.stdout.write(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

