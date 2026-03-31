from typing import Optional, Any
import json
import asyncpg

from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__("audit_log")

    async def log(
        self,
        table_name: str,
        record_id: int,
        action: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        user_id: Optional[int] = None,
        conn: Optional[asyncpg.Connection] = None,
    ) -> None:
        query = """
            INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        await self.execute(
            query,
            table_name,
            record_id,
            action,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            user_id,
            conn=conn,
        )

    async def get_for_record(
        self,
        table_name: str,
        record_id: int,
        limit: int = 50,
        conn: Optional[asyncpg.Connection] = None,
    ) -> list[dict]:
        query = """
            SELECT id, table_name, record_id, action, old_values, new_values,
                   user_id, created_at
            FROM audit_log
            WHERE table_name = $1 AND record_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """
        records = await self.fetch_many(query, table_name, record_id, limit, conn=conn)
        return [dict(r) for r in records]

    async def get_recent(
        self, limit: int = 100, conn: Optional[asyncpg.Connection] = None
    ) -> list[dict]:
        query = """
            SELECT al.id, al.table_name, al.record_id, al.action,
                   al.old_values, al.new_values, al.user_id, al.created_at,
                   u.name AS user_name
            FROM audit_log al
            LEFT JOIN users u ON u.id = al.user_id
            ORDER BY al.created_at DESC
            LIMIT $1
        """
        records = await self.fetch_many(query, limit, conn=conn)
        return [dict(r) for r in records]
