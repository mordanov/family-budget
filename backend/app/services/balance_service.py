from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.monthly_balance_repository import MonthlyBalanceRepository
from app.repositories.operation_repository import OperationRepository
from app.schemas.report import MonthlyBalanceResponse, MonthlyBalanceUpdate
from datetime import datetime, timezone


class BalanceService:
    def __init__(self, db: AsyncSession):
        self.balance_repo = MonthlyBalanceRepository(db)
        self.op_repo = OperationRepository(db)

    async def recalculate_month(self, year: int, month: int) -> None:
        from datetime import date
        import calendar

        last_day = calendar.monthrange(year, month)[1]
        date_from = datetime(year, month, 1, tzinfo=timezone.utc)
        date_to = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

        totals = await self.op_repo.get_totals_by_period(date_from, date_to)
        balance = await self.balance_repo.get_or_create(year, month)

        # Get previous month closing balance as opening
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_balance = await self.balance_repo.get_by_year_month(prev_year, prev_month)

        opening = Decimal("0")
        if balance.is_manually_adjusted and balance.manual_opening_balance is not None:
            opening = balance.manual_opening_balance
        elif prev_balance:
            opening = prev_balance.closing_balance

        balance.total_income = totals.get("income", Decimal("0"))
        balance.total_expense = totals.get("expense", Decimal("0"))
        balance.opening_balance = opening
        balance.closing_balance = opening + balance.total_income - balance.total_expense
        await self.balance_repo.db.flush()

    async def get_all(self) -> list:
        balances = await self.balance_repo.get_all_ordered()
        return [MonthlyBalanceResponse.model_validate(b) for b in balances]

    async def get_month(self, year: int, month: int) -> MonthlyBalanceResponse:
        balance = await self.balance_repo.get_or_create(year, month)
        return MonthlyBalanceResponse.model_validate(balance)

    async def set_manual_opening(
        self, year: int, month: int, data: MonthlyBalanceUpdate
    ) -> MonthlyBalanceResponse:
        balance = await self.balance_repo.get_or_create(year, month)
        balance.is_manually_adjusted = True
        balance.manual_opening_balance = data.manual_opening_balance
        await self.balance_repo.db.flush()
        await self.recalculate_month(year, month)
        await self.balance_repo.db.refresh(balance)
        return MonthlyBalanceResponse.model_validate(balance)
