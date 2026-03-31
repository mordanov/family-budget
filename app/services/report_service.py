from typing import Optional
from decimal import Decimal
from datetime import datetime, date
import calendar

from app.repositories.operation_repository import OperationRepository
from app.models.operation import OperationFilter
from app.models.enums import OperationType
from app.utils.logger import get_logger

logger = get_logger("service.report")


class ReportService:
    def __init__(self):
        self.op_repo = OperationRepository()

    def _month_range(self, year: int, month: int) -> tuple[datetime, datetime]:
        start = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = datetime(year, month, last_day, 23, 59, 59)
        return start, end

    async def by_category(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        operation_type: Optional[OperationType] = None,
    ) -> list[dict]:
        f = OperationFilter(
            date_from=date_from,
            date_to=date_to,
            operation_type=operation_type,
        )
        rows = await self.op_repo.get_sum_by_category(f)
        return rows

    async def by_user(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        operation_type: Optional[OperationType] = None,
    ) -> list[dict]:
        f = OperationFilter(
            date_from=date_from,
            date_to=date_to,
            operation_type=operation_type,
        )
        return await self.op_repo.get_sum_by_user(f)

    async def by_payment_type(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        operation_type: Optional[OperationType] = None,
    ) -> list[dict]:
        f = OperationFilter(
            date_from=date_from,
            date_to=date_to,
            operation_type=operation_type,
        )
        return await self.op_repo.get_sum_by_payment_type(f)

    async def by_month(self, year: Optional[int] = None) -> list[dict]:
        return await self.op_repo.get_monthly_totals(year)

    async def income_vs_expense(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        f = OperationFilter(date_from=date_from, date_to=date_to)
        sums = await self.op_repo.get_sum_by_type(f)
        income = float(sums.get("income", Decimal("0")))
        expense = float(sums.get("expense", Decimal("0")))
        return {
            "income": income,
            "expense": expense,
            "net": income - expense,
            "savings_rate": (income - expense) / income * 100 if income > 0 else 0,
        }

    async def forecast_next_month(
        self, base_year: int, base_month: int
    ) -> dict:
        """Forecast next month based on recurring operations and previous month trends."""
        next_year, next_month = base_year, base_month + 1
        if next_month > 12:
            next_year += 1
            next_month = 1

        # Get recurring operations
        recurring = await self.op_repo.get_recurring()

        forecast_income = Decimal("0")
        forecast_expense = Decimal("0")
        details = []

        for op in recurring:
            # Check if forecast_end_date has passed
            if op.forecast_end_date:
                end = datetime.combine(op.forecast_end_date, datetime.min.time())
                target = datetime(next_year, next_month, 1)
                if end < target:
                    continue

            if op.operation_type == OperationType.INCOME:
                forecast_income += op.amount
            else:
                forecast_expense += op.amount

            details.append({
                "id": op.id,
                "description": op.description or "Recurring",
                "amount": float(op.amount),
                "operation_type": op.operation_type.value,
                "payment_type": op.payment_type.value,
                "category_name": op.category_name,
            })

        # Also factor in average from last 3 months of non-recurring
        avg_income, avg_expense = await self._avg_non_recurring(base_year, base_month, months=3)
        forecast_income += avg_income
        forecast_expense += avg_expense

        return {
            "year": next_year,
            "month": next_month,
            "forecast_income": float(forecast_income),
            "forecast_expense": float(forecast_expense),
            "forecast_net": float(forecast_income - forecast_expense),
            "recurring_details": details,
            "avg_income_base": float(avg_income),
            "avg_expense_base": float(avg_expense),
        }

    async def _avg_non_recurring(
        self, base_year: int, base_month: int, months: int = 3
    ) -> tuple[Decimal, Decimal]:
        total_income = Decimal("0")
        total_expense = Decimal("0")
        count = 0

        y, m = base_year, base_month
        for _ in range(months):
            start, end = self._month_range(y, m)
            f = OperationFilter(date_from=start, date_to=end, is_recurring=False)
            sums = await self.op_repo.get_sum_by_type(f)
            total_income += sums.get("income", Decimal("0"))
            total_expense += sums.get("expense", Decimal("0"))
            count += 1
            if m == 1:
                y -= 1
                m = 12
            else:
                m -= 1

        if count == 0:
            return Decimal("0"), Decimal("0")
        return total_income / count, total_expense / count
