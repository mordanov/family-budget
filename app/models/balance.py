from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class MonthlyBalance:
    id: int
    year: int
    month: int
    debit_balance: Decimal
    credit_balance: Decimal
    is_manual: bool = False
    previous_month_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @property
    def period_label(self) -> str:
        from datetime import date
        d = date(self.year, self.month, 1)
        return d.strftime("%B %Y")

    @property
    def net_balance(self) -> Decimal:
        return self.debit_balance - self.credit_balance

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "year": self.year,
            "month": self.month,
            "debit_balance": float(self.debit_balance),
            "credit_balance": float(self.credit_balance),
            "is_manual": self.is_manual,
            "previous_month_id": self.previous_month_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "period_label": self.period_label,
        }

    @classmethod
    def from_record(cls, record: dict) -> "MonthlyBalance":
        return cls(
            id=record["id"],
            year=record["year"],
            month=record["month"],
            debit_balance=Decimal(str(record["debit_balance"])),
            credit_balance=Decimal(str(record["credit_balance"])),
            is_manual=record.get("is_manual", False),
            previous_month_id=record.get("previous_month_id"),
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
        )


@dataclass
class RecurringRule:
    id: int
    name: str
    amount: Decimal
    currency: str
    operation_type: str
    payment_type: str
    category_id: int
    user_id: int
    description: Optional[str] = None
    frequency: str = "monthly"
    end_date: Optional[datetime] = None
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
            "amount": float(self.amount),
            "currency": self.currency,
            "operation_type": self.operation_type,
            "payment_type": self.payment_type,
            "category_id": self.category_id,
            "user_id": self.user_id,
            "description": self.description,
            "frequency": self.frequency,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_record(cls, record: dict) -> "RecurringRule":
        return cls(
            id=record["id"],
            name=record["name"],
            amount=Decimal(str(record["amount"])),
            currency=record["currency"],
            operation_type=record["operation_type"],
            payment_type=record["payment_type"],
            category_id=record["category_id"],
            user_id=record["user_id"],
            description=record.get("description"),
            frequency=record.get("frequency", "monthly"),
            end_date=record.get("end_date"),
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
            deleted_at=record.get("deleted_at"),
        )


@dataclass
class CreateRecurringRuleDTO:
    name: str
    amount: Decimal
    currency: str
    operation_type: str
    payment_type: str
    category_id: int
    user_id: int
    description: Optional[str] = None
    frequency: str = "monthly"
    end_date: Optional[datetime] = None
