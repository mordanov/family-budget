"""Tests for ReportService."""
import pytest
from decimal import Decimal
from datetime import datetime

from app.services.report_service import ReportService
from app.services.operation_service import OperationService
from app.models.enums import OperationType, PaymentType, Currency


@pytest.mark.asyncio
class TestReportService:
    async def _seed_operations(self, sample_user, sample_category):
        svc = OperationService()
        now = datetime.now()

        # 3 expenses
        for i, (amount, pay_type) in enumerate([
            ("100.00", PaymentType.CASH),
            ("200.00", PaymentType.DEBIT_CARD),
            ("50.00", PaymentType.CREDIT_CARD),
        ]):
            await svc.create(
                amount=Decimal(amount),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=pay_type,
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=now,
                description=f"Expense {i}",
            )

        # 1 income
        await svc.create(
            amount=Decimal("1000.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )

    async def test_income_vs_expense(self, sample_user, sample_category):
        await self._seed_operations(sample_user, sample_category)

        svc = ReportService()
        result = await svc.income_vs_expense()
        assert result["income"] == 1000.0
        assert result["expense"] == 350.0
        assert result["net"] == 650.0
        assert result["savings_rate"] == pytest.approx(65.0, rel=0.01)

    async def test_by_category(self, sample_user, sample_category):
        await self._seed_operations(sample_user, sample_category)

        svc = ReportService()
        result = await svc.by_category()
        assert len(result) > 0
        total_expense = sum(
            float(r["total"]) for r in result
            if r["operation_type"] == "expense"
        )
        assert total_expense == 350.0

    async def test_by_user(self, sample_users, sample_category):
        op_svc = OperationService()
        now = datetime.now()

        for user in sample_users:
            await op_svc.create(
                amount=Decimal("200.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category["id"],
                user_id=user["id"],
                operation_date=now,
            )

        svc = ReportService()
        result = await svc.by_user()
        assert len(result) == 2
        names = [r["user_name"] for r in result]
        assert "Alice" in names
        assert "Bob" in names

    async def test_by_payment_type(self, sample_user, sample_category):
        await self._seed_operations(sample_user, sample_category)

        svc = ReportService()
        result = await svc.by_payment_type()
        payment_types = {r["payment_type"] for r in result}
        assert "cash" in payment_types
        assert "debit_card" in payment_types

    async def test_by_month(self, sample_user, sample_category):
        op_svc = OperationService()
        now = datetime.now()
        await op_svc.create(
            amount=Decimal("500.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )

        svc = ReportService()
        result = await svc.by_month(year=now.year)
        assert len(result) > 0
        assert any(r["year"] == now.year and r["month"] == now.month for r in result)

    async def test_savings_rate_zero_income(self):
        svc = ReportService()
        # When no operations, income=0
        result = await svc.income_vs_expense()
        assert result["savings_rate"] == 0

    async def test_date_range_filter(self, sample_user, sample_category):
        op_svc = OperationService()
        from datetime import timedelta

        # Old operation
        old_date = datetime.now() - timedelta(days=60)
        await op_svc.create(
            amount=Decimal("100.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=old_date,
        )

        # Recent operation
        now = datetime.now()
        await op_svc.create(
            amount=Decimal("200.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )

        svc = ReportService()
        from datetime import timedelta

        # Only recent
        result = await svc.income_vs_expense(
            date_from=now - timedelta(days=1),
            date_to=now + timedelta(days=1),
        )
        assert result["expense"] == 200.0

    async def test_forecast_next_month(self, sample_user, sample_category, db_pool):
        # Create a recurring rule
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO recurring_rules
                    (name, amount, currency, operation_type, payment_type, category_id, user_id, frequency)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
                "Monthly Rent", Decimal("800.00"), "USD", "expense",
                "debit_card", sample_category["id"], sample_user["id"], "monthly"
            )

        svc = ReportService()
        now = datetime.now()
        forecast = await svc.forecast_next_month(now.year, now.month)

        assert "forecast_expense" in forecast
        assert forecast["forecast_expense"] >= 800.0
