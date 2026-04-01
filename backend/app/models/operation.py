from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, DateTime, Text, Numeric,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class OperationType(str, enum.Enum):
    income = "income"
    expense = "expense"


class PaymentType(str, enum.Enum):
    cash = "cash"
    card = "card"
    bank_transfer = "bank_transfer"
    other = "other"


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    type: Mapped[OperationType] = mapped_column(
        SAEnum(OperationType, name="operation_type"), nullable=False, index=True
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        SAEnum(PaymentType, name="payment_type"), nullable=False, default=PaymentType.card
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recurring
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    operation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    payment_method_id: Mapped[int] = mapped_column(ForeignKey("payment_methods.id"), nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="operations")
    category: Mapped["Category"] = relationship("Category", back_populates="operations")
    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", back_populates="operations")
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="operation", cascade="all, delete-orphan"
    )
