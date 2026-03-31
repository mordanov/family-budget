"""Tests for BalanceRepository and BalanceService."""
import pytest
from decimal import Decimal
from datetime import datetime

from app.repositories.balance_repository import BalanceRepository
from app.services.balance_service import BalanceService
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestBalanceRepository:
    async def test_upsert_creates_new(self):
        repo = BalanceRepository()
        balance = await repo.upsert(2024, 1, Decimal("1000.00"), Decimal("500.00"))
        assert balance.year == 2024
        assert balance.month == 1
        assert balance.debit_balance == Decimal("1000.00")
        assert balance.credit_balance == Decimal("500.00")

    async def test_upsert_updates_existing(self):
        repo = BalanceRepository()
        await repo.upsert(2024, 2, Decimal("1000.00"), Decimal("200.00"))
        updated = await repo.upsert(2024, 2, Decimal("1500.00"), Decimal("300.00"))
        assert updated.debit_balance == Decimal("1500.00")
        assert updated.credit_balance == Decimal("300.00")

    async def test_get_by_month(self):
        repo = BalanceRepository()
        await repo.upsert(2024, 3, Decimal("500.00"), Decimal("100.00"))
        balance = await repo.get_by_month(2024, 3)
        assert balance is not None
        assert balance.year == 2024
        assert balance.month == 3

    async def test_get_by_month_not_found(self):
        repo = BalanceRepository()
        balance = await repo.get_by_month(1990, 1)
        assert balance is None

    async def test_get_all(self):
        repo = BalanceRepository()
        await repo.upsert(2024, 1, Decimal("100.00"), Decimal("0.00"))
        await repo.upsert(2024, 2, Decimal("200.00"), Decimal("0.00"))
        all_balances = await repo.get_all()
        assert len(all_balances) >= 2

    async def test_get_history(self):
        repo = BalanceRepository()
        for m in range(1, 7):
            await repo.upsert(2024, m, Decimal("100.00") * m, Decimal("0.00"))
        history = await repo.get_history(months=3)
        assert len(history) == 3

    async def test_net_balance_property(self):
        repo = BalanceRepository()
        balance = await repo.upsert(2024, 5, Decimal("1000.00"), Decimal("300.00"))
        assert balance.net_balance == Decimal("700.00")

    async def test_period_label(self):
        repo = BalanceRepository()
        balance = await repo.upsert(2024, 6, Decimal("0.00"), Decimal("0.00"))
        assert "2024" in balance.period_label
        assert "June" in balance.period_label


@pytest.mark.asyncio
class TestBalanceService:
    async def test_set_manual_balance(self):
        svc = BalanceService()
        balance = await svc.set_manual(2024, 4, Decimal("2000.00"), Decimal("500.00"))
        assert balance.is_manual is True
        assert balance.debit_balance == Decimal("2000.00")

    async def test_invalid_month(self):
        svc = BalanceService()
        with pytest.raises(ValidationError):
            await svc.set_manual(2024, 13, Decimal("100.00"), Decimal("0.00"))

    async def test_invalid_year(self):
        svc = BalanceService()
        with pytest.raises(ValidationError):
            await svc.set_manual(1999, 1, Decimal("100.00"), Decimal("0.00"))

    async def test_negative_debit_rejected(self):
        svc = BalanceService()
        with pytest.raises(ValidationError):
            await svc.set_manual(2024, 1, Decimal("-100.00"), Decimal("0.00"))

    async def test_get_or_create_returns_existing(self):
        svc = BalanceService()
        await svc.set_manual(2024, 7, Decimal("1000.00"), Decimal("200.00"))
        balance = await svc.get_or_create(2024, 7)
        assert balance.debit_balance == Decimal("1000.00")

    async def test_get_history_sorted(self):
        svc = BalanceService()
        for m in [1, 2, 3]:
            await svc.set_manual(2024, m, Decimal("100.00"), Decimal("0.00"))
        history = await svc.get_history(months=3)
        # Should be sorted descending
        assert history[0].month >= history[-1].month
