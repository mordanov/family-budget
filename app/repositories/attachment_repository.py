from typing import Optional
import asyncpg

from app.repositories.base_repository import BaseRepository
from app.models.attachment import Attachment, CreateAttachmentDTO


class AttachmentRepository(BaseRepository):
    def __init__(self):
        super().__init__("attachments")

    async def get_by_id(
        self, att_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Attachment]:
        query = """
            SELECT id, operation_id, file_name, file_path, mime_type,
                   file_size, upload_date, created_at, deleted_at
            FROM attachments
            WHERE id = $1 AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, att_id, conn=conn)
        return Attachment.from_record(dict(record)) if record else None

    async def get_by_operation(
        self, operation_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> list[Attachment]:
        query = """
            SELECT id, operation_id, file_name, file_path, mime_type,
                   file_size, upload_date, created_at, deleted_at
            FROM attachments
            WHERE operation_id = $1 AND deleted_at IS NULL
            ORDER BY upload_date DESC
        """
        records = await self.fetch_many(query, operation_id, conn=conn)
        return [Attachment.from_record(dict(r)) for r in records]

    async def create(
        self, dto: CreateAttachmentDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Attachment:
        query = """
            INSERT INTO attachments (operation_id, file_name, file_path, mime_type, file_size)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, operation_id, file_name, file_path, mime_type,
                      file_size, upload_date, created_at, deleted_at
        """
        record = await self.fetch_one(
            query,
            dto.operation_id, dto.file_name, dto.file_path, dto.mime_type, dto.file_size,
            conn=conn,
        )
        return Attachment.from_record(dict(record))

    async def delete(
        self, att_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        return await self.soft_delete(att_id, conn=conn)

    async def delete_by_operation(
        self, operation_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> int:
        query = """
            UPDATE attachments
            SET deleted_at = NOW()
            WHERE operation_id = $1 AND deleted_at IS NULL
        """
        result = await self.execute(query, operation_id, conn=conn)
        # result is like "UPDATE 3"
        try:
            return int(result.split()[-1])
        except (IndexError, ValueError):
            return 0
