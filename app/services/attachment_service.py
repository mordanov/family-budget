import os
import uuid
from pathlib import Path
from typing import Optional

from app.repositories.attachment_repository import AttachmentRepository
from app.models.attachment import Attachment, CreateAttachmentDTO
from app.utils.validators import validate_file_size, validate_mime_type, ValidationError
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger("service.attachment")


class AttachmentService:
    def __init__(self):
        self.repo = AttachmentRepository()

    def _generate_path(self, operation_id: int, original_name: str) -> str:
        ext = Path(original_name).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        op_dir = os.path.join(settings.upload_dir_path, str(operation_id))
        os.makedirs(op_dir, exist_ok=True)
        return os.path.join(op_dir, unique_name)

    async def get_by_operation(self, operation_id: int) -> list[Attachment]:
        return await self.repo.get_by_operation(operation_id)

    async def get_by_id(self, att_id: int) -> Optional[Attachment]:
        att = await self.repo.get_by_id(att_id)
        if not att:
            raise ValidationError("id", f"Attachment {att_id} not found")
        return att

    async def upload(
        self,
        operation_id: int,
        file_name: str,
        file_bytes: bytes,
        mime_type: str,
    ) -> Attachment:
        validate_file_size(len(file_bytes), settings.max_file_size_bytes)
        validate_mime_type(mime_type, settings.allowed_mime_types_list)

        file_path = self._generate_path(operation_id, file_name)

        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except OSError as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise ValidationError("file", f"Failed to store file: {e}")

        dto = CreateAttachmentDTO(
            operation_id=operation_id,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            file_size=len(file_bytes),
        )
        attachment = await self.repo.create(dto)
        logger.info(f"Uploaded attachment id={attachment.id} op={operation_id}")
        return attachment

    async def delete(self, att_id: int) -> bool:
        att = await self.repo.get_by_id(att_id)
        if not att:
            raise ValidationError("id", f"Attachment {att_id} not found")

        result = await self.repo.delete(att_id)
        if result:
            # Remove physical file
            try:
                if os.path.exists(att.file_path):
                    os.remove(att.file_path)
            except OSError as e:
                logger.warning(f"Could not remove file {att.file_path}: {e}")
            logger.info(f"Deleted attachment id={att_id}")
        return result

    def read_file(self, att: Attachment) -> Optional[bytes]:
        try:
            with open(att.file_path, "rb") as f:
                return f.read()
        except OSError as e:
            logger.error(f"Cannot read file {att.file_path}: {e}")
            return None
