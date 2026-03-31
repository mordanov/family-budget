from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#808080"
    icon: Optional[str] = "📁"
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_record(cls, record: dict) -> "Category":
        return cls(
            id=record["id"],
            name=record["name"],
            description=record.get("description"),
            color=record.get("color", "#808080"),
            icon=record.get("icon", "📁"),
            created_by=record.get("created_by"),
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
            deleted_at=record.get("deleted_at"),
        )


@dataclass
class CreateCategoryDTO:
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#808080"
    icon: Optional[str] = "📁"
    created_by: Optional[int] = None


@dataclass
class UpdateCategoryDTO:
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
