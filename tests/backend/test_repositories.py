"""
Repository tests — BaseRepository fetch methods are patched so no DB is needed.
This validates query-building logic and model mapping in each repository.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.balance_repository import BalanceRepository, RecurringRuleRepository
from app.repositories.operation_repository import OperationRepository
from app.models.user import CreateUserDTO, UpdateUserDTO
from app.models.category import CreateCategoryDTO, UpdateCategoryDTO
from app.models.attachment import CreateAttachmentDTO
from app.models.balance import CreateRecurringRuleDTO
from app.models.operation import CreateOperationDTO, UpdateOperationDTO, OperationFilter
from app.models.enums import OperationType, PaymentType, Currency


# ── helpers ──────────────────────────────────────────────────────────────────

def _user_record(**kw):
    now = datetime.now()
    r = {"id": 1, "name": "Alice", "email": "alice@example.com",
         "created_at": now, "updated_at": None, "deleted_at": None}
    r.update(kw)
    return r


def _category_record(**kw):
    now = datetime.now()
    r = {"id": 1, "name": "Food", "description": None, "color": "#808080",
         "icon": "📁", "created_by": None, "created_at": now,
         "updated_at": None, "deleted_at": None}
    r.update(kw)
    return r


def _attachment_record(**kw):
    now = datetime.now()
    r = {"id": 1, "operation_id": 5, "file_name": "receipt.png",
         "file_path": "/up/5/x.png", "mime_type": "image/png",
         "file_size": 1024, "upload_date": now, "created_at": now,
         "deleted_at": None}
    r.update(kw)
    return r


def _balance_record(**kw):
    now = datetime.now()
    r = {"id": 1, "year": 2024, "month": 3,
         "debit_balance": Decimal("1000.00"), "credit_balance": Decimal("0.00"),
         "is_manual": False, "previous_month_id": None,
         "created_at": now, "updated_at": None}
    r.update(kw)
    return r


def _rule_record(**kw):
    now = datetime.now()
    r = {"id": 1, "name": "Rent", "amount": Decimal("800.00"),
         "currency": "USD", "operation_type": "expense",
         "payment_type": "debit_card", "category_id": 1, "user_id": 1,
         "description": None, "frequency": "monthly", "end_date": None,
         "created_at": now, "updated_at": None, "deleted_at": None}
    r.update(kw)
    return r


def _op_record(**kw):
    now = datetime.now()
    r = {"id": 1, "amount": Decimal("100.00"), "currency": "USD",
         "operation_type": "expense", "payment_type": "cash",
         "category_id": 1, "user_id": 1, "operation_date": now,
         "description": None, "recurring_rule_id": None,
         "forecast_end_date": None, "is_recurring": False,
         "created_at": now, "updated_at": None, "deleted_at": None,
         "category_name": "Food", "user_name": "Alice"}
    r.update(kw)
    return r


# ── UserRepository ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestUserRepository:
    async def test_get_by_id_found(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _user_record()
            user = await repo.get_by_id(1)
        assert user.id == 1
        assert user.name == "Alice"

    async def test_get_by_id_not_found(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            user = await repo.get_by_id(99)
        assert user is None

    async def test_get_by_email_found(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _user_record()
            user = await repo.get_by_email("alice@example.com")
        assert user.email == "alice@example.com"

    async def test_get_by_email_not_found(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            user = await repo.get_by_email("none@example.com")
        assert user is None

    async def test_get_all(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_user_record(id=1), _user_record(id=2, name="Bob", email="b@b.com")]
            users = await repo.get_all()
        assert len(users) == 2
        assert users[0].name == "Alice"

    async def test_create(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _user_record()
            user = await repo.create(CreateUserDTO(name="Alice", email="alice@example.com"))
        assert user.id == 1

    async def test_update_with_fields(self):
        repo = UserRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _user_record(name="Updated")
            dto = UpdateUserDTO(name="Updated")
            user = await repo.update(1, dto)
        assert user.name == "Updated"

    async def test_update_no_fields_calls_get_by_id(self):
        repo = UserRepository()
        with patch.object(repo, "get_by_id", new_callable=AsyncMock) as m:
            from app.models.user import User
            m.return_value = User(id=1, name="Alice", email="a@a.com", created_at=datetime.now())
            result = await repo.update(1, UpdateUserDTO())
        m.assert_awaited_once_with(1, conn=None)
        assert result.id == 1

    async def test_delete(self):
        repo = UserRepository()
        with patch.object(repo, "soft_delete", new_callable=AsyncMock) as m:
            m.return_value = True
            result = await repo.delete(1)
        assert result is True


# ── CategoryRepository ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCategoryRepository:
    async def test_get_by_id_found(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _category_record()
            cat = await repo.get_by_id(1)
        assert cat.id == 1
        assert cat.name == "Food"

    async def test_get_by_id_not_found(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            cat = await repo.get_by_id(99)
        assert cat is None

    async def test_get_all(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_category_record()]
            cats = await repo.get_all()
        assert len(cats) == 1

    async def test_get_by_name_found(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _category_record()
            cat = await repo.get_by_name("Food")
        assert cat.name == "Food"

    async def test_create(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _category_record()
            cat = await repo.create(CreateCategoryDTO(name="Food"))
        assert cat.name == "Food"

    async def test_update_with_fields(self):
        repo = CategoryRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _category_record(name="Updated", color="#0000ff")
            dto = UpdateCategoryDTO(name="Updated", color="#0000ff")
            cat = await repo.update(1, dto)
        assert cat.name == "Updated"

    async def test_update_no_fields(self):
        repo = CategoryRepository()
        with patch.object(repo, "get_by_id", new_callable=AsyncMock) as m:
            from app.models.category import Category
            m.return_value = Category(id=1, name="Food", created_at=datetime.now())
            result = await repo.update(1, UpdateCategoryDTO())
        m.assert_awaited_once()

    async def test_delete(self):
        repo = CategoryRepository()
        with patch.object(repo, "soft_delete", new_callable=AsyncMock) as m:
            m.return_value = True
            assert await repo.delete(1) is True


# ── AttachmentRepository ──────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAttachmentRepository:
    async def test_get_by_id_found(self):
        repo = AttachmentRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _attachment_record()
            att = await repo.get_by_id(1)
        assert att.id == 1
        assert att.file_name == "receipt.png"

    async def test_get_by_id_not_found(self):
        repo = AttachmentRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            att = await repo.get_by_id(99)
        assert att is None

    async def test_get_by_operation(self):
        repo = AttachmentRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_attachment_record()]
            atts = await repo.get_by_operation(5)
        assert len(atts) == 1

    async def test_create(self):
        repo = AttachmentRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _attachment_record()
            dto = CreateAttachmentDTO(
                operation_id=5, file_name="receipt.png",
                file_path="/up/5/x.png", mime_type="image/png", file_size=1024,
            )
            att = await repo.create(dto)
        assert att.id == 1

    async def test_delete(self):
        repo = AttachmentRepository()
        with patch.object(repo, "soft_delete", new_callable=AsyncMock) as m:
            m.return_value = True
            assert await repo.delete(1) is True

    async def test_delete_by_operation_parses_count(self):
        repo = AttachmentRepository()
        with patch.object(repo, "execute", new_callable=AsyncMock) as m:
            m.return_value = "UPDATE 3"
            count = await repo.delete_by_operation(5)
        assert count == 3

    async def test_delete_by_operation_zero(self):
        repo = AttachmentRepository()
        with patch.object(repo, "execute", new_callable=AsyncMock) as m:
            m.return_value = "UPDATE 0"
            count = await repo.delete_by_operation(5)
        assert count == 0


# ── AuditRepository ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAuditRepository:
    async def test_log(self):
        repo = AuditRepository()
        with patch.object(repo, "execute", new_callable=AsyncMock) as m:
            await repo.log("users", 1, "CREATE", new_values={"name": "Alice"}, user_id=1)
        m.assert_awaited_once()

    async def test_log_without_values(self):
        repo = AuditRepository()
        with patch.object(repo, "execute", new_callable=AsyncMock) as m:
            await repo.log("users", 1, "DELETE")
        m.assert_awaited_once()

    async def test_get_for_record(self):
        repo = AuditRepository()
        now = datetime.now()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [{"id": 1, "table_name": "users", "record_id": 1,
                               "action": "CREATE", "old_values": None,
                               "new_values": None, "user_id": None, "created_at": now}]
            results = await repo.get_for_record("users", 1)
        assert len(results) == 1
        assert results[0]["action"] == "CREATE"

    async def test_get_recent(self):
        repo = AuditRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = []
            results = await repo.get_recent(limit=10)
        assert results == []


# ── BalanceRepository ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestBalanceRepository:
    async def test_get_by_month_found(self):
        repo = BalanceRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _balance_record()
            bal = await repo.get_by_month(2024, 3)
        assert bal.year == 2024
        assert bal.month == 3

    async def test_get_by_month_not_found(self):
        repo = BalanceRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            assert await repo.get_by_month(1990, 1) is None

    async def test_get_all(self):
        repo = BalanceRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_balance_record(), _balance_record(id=2, month=4)]
            bals = await repo.get_all()
        assert len(bals) == 2

    async def test_upsert(self):
        repo = BalanceRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _balance_record(is_manual=True)
            bal = await repo.upsert(2024, 3, Decimal("1000.00"), Decimal("0.00"), is_manual=True)
        assert bal.is_manual is True

    async def test_get_history(self):
        repo = BalanceRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_balance_record(month=m) for m in range(1, 4)]
            history = await repo.get_history(months=3)
        assert len(history) == 3


# ── RecurringRuleRepository ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestRecurringRuleRepository:
    async def test_get_by_id_found(self):
        repo = RecurringRuleRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _rule_record()
            rule = await repo.get_by_id(1)
        assert rule.id == 1
        assert rule.name == "Rent"

    async def test_get_by_id_not_found(self):
        repo = RecurringRuleRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            assert await repo.get_by_id(99) is None

    async def test_get_all_active(self):
        repo = RecurringRuleRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_rule_record()]
            rules = await repo.get_all_active()
        assert len(rules) == 1
        assert rules[0].name == "Rent"

    async def test_create(self):
        repo = RecurringRuleRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _rule_record()
            dto = CreateRecurringRuleDTO(
                name="Rent", amount=Decimal("800.00"), currency="USD",
                operation_type="expense", payment_type="debit_card",
                category_id=1, user_id=1,
            )
            rule = await repo.create(dto)
        assert rule.name == "Rent"

    async def test_delete(self):
        repo = RecurringRuleRepository()
        with patch.object(repo, "soft_delete", new_callable=AsyncMock) as m:
            m.return_value = True
            assert await repo.delete(1) is True


# ── OperationRepository._build_filter (pure Python) ──────────────────────────

class TestOperationFilterBuilder:
    """Tests for _build_filter — pure Python, no DB needed."""

    def test_empty_filter(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter())
        assert "deleted_at IS NULL" in where
        assert vals == []

    def test_date_from(self):
        repo = OperationRepository()
        now = datetime.now()
        where, vals = repo._build_filter(OperationFilter(date_from=now))
        assert "operation_date >=" in where
        assert now in vals

    def test_date_to(self):
        repo = OperationRepository()
        now = datetime.now()
        where, vals = repo._build_filter(OperationFilter(date_to=now))
        assert "operation_date <=" in where

    def test_operation_type(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(operation_type=OperationType.EXPENSE))
        assert "operation_type" in where
        assert "expense" in vals

    def test_payment_type(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(payment_type=PaymentType.CASH))
        assert "payment_type" in where
        assert "cash" in vals

    def test_category_id(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(category_id=5))
        assert "category_id" in where
        assert 5 in vals

    def test_user_id(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(user_id=2))
        assert "user_id" in where
        assert 2 in vals

    def test_currency(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(currency=Currency.EUR))
        assert "currency" in where
        assert "EUR" in vals

    def test_is_recurring_true(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(is_recurring=True))
        assert "is_recurring" in where
        assert True in vals

    def test_is_recurring_false(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(is_recurring=False))
        assert "is_recurring" in where
        assert False in vals

    def test_search(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(search="lunch"))
        assert "ILIKE" in where
        assert "%lunch%" in vals

    def test_combined_filters(self):
        repo = OperationRepository()
        now = datetime.now()
        where, vals = repo._build_filter(OperationFilter(
            date_from=now,
            operation_type=OperationType.EXPENSE,
            user_id=3,
        ))
        assert "operation_date >=" in where
        assert "operation_type" in where
        assert "user_id" in where
        assert len(vals) == 3

    def test_start_idx_offset(self):
        repo = OperationRepository()
        where, vals = repo._build_filter(OperationFilter(user_id=1), start_idx=5)
        assert "$5" in where


# ── OperationRepository query methods ────────────────────────────────────────

@pytest.mark.asyncio
class TestOperationRepository:
    async def test_get_by_id_found(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = _op_record()
            op = await repo.get_by_id(1)
        assert op.id == 1
        assert op.amount == Decimal("100.00")

    async def test_get_by_id_not_found(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_one", new_callable=AsyncMock) as m:
            m.return_value = None
            assert await repo.get_by_id(99) is None

    async def test_get_many(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [_op_record()]
            ops = await repo.get_many(OperationFilter())
        assert len(ops) == 1

    async def test_count_many(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_val", new_callable=AsyncMock) as m:
            m.return_value = 5
            count = await repo.count_many(OperationFilter())
        assert count == 5

    async def test_count_many_none_returns_zero(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_val", new_callable=AsyncMock) as m:
            m.return_value = None
            count = await repo.count_many(OperationFilter())
        assert count == 0

    async def test_create(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_val", new_callable=AsyncMock) as fv, \
             patch.object(repo, "get_by_id", new_callable=AsyncMock) as gbi:
            fv.return_value = 1
            from app.models.operation import Operation
            gbi.return_value = Operation.from_record(_op_record())
            dto = CreateOperationDTO(
                amount=Decimal("100.00"), currency=Currency.USD,
                operation_type=OperationType.EXPENSE, payment_type=PaymentType.CASH,
                category_id=1, user_id=1, operation_date=datetime.now(),
            )
            op = await repo.create(dto)
        assert op.id == 1

    async def test_update_with_fields(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_val", new_callable=AsyncMock) as fv, \
             patch.object(repo, "get_by_id", new_callable=AsyncMock) as gbi:
            fv.return_value = 1
            from app.models.operation import Operation
            gbi.return_value = Operation.from_record(_op_record(amount=Decimal("200.00")))
            dto = UpdateOperationDTO(amount=Decimal("200.00"))
            op = await repo.update(1, dto)
        assert op.amount == Decimal("200.00")

    async def test_update_empty_dto_calls_get_by_id(self):
        repo = OperationRepository()
        with patch.object(repo, "get_by_id", new_callable=AsyncMock) as gbi:
            from app.models.operation import Operation
            gbi.return_value = Operation.from_record(_op_record())
            result = await repo.update(1, UpdateOperationDTO())
        gbi.assert_awaited_once_with(1, conn=None)

    async def test_delete(self):
        repo = OperationRepository()
        with patch.object(repo, "soft_delete", new_callable=AsyncMock) as m:
            m.return_value = True
            assert await repo.delete(1) is True

    async def test_get_sum_by_type(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [
                {"operation_type": "expense", "total": Decimal("350.00")},
                {"operation_type": "income", "total": Decimal("1000.00")},
            ]
            sums = await repo.get_sum_by_type(OperationFilter())
        assert sums["expense"] == Decimal("350.00")
        assert sums["income"] == Decimal("1000.00")

    async def test_get_sum_by_category(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [{"category_name": "Food", "operation_type": "expense",
                               "total": Decimal("100.00"), "count": 3}]
            result = await repo.get_sum_by_category(OperationFilter())
        assert len(result) == 1
        assert result[0]["category_name"] == "Food"

    async def test_get_sum_by_user(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [{"user_name": "Alice", "operation_type": "expense",
                               "total": Decimal("200.00"), "count": 2}]
            result = await repo.get_sum_by_user(OperationFilter())
        assert len(result) == 1

    async def test_get_sum_by_payment_type(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [{"payment_type": "cash", "operation_type": "expense",
                               "total": Decimal("50.00"), "count": 1}]
            result = await repo.get_sum_by_payment_type(OperationFilter())
        assert result[0]["payment_type"] == "cash"

    async def test_get_monthly_totals_with_year(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = [{"year": 2024, "month": 3, "operation_type": "expense",
                               "total": Decimal("300.00")}]
            result = await repo.get_monthly_totals(year=2024)
        assert result[0]["year"] == 2024

    async def test_get_monthly_totals_no_year(self):
        repo = OperationRepository()
        with patch.object(repo, "fetch_many", new_callable=AsyncMock) as m:
            m.return_value = []
            result = await repo.get_monthly_totals()
        assert result == []

    async def test_get_recurring(self):
        repo = OperationRepository()
        with patch.object(repo, "get_many", new_callable=AsyncMock) as m:
            from app.models.operation import Operation
            m.return_value = [Operation.from_record(_op_record(is_recurring=True))]
            ops = await repo.get_recurring()
        assert ops[0].is_recurring is True
