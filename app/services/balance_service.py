from typing import Optional
from decimal import Decimal
from datetime import datetime
import calendar

from app.repositories.balance_repository import BalanceRepository
from app.repositories.operation_repository import OperationRepository
from app.models.balance import MonthlyBalance
from app.models.operation import OperationFilter
from app.utils.validators import validate_year_month, ValidationError
from app.utils.logger import get_logger

logger = get_logger("service.balance")


class BalanceService:
    def __init__(self):
        self.balance_repo = BalanceRepository()
        self.op_repo = OperationRepository()

    async def get_or_create(self, year: int, month: int) -> MonthlyBalance:
        validate_year_month(year, month)
        balance = await self.balance_repo.get_by_month(year, month)
        if balance:
            return balance
        return await self._compute_and_store(year, month)

    async def get_all(self) -> list[MonthlyBalance]:
        return await self.balance_repo.get_all()

    async def get_history(self, months: int = 12) -> list[MonthlyBalance]:
        return await self.balance_repo.get_history(months)

    async def set_manual(
        self,
        year: int,
        month: int,
        debit_balance: Decimal,
        credit_balance: Decimal,
    ) -> MonthlyBalance:
        validate_year_month(year, month)
        if debit_balance < 0:
            raise ValidationError("debit_balance", "Cannot be negative")
        if credit_balance < 0:
            raise ValidationError("credit_balance", "Cannot be negative")

        balance = await self.balance_repo.upsert(
            year, month, debit_balance, credit_balance, is_manual=True
        )
        logger.info(f"Manually set balance for {year}-{month:02d}")
        return balance

    async def _compute_and_store(self, year: int, month: int) -> MonthlyBalance:
        """Compute opening balance from previous month's closing balance + operations."""
        prev_year, prev_month = self._prev_month(year, month)
        prev_balance = await self.balance_repo.get_by_month(prev_year, prev_month)

        prev_debit = prev_balance.debit_balance if prev_balance else Decimal("0")
        prev_credit = prev_balance.credit_balance if prev_balance else Decimal("0")

        # Apply previous month operations to get closing balance
        start = datetime(prev_year, prev_month, 1)
        last_day = calendar.monthrange(prev_year, prev_month)[1]
        end = datetime(prev_year, prev_month, last_day, 23, 59, 59)

        f = OperationFilter(date_from=start, date_to=end)
        sums = await self.op_repo.get_sum_by_type(f)

        income = sums.get("income", Decimal("0"))
        expense = sums.get("expense", Decimal("0"))

        new_debit = prev_debit + income - expense
        new_credit = prev_credit  # credit balance propagates unless manually adjusted

        balance = await self.balance_repo.upsert(
            year, month, new_debit, new_credit,
            is_manual=False,
            previous_month_id=prev_balance.id if prev_balance else None,
        )
        return balance

    async def recalculate_from(self, year: int, month: int, months_ahead: int = 3) -> None:
        """Recalculate balances starting from a given month."""
        y, m = year, month
        for _ in range(months_ahead):
            await self._compute_and_store(y, m)
            y, m = self._next_month(y, m)

    @staticmethod
    def _prev_month(year: int, month: int) -> tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def _next_month(year: int, month: int) -> tuple[int, int]:
        if month == 12:
            return year + 1, 1
        return year, month + 1
