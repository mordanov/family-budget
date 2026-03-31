"""Tests for ReportService (mock-based, no database required)."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from app.services.report_service import ReportService
from app.models.operation import Operation
from app.models.enums import OperationType, PaymentType, Currency


def _make_op(amount=Decimal("100.00"), op_type=OperationType.EXPENSE, pay_type=PaymentType.CASH, category_name="Food"):
    return Operation(
        id=1,
        amount=amount,
        currency=Currency.USD,
        operation_type=op_type,
        payment_type=pay_type,
        category_id=1,
        user_id=1,
        operation_date=datetime.now(),
        created_at=datetime.now(),
        category_name=category_name,
        user_name="Test User",
        forecast_end_date=None,
        is_recurring=False,
    )


@pytest.mark.asyncio
class TestReportService:
    def _make_svc(self):
        svc = ReportService()
        svc.op_repo = AsyncMock()
        return svc

    async def test_income_vs_expense(self):
        svc = self._make_svc()
        svc.op_repo.get_sum_by_type.return_value = {
            "income": Decimal("1000.00"),
            "expense": Decimal("350.00"),
        }

        result = await svc.income_vs_expense()

        assert result["income"] == 1000.0
        assert result["expense"] == 350.0
        assert result["net"] == 650.0
        assert result["savings_rate"] == pytest.approx(65.0, rel=0.01)

    async def test_by_category(self):
        svc = self._make_svc()
        now = datetime.now()
        svc.op_repo.get_sum_by_category.return_value = [
            {"category_name": "Food", "operation_type": "expense", "total": Decimal("350.00")},
            {"category_name": "Food", "operation_type": "income", "total": Decimal("1000.00")},
        ]

        result = await svc.by_category()

        assert len(result) > 0
        total_expense = sum(float(r["total"]) for r in result if r["operation_type"] == "expense")
        assert total_expense == 350.0

    async def test_by_user(self):
        svc = self._make_svc()
        svc.op_repo.get_sum_by_user.return_value = [
            {"user_name": "Alice", "total": Decimal("200.00")},
            {"user_name": "Bob", "total": Decimal("200.00")},
        ]

        result = await svc.by_user()

        assert len(result) == 2
        names = [r["user_name"] for r in result]
        assert "Alice" in names
        assert "Bob" in names

    async def test_by_payment_type(self):
        svc = self._make_svc()
        svc.op_repo.get_sum_by_payment_type.return_value = [
            {"payment_type": "cash", "total": Decimal("100.00")},
            {"payment_type": "debit_card", "total": Decimal("250.00")},
        ]

        result = await svc.by_payment_type()

        payment_types = {r["payment_type"] for r in result}
        assert "cash" in payment_types
        assert "debit_card" in payment_types

    async def test_by_month(self):
        svc = self._make_svc()
        now = datetime.now()
        svc.op_repo.get_monthly_totals.return_value = [
            {"year": now.year, "month": now.month, "income": Decimal("500.00"), "expense": Decimal("0.00")},
        ]

        result = await svc.by_month(year=now.year)

        assert len(result) > 0
        assert any(r["year"] == now.year and r["month"] == now.month for r in result)

    async def test_savings_rate_zero_income(self):
        svc = self._make_svc()
        svc.op_repo.get_sum_by_type.return_value = {}

        result = await svc.income_vs_expense()

        assert result["savings_rate"] == 0

    async def test_date_range_filter(self):
        svc = self._make_svc()
        now = datetime.now()
        svc.op_repo.get_sum_by_type.return_value = {"expense": Decimal("200.00")}

        result = await svc.income_vs_expense(
            date_from=now - timedelta(days=1),
            date_to=now + timedelta(days=1),
        )

        assert result["expense"] == 200.0

    async def test_forecast_next_month(self):
        svc = self._make_svc()
        now = datetime.now()

        recurring_op = Operation(
            id=1,
            amount=Decimal("800.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=1,
            user_id=1,
            operation_date=now,
            created_at=now,
            is_recurring=True,
            forecast_end_date=None,
            category_name="Rent",
        )
        svc.op_repo.get_recurring.return_value = [recurring_op]
        # _avg_non_recurring calls get_sum_by_type once per month for 3 months
        svc.op_repo.get_sum_by_type.return_value = {}

        forecast = await svc.forecast_next_month(now.year, now.month)

        assert "forecast_expense" in forecast
        assert forecast["forecast_expense"] >= 800.0
        assert len(forecast["recurring_details"]) == 1

    async def test_forecast_skips_expired_recurring(self):
        svc = self._make_svc()
        now = datetime.now()

        from datetime import date
        expired_op = Operation(
            id=1,
            amount=Decimal("500.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=1,
            user_id=1,
            operation_date=now,
            created_at=now,
            is_recurring=True,
            forecast_end_date=date(now.year, now.month, 1),  # expires this month
            category_name="Old Sub",
        )
        svc.op_repo.get_recurring.return_value = [expired_op]
        svc.op_repo.get_sum_by_type.return_value = {}

        forecast = await svc.forecast_next_month(now.year, now.month)

        # Expired recurring should not appear in forecast
        assert forecast["forecast_expense"] == 0.0
        assert len(forecast["recurring_details"]) == 0
