"""Tests for BalanceService (mock-based, no database required)."""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock

from app.services.balance_service import BalanceService
from app.models.balance import MonthlyBalance
from app.utils.validators import ValidationError


def _make_balance(year=2024, month=1, debit=Decimal("1000.00"), credit=Decimal("0.00"), is_manual=False, id=1):
    return MonthlyBalance(
        id=id,
        year=year,
        month=month,
        debit_balance=debit,
        credit_balance=credit,
        is_manual=is_manual,
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
class TestBalanceService:
    def _make_svc(self):
        svc = BalanceService()
        svc.balance_repo = AsyncMock()
        svc.op_repo = AsyncMock()
        return svc

    async def test_set_manual_balance(self):
        svc = self._make_svc()
        expected = _make_balance(year=2024, month=4, debit=Decimal("2000.00"), credit=Decimal("500.00"), is_manual=True)
        svc.balance_repo.upsert.return_value = expected

        balance = await svc.set_manual(2024, 4, Decimal("2000.00"), Decimal("500.00"))

        assert balance.is_manual is True
        assert balance.debit_balance == Decimal("2000.00")
        svc.balance_repo.upsert.assert_awaited_once()

    async def test_invalid_month(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.set_manual(2024, 13, Decimal("100.00"), Decimal("0.00"))
        svc.balance_repo.upsert.assert_not_awaited()

    async def test_invalid_year(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.set_manual(1999, 1, Decimal("100.00"), Decimal("0.00"))
        svc.balance_repo.upsert.assert_not_awaited()

    async def test_negative_debit_rejected(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.set_manual(2024, 1, Decimal("-100.00"), Decimal("0.00"))
        svc.balance_repo.upsert.assert_not_awaited()

    async def test_negative_credit_rejected(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.set_manual(2024, 1, Decimal("100.00"), Decimal("-50.00"))
        svc.balance_repo.upsert.assert_not_awaited()

    async def test_get_or_create_returns_existing(self):
        existing = _make_balance(year=2024, month=7, debit=Decimal("1000.00"), credit=Decimal("200.00"))
        svc = self._make_svc()
        svc.balance_repo.get_by_month.return_value = existing

        balance = await svc.get_or_create(2024, 7)

        assert balance.debit_balance == Decimal("1000.00")
        svc.balance_repo.get_by_month.assert_awaited_once_with(2024, 7)
        svc.balance_repo.upsert.assert_not_awaited()

    async def test_get_or_create_computes_when_missing(self):
        svc = self._make_svc()
        svc.balance_repo.get_by_month.return_value = None  # not found
        svc.op_repo.get_sum_by_type.return_value = {}
        computed = _make_balance(year=2024, month=8, debit=Decimal("0.00"), credit=Decimal("0.00"), is_manual=False)
        svc.balance_repo.upsert.return_value = computed

        balance = await svc.get_or_create(2024, 8)

        assert balance.is_manual is False
        svc.balance_repo.upsert.assert_awaited_once()

    async def test_get_history_sorted(self):
        svc = self._make_svc()
        history = [
            _make_balance(year=2024, month=3, debit=Decimal("300.00"), id=3),
            _make_balance(year=2024, month=2, debit=Decimal("200.00"), id=2),
            _make_balance(year=2024, month=1, debit=Decimal("100.00"), id=1),
        ]
        svc.balance_repo.get_history.return_value = history

        result = await svc.get_history(months=3)

        assert result[0].month >= result[-1].month
        svc.balance_repo.get_history.assert_awaited_once_with(3)

    async def test_net_balance_property(self):
        balance = _make_balance(debit=Decimal("1000.00"), credit=Decimal("300.00"))
        assert balance.net_balance == Decimal("700.00")

    async def test_period_label(self):
        balance = _make_balance(year=2024, month=6)
        assert "2024" in balance.period_label
        assert "June" in balance.period_label
