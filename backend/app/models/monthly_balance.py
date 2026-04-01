from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, Numeric, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class MonthlyBalance(Base):
    __tablename__ = "monthly_balances"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_monthly_balance_year_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Calculated totals
    total_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_expense: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    # Manual override flag
    is_manually_adjusted: Mapped[bool] = mapped_column(default=False, nullable=False)
    manual_opening_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
