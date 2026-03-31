from typing import Any, Optional
import asyncpg

from app.db.connection import get_connection, get_transaction
from app.utils.logger import get_logger


class BaseRepository:
    """Base repository providing common DB operations."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.logger = get_logger(f"repository.{table_name}")

    async def fetch_one(
        self, query: str, *args, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[asyncpg.Record]:
        if conn:
            return await conn.fetchrow(query, *args)
        async with get_connection() as c:
            return await c.fetchrow(query, *args)

    async def fetch_many(
        self, query: str, *args, conn: Optional[asyncpg.Connection] = None
    ) -> list[asyncpg.Record]:
        if conn:
            return await conn.fetch(query, *args)
        async with get_connection() as c:
            return await c.fetch(query, *args)

    async def fetch_val(
        self, query: str, *args, conn: Optional[asyncpg.Connection] = None
    ) -> Any:
        if conn:
            return await conn.fetchval(query, *args)
        async with get_connection() as c:
            return await c.fetchval(query, *args)

    async def execute(
        self, query: str, *args, conn: Optional[asyncpg.Connection] = None
    ) -> str:
        if conn:
            return await conn.execute(query, *args)
        async with get_connection() as c:
            return await c.execute(query, *args)

    async def execute_many(
        self, query: str, args_list: list, conn: Optional[asyncpg.Connection] = None
    ) -> None:
        if conn:
            await conn.executemany(query, args_list)
            return
        async with get_connection() as c:
            await c.executemany(query, args_list)

    async def count(
        self, where: str = "", *args, conn: Optional[asyncpg.Connection] = None
    ) -> int:
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where:
            query += f" WHERE {where}"
        result = await self.fetch_val(query, *args, conn=conn)
        return result or 0

    async def soft_delete(
        self, record_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        query = f"""
            UPDATE {self.table_name}
            SET deleted_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING id
        """
        result = await self.fetch_val(query, record_id, conn=conn)
        return result is not None

    async def exists(
        self, record_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        query = f"""
            SELECT EXISTS(
                SELECT 1 FROM {self.table_name}
                WHERE id = $1 AND deleted_at IS NULL
            )
        """
        return await self.fetch_val(query, record_id, conn=conn)
