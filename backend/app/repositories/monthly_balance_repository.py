from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.monthly_balance import MonthlyBalance
from app.repositories.base import BaseRepository


class MonthlyBalanceRepository(BaseRepository[MonthlyBalance]):
    def __init__(self, db: AsyncSession):
        super().__init__(MonthlyBalance, db)

    async def get_by_year_month(self, year: int, month: int) -> MonthlyBalance | None:
        result = await self.db.execute(
            select(MonthlyBalance).where(
                MonthlyBalance.year == year, MonthlyBalance.month == month
            )
        )
        return result.scalar_one_or_none()

    async def get_all_ordered(self) -> list[MonthlyBalance]:
        result = await self.db.execute(
            select(MonthlyBalance).order_by(
                MonthlyBalance.year.desc(), MonthlyBalance.month.desc()
            )
        )
        return list(result.scalars().all())

    async def get_or_create(self, year: int, month: int) -> MonthlyBalance:
        existing = await self.get_by_year_month(year, month)
        if existing:
            return existing
        balance = MonthlyBalance(
            year=year,
            month=month,
            total_income=Decimal("0"),
            total_expense=Decimal("0"),
            opening_balance=Decimal("0"),
            closing_balance=Decimal("0"),
        )
        return await self.create(balance)
