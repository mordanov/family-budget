from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from app.models.enums import OperationType, PaymentType, Currency


@dataclass
class Operation:
    id: int
    amount: Decimal
    currency: Currency
    operation_type: OperationType
    payment_type: PaymentType
    category_id: int
    user_id: int
    operation_date: datetime
    description: Optional[str] = None
    recurring_rule_id: Optional[int] = None
    forecast_end_date: Optional[date] = None
    is_recurring: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Joined fields (populated from queries)
    category_name: Optional[str] = None
    user_name: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": float(self.amount),
            "currency": self.currency.value,
            "operation_type": self.operation_type.value,
            "payment_type": self.payment_type.value,
            "category_id": self.category_id,
            "user_id": self.user_id,
            "operation_date": self.operation_date.isoformat() if self.operation_date else None,
            "description": self.description,
            "recurring_rule_id": self.recurring_rule_id,
            "forecast_end_date": self.forecast_end_date.isoformat() if self.forecast_end_date else None,
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "category_name": self.category_name,
            "user_name": self.user_name,
        }

    @classmethod
    def from_record(cls, record: dict) -> "Operation":
        return cls(
            id=record["id"],
            amount=Decimal(str(record["amount"])),
            currency=Currency(record["currency"]),
            operation_type=OperationType(record["operation_type"]),
            payment_type=PaymentType(record["payment_type"]),
            category_id=record["category_id"],
            user_id=record["user_id"],
            operation_date=record["operation_date"],
            description=record.get("description"),
            recurring_rule_id=record.get("recurring_rule_id"),
            forecast_end_date=record.get("forecast_end_date"),
            is_recurring=record.get("is_recurring", False),
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
            deleted_at=record.get("deleted_at"),
            category_name=record.get("category_name"),
            user_name=record.get("user_name"),
        )


@dataclass
class CreateOperationDTO:
    amount: Decimal
    currency: Currency
    operation_type: OperationType
    payment_type: PaymentType
    category_id: int
    user_id: int
    operation_date: datetime
    description: Optional[str] = None
    recurring_rule_id: Optional[int] = None
    forecast_end_date: Optional[date] = None
    is_recurring: bool = False


@dataclass
class UpdateOperationDTO:
    amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    operation_type: Optional[OperationType] = None
    payment_type: Optional[PaymentType] = None
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    operation_date: Optional[datetime] = None
    description: Optional[str] = None
    recurring_rule_id: Optional[int] = None
    forecast_end_date: Optional[date] = None
    is_recurring: Optional[bool] = None


@dataclass
class OperationFilter:
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    operation_type: Optional[OperationType] = None
    payment_type: Optional[PaymentType] = None
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    currency: Optional[Currency] = None
    is_recurring: Optional[bool] = None
    search: Optional[str] = None
