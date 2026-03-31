import asyncio
import asyncpg
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("db.connection")

_pool: Optional[asyncpg.Pool] = None


async def create_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        logger.info("Creating database connection pool")
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=settings.DB_MIN_CONNECTIONS,
            max_size=settings.DB_MAX_CONNECTIONS,
            command_timeout=settings.DB_COMMAND_TIMEOUT,
        )
        logger.info("Database pool created successfully")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_pool() -> asyncpg.Pool:
    return await create_pool()


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[asyncpg.Connection, None]:
    async with get_connection() as conn:
        async with conn.transaction():
            yield conn


def run_async(coro):
    """
    Run an async coroutine from synchronous Streamlit context.
    Handles both cases: existing event loop and no loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an already-running loop (e.g., Jupyter, some test runners)
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            pass  # Keep loop alive for connection pool reuse


async def health_check() -> bool:
    try:
        async with get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
