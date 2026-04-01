from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attachment import Attachment
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository[Attachment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Attachment, db)

    async def get_by_operation(self, operation_id: int) -> list[Attachment]:
        result = await self.db.execute(
            select(Attachment).where(Attachment.operation_id == operation_id)
        )
        return list(result.scalars().all())
