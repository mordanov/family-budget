#!/usr/bin/env python3
"""
Run all SQL migrations from the /migrations directory in sorted order.
Used by the 'migrate' Docker Compose service.
"""
import asyncio
import os
import sys
from pathlib import Path


MIGRATIONS_DIR = Path("/migrations")
DATABASE_URL = os.environ["DATABASE_URL"]


async def run():
    import asyncpg

    print(f"Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    # Ensure migrations table exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    for mf in migration_files:
        version = mf.stem  # e.g. "001_initial_schema"

        already_applied = await conn.fetchval(
            "SELECT version FROM schema_migrations WHERE version = $1", version
        )
        if already_applied:
            print(f"  SKIP  {mf.name} (already applied)")
            continue

        print(f"  APPLY {mf.name}...")
        sql = mf.read_text()
        async with conn.transaction():
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO schema_migrations (version) VALUES ($1)", version
            )
        print(f"  OK    {mf.name}")

    await conn.close()
    print("All migrations complete.")


if __name__ == "__main__":
    asyncio.run(run())
