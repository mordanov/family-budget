from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: str
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
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_record(cls, record: dict) -> "User":
        return cls(
            id=record["id"],
            name=record["name"],
            email=record["email"],
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
            deleted_at=record.get("deleted_at"),
        )


@dataclass
class CreateUserDTO:
    name: str
    email: str


@dataclass
class UpdateUserDTO:
    name: Optional[str] = None
    email: Optional[str] = None
