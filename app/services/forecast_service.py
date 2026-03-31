from decimal import Decimal
from datetime import datetime

from app.repositories.balance_repository import RecurringRuleRepository
from app.repositories.operation_repository import OperationRepository
from app.models.enums import OperationType
from app.models.operation import OperationFilter
from app.utils.logger import get_logger

logger = get_logger("service.forecast")


class ForecastService:
    def __init__(self):
        self.rule_repo = RecurringRuleRepository()
        self.op_repo = OperationRepository()

    async def get_next_month_forecast(self, base_year: int, base_month: int) -> dict:
        next_year, next_month = base_year, base_month + 1
        if next_month > 12:
            next_year += 1
            next_month = 1

        rules = await self.rule_repo.get_all_active()

        forecast_income = Decimal("0")
        forecast_expense = Decimal("0")
        items = []

        for rule in rules:
            if rule.end_date:
                target = datetime(next_year, next_month, 1)
                if rule.end_date < target:
                    continue

            if rule.operation_type == "income":
                forecast_income += rule.amount
            else:
                forecast_expense += rule.amount

            items.append({
                "name": rule.name,
                "amount": float(rule.amount),
                "operation_type": rule.operation_type,
                "payment_type": rule.payment_type,
                "category_id": rule.category_id,
                "frequency": rule.frequency,
            })

        return {
            "year": next_year,
            "month": next_month,
            "forecast_income": float(forecast_income),
            "forecast_expense": float(forecast_expense),
            "forecast_net": float(forecast_income - forecast_expense),
            "items": items,
        }

    async def get_all_rules(self) -> list:
        return await self.rule_repo.get_all_active()
