"""Tests for ForecastService (mock-based, no database required)."""
import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import AsyncMock

from app.services.forecast_service import ForecastService
from app.models.balance import RecurringRule


def _make_rule(
    id=1,
    name="Rent",
    amount=Decimal("800.00"),
    op_type="expense",
    pay_type="debit_card",
    end_date=None,
):
    return RecurringRule(
        id=id,
        name=name,
        amount=amount,
        currency="USD",
        operation_type=op_type,
        payment_type=pay_type,
        category_id=1,
        user_id=1,
        frequency="monthly",
        end_date=end_date,
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
class TestForecastService:
    def _make_svc(self):
        svc = ForecastService()
        svc.rule_repo = AsyncMock()
        svc.op_repo = AsyncMock()
        return svc

    async def test_forecast_with_expense_rule(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = [_make_rule()]

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_expense"] == 800.0
        assert result["forecast_income"] == 0.0
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Rent"

    async def test_forecast_with_income_rule(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = [
            _make_rule(name="Salary", amount=Decimal("3000.00"), op_type="income", pay_type="debit_card"),
        ]

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_income"] == 3000.0
        assert result["forecast_expense"] == 0.0
        assert result["forecast_net"] == 3000.0

    async def test_forecast_mixed_rules(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = [
            _make_rule(name="Salary", amount=Decimal("3000.00"), op_type="income", pay_type="debit_card"),
            _make_rule(name="Rent", amount=Decimal("800.00"), op_type="expense"),
            _make_rule(name="Netflix", amount=Decimal("15.00"), op_type="expense", pay_type="credit_card"),
        ]

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_income"] == 3000.0
        assert result["forecast_expense"] == 815.0
        assert result["forecast_net"] == 2185.0
        assert len(result["items"]) == 3

    async def test_forecast_skips_expired_rule(self):
        svc = self._make_svc()
        # Rule ended in the past (before next month)
        past = datetime(2024, 1, 1)
        svc.rule_repo.get_all_active.return_value = [
            _make_rule(name="Old Sub", amount=Decimal("9.99"), end_date=past),
        ]

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_expense"] == 0.0
        assert len(result["items"]) == 0

    async def test_forecast_includes_future_end_date(self):
        svc = self._make_svc()
        # Rule ends in the far future — should be included
        future = datetime(2099, 12, 31)
        svc.rule_repo.get_all_active.return_value = [
            _make_rule(name="Subscription", amount=Decimal("20.00"), end_date=future),
        ]

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_expense"] == 20.0

    async def test_forecast_no_rules(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = []

        result = await svc.get_next_month_forecast(2024, 3)

        assert result["forecast_expense"] == 0.0
        assert result["forecast_income"] == 0.0
        assert result["items"] == []

    async def test_year_rollover_december(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = []

        result = await svc.get_next_month_forecast(2024, 12)

        assert result["year"] == 2025
        assert result["month"] == 1

    async def test_normal_month_increment(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = []

        result = await svc.get_next_month_forecast(2024, 6)

        assert result["year"] == 2024
        assert result["month"] == 7

    async def test_items_contain_required_keys(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = [_make_rule()]

        result = await svc.get_next_month_forecast(2024, 3)

        item = result["items"][0]
        for key in ("name", "amount", "operation_type", "payment_type", "category_id", "frequency"):
            assert key in item

    async def test_get_all_rules(self):
        svc = self._make_svc()
        svc.rule_repo.get_all_active.return_value = [_make_rule(), _make_rule(id=2, name="Gym")]

        rules = await svc.get_all_rules()

        assert len(rules) == 2
        svc.rule_repo.get_all_active.assert_awaited_once()
