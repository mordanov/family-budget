from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Attachment:
    id: int
    operation_id: int
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    upload_date: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == "application/pdf"

    @property
    def file_size_kb(self) -> float:
        return self.file_size / 1024

    @property
    def file_size_mb(self) -> float:
        return self.file_size / (1024 * 1024)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_record(cls, record: dict) -> "Attachment":
        return cls(
            id=record["id"],
            operation_id=record["operation_id"],
            file_name=record["file_name"],
            file_path=record["file_path"],
            mime_type=record["mime_type"],
            file_size=record["file_size"],
            upload_date=record["upload_date"],
            created_at=record["created_at"],
            deleted_at=record.get("deleted_at"),
        )


@dataclass
class CreateAttachmentDTO:
    operation_id: int
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
