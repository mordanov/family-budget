import os
import uuid
import aiofiles
from fastapi import HTTPException, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.attachment import Attachment
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.operation_repository import OperationRepository
from app.schemas.attachment import AttachmentResponse


ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"
}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class AttachmentService:
    def __init__(self, db: AsyncSession):
        self.repo = AttachmentRepository(db)
        self.op_repo = OperationRepository(db)

    async def upload(
        self, operation_id: int, file: UploadFile, description: str | None
    ) -> AttachmentResponse:
        op = await self.op_repo.get_by_id(operation_id)
        if not op or op.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Operation not found")

        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
            )

        contents = await file.read()
        if len(contents) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
            )

        ext = os.path.splitext(file.filename or "file")[1].lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        op_dir = os.path.join(settings.UPLOAD_DIR, str(operation_id))
        os.makedirs(op_dir, exist_ok=True)
        file_path = os.path.join(op_dir, unique_name)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)

        attachment = Attachment(
            filename=unique_name,
            original_filename=file.filename or unique_name,
            file_path=file_path,
            mime_type=file.content_type,
            file_size=len(contents),
            description=description,
            operation_id=operation_id,
        )
        attachment = await self.repo.create(attachment)
        return AttachmentResponse.model_validate(attachment)

    async def get_by_operation(self, operation_id: int) -> list[AttachmentResponse]:
        attachments = await self.repo.get_by_operation(operation_id)
        return [AttachmentResponse.model_validate(a) for a in attachments]

    async def delete(self, attachment_id: int) -> None:
        att = await self.repo.get_by_id(attachment_id)
        if not att:
            raise HTTPException(status_code=404, detail="Attachment not found")
        if os.path.exists(att.file_path):
            os.remove(att.file_path)
        await self.repo.delete(att)
