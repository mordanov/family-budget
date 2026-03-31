"""Tests for model dataclasses — to_dict, from_record, and properties."""
from datetime import datetime, date
from decimal import Decimal

from app.models.user import User
from app.models.category import Category
from app.models.operation import Operation
from app.models.attachment import Attachment
from app.models.balance import MonthlyBalance, RecurringRule
from app.models.enums import (
    OperationType, PaymentType, Currency, Frequency,
    EXPENSE_PAYMENT_TYPES, INCOME_PAYMENT_TYPES,
    PAYMENT_TYPE_LABELS, OPERATION_TYPE_LABELS,
)


# ── User ──────────────────────────────────────────────────────────────────────

class TestUserModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "name": "Alice", "email": "alice@example.com",
            "created_at": now, "updated_at": None, "deleted_at": None,
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        r = self._record()
        user = User.from_record(r)
        assert user.id == 1
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.deleted_at is None

    def test_from_record_with_optional_fields(self):
        now = datetime.now()
        r = self._record(updated_at=now, deleted_at=now)
        user = User.from_record(r)
        assert user.updated_at == now
        assert user.deleted_at == now

    def test_is_active_true(self):
        user = User(id=1, name="Alice", email="a@a.com", created_at=datetime.now())
        assert user.is_active is True

    def test_is_active_false(self):
        user = User(id=1, name="Alice", email="a@a.com", created_at=datetime.now(), deleted_at=datetime.now())
        assert user.is_active is False

    def test_to_dict(self):
        now = datetime.now()
        user = User(id=1, name="Alice", email="a@a.com", created_at=now)
        d = user.to_dict()
        assert d["id"] == 1
        assert d["name"] == "Alice"
        assert d["email"] == "a@a.com"
        assert d["deleted_at"] is None
        assert "created_at" in d

    def test_to_dict_with_deleted_at(self):
        now = datetime.now()
        user = User(id=1, name="Alice", email="a@a.com", created_at=now, deleted_at=now)
        d = user.to_dict()
        assert d["deleted_at"] is not None


# ── Category ──────────────────────────────────────────────────────────────────

class TestCategoryModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "name": "Food", "description": "Daily meals",
            "color": "#ff0000", "icon": "🍽️", "created_by": None,
            "created_at": now, "updated_at": None, "deleted_at": None,
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        cat = Category.from_record(self._record())
        assert cat.id == 1
        assert cat.name == "Food"
        assert cat.color == "#ff0000"
        assert cat.icon == "🍽️"

    def test_from_record_defaults(self):
        r = self._record()
        del r["color"]
        del r["icon"]
        cat = Category.from_record(r)
        assert cat.color == "#808080"
        assert cat.icon == "📁"

    def test_is_active(self):
        cat = Category(id=1, name="Food", created_at=datetime.now())
        assert cat.is_active is True

    def test_to_dict(self):
        cat = Category(id=1, name="Food", color="#ff0000", created_at=datetime.now())
        d = cat.to_dict()
        assert d["id"] == 1
        assert d["name"] == "Food"
        assert d["color"] == "#ff0000"


# ── Operation ─────────────────────────────────────────────────────────────────

class TestOperationModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "amount": Decimal("99.50"), "currency": "USD",
            "operation_type": "expense", "payment_type": "cash",
            "category_id": 2, "user_id": 3, "operation_date": now,
            "description": "Lunch", "recurring_rule_id": None,
            "forecast_end_date": None, "is_recurring": False,
            "created_at": now, "updated_at": None, "deleted_at": None,
            "category_name": "Food", "user_name": "Alice",
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        op = Operation.from_record(self._record())
        assert op.id == 1
        assert op.amount == Decimal("99.50")
        assert op.operation_type == OperationType.EXPENSE
        assert op.payment_type == PaymentType.CASH
        assert op.currency == Currency.USD
        assert op.category_name == "Food"
        assert op.user_name == "Alice"

    def test_from_record_income(self):
        op = Operation.from_record(self._record(operation_type="income", payment_type="debit_card"))
        assert op.operation_type == OperationType.INCOME
        assert op.payment_type == PaymentType.DEBIT_CARD

    def test_from_record_recurring(self):
        today = date.today()
        op = Operation.from_record(self._record(is_recurring=True, forecast_end_date=today))
        assert op.is_recurring is True
        assert op.forecast_end_date == today

    def test_is_active(self):
        op = Operation.from_record(self._record())
        assert op.is_active is True

    def test_to_dict_contains_required_keys(self):
        op = Operation.from_record(self._record())
        d = op.to_dict()
        for key in ("id", "amount", "currency", "operation_type", "payment_type",
                    "category_id", "user_id", "is_recurring", "category_name", "user_name"):
            assert key in d

    def test_to_dict_enums_serialised_as_values(self):
        op = Operation.from_record(self._record())
        d = op.to_dict()
        assert d["operation_type"] == "expense"
        assert d["payment_type"] == "cash"
        assert d["currency"] == "USD"


# ── Attachment ────────────────────────────────────────────────────────────────

class TestAttachmentModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "operation_id": 5,
            "file_name": "receipt.pdf", "file_path": "/uploads/5/abc.pdf",
            "mime_type": "application/pdf", "file_size": 10240,
            "upload_date": now, "created_at": now, "deleted_at": None,
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        att = Attachment.from_record(self._record())
        assert att.id == 1
        assert att.file_name == "receipt.pdf"
        assert att.mime_type == "application/pdf"
        assert att.file_size == 10240

    def test_is_active(self):
        att = Attachment.from_record(self._record())
        assert att.is_active is True

    def test_is_pdf(self):
        att = Attachment.from_record(self._record(mime_type="application/pdf"))
        assert att.is_pdf is True
        assert att.is_image is False

    def test_is_image_jpeg(self):
        att = Attachment.from_record(self._record(mime_type="image/jpeg"))
        assert att.is_image is True
        assert att.is_pdf is False

    def test_is_image_png(self):
        att = Attachment.from_record(self._record(mime_type="image/png"))
        assert att.is_image is True

    def test_file_size_kb(self):
        att = Attachment.from_record(self._record(file_size=2048))
        assert att.file_size_kb == 2.0

    def test_file_size_mb(self):
        att = Attachment.from_record(self._record(file_size=1048576))
        assert att.file_size_mb == 1.0

    def test_to_dict(self):
        att = Attachment.from_record(self._record())
        d = att.to_dict()
        assert d["id"] == 1
        assert d["operation_id"] == 5
        assert d["file_name"] == "receipt.pdf"
        assert d["deleted_at"] is None


# ── MonthlyBalance ─────────────────────────────────────────────────────────────

class TestMonthlyBalanceModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "year": 2024, "month": 6,
            "debit_balance": Decimal("1500.00"), "credit_balance": Decimal("300.00"),
            "is_manual": False, "previous_month_id": None,
            "created_at": now, "updated_at": None,
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        bal = MonthlyBalance.from_record(self._record())
        assert bal.year == 2024
        assert bal.month == 6
        assert bal.debit_balance == Decimal("1500.00")
        assert bal.credit_balance == Decimal("300.00")
        assert bal.is_manual is False

    def test_net_balance(self):
        bal = MonthlyBalance.from_record(self._record())
        assert bal.net_balance == Decimal("1200.00")

    def test_period_label_june(self):
        bal = MonthlyBalance.from_record(self._record())
        assert "2024" in bal.period_label
        assert "June" in bal.period_label

    def test_period_label_january(self):
        bal = MonthlyBalance.from_record(self._record(month=1))
        assert "January" in bal.period_label

    def test_to_dict(self):
        bal = MonthlyBalance.from_record(self._record())
        d = bal.to_dict()
        assert d["year"] == 2024
        assert d["month"] == 6
        assert d["debit_balance"] == 1500.0
        assert "period_label" in d


# ── RecurringRule ──────────────────────────────────────────────────────────────

class TestRecurringRuleModel:
    def _record(self, **kwargs):
        now = datetime.now()
        base = {
            "id": 1, "name": "Rent", "amount": Decimal("800.00"),
            "currency": "USD", "operation_type": "expense",
            "payment_type": "debit_card", "category_id": 1, "user_id": 1,
            "description": "Monthly rent", "frequency": "monthly",
            "end_date": None, "created_at": now, "updated_at": None, "deleted_at": None,
        }
        base.update(kwargs)
        return base

    def test_from_record(self):
        rule = RecurringRule.from_record(self._record())
        assert rule.id == 1
        assert rule.name == "Rent"
        assert rule.amount == Decimal("800.00")
        assert rule.frequency == "monthly"
        assert rule.end_date is None

    def test_is_active_true(self):
        rule = RecurringRule.from_record(self._record())
        assert rule.is_active is True

    def test_is_active_false(self):
        now = datetime.now()
        rule = RecurringRule.from_record(self._record(deleted_at=now))
        assert rule.is_active is False

    def test_to_dict(self):
        rule = RecurringRule.from_record(self._record())
        d = rule.to_dict()
        assert d["name"] == "Rent"
        assert d["amount"] == 800.0
        assert d["frequency"] == "monthly"
        assert d["end_date"] is None


# ── Enums ──────────────────────────────────────────────────────────────────────

class TestEnums:
    def test_operation_type_values(self):
        assert OperationType.EXPENSE.value == "expense"
        assert OperationType.INCOME.value == "income"

    def test_payment_type_values(self):
        assert PaymentType.CASH.value == "cash"
        assert PaymentType.DEBIT_CARD.value == "debit_card"
        assert PaymentType.CREDIT_CARD.value == "credit_card"
        assert PaymentType.REFUND_TO_DEBIT.value == "refund_to_debit"
        assert PaymentType.REFUND_TO_CREDIT.value == "refund_to_credit"

    def test_currency_values(self):
        assert Currency.USD.value == "USD"
        assert Currency.EUR.value == "EUR"
        assert Currency.RUB.value == "RUB"
        assert Currency.GBP.value == "GBP"

    def test_frequency_values(self):
        assert Frequency.DAILY.value == "daily"
        assert Frequency.WEEKLY.value == "weekly"
        assert Frequency.MONTHLY.value == "monthly"
        assert Frequency.YEARLY.value == "yearly"

    def test_expense_payment_types(self):
        assert PaymentType.CASH in EXPENSE_PAYMENT_TYPES
        assert PaymentType.DEBIT_CARD in EXPENSE_PAYMENT_TYPES
        assert PaymentType.CREDIT_CARD in EXPENSE_PAYMENT_TYPES
        assert PaymentType.REFUND_TO_DEBIT not in EXPENSE_PAYMENT_TYPES
        assert PaymentType.REFUND_TO_CREDIT not in EXPENSE_PAYMENT_TYPES

    def test_income_payment_types(self):
        assert PaymentType.CASH in INCOME_PAYMENT_TYPES
        assert PaymentType.DEBIT_CARD in INCOME_PAYMENT_TYPES
        assert PaymentType.REFUND_TO_DEBIT in INCOME_PAYMENT_TYPES
        assert PaymentType.REFUND_TO_CREDIT in INCOME_PAYMENT_TYPES
        assert PaymentType.CREDIT_CARD not in INCOME_PAYMENT_TYPES

    def test_payment_type_labels(self):
        assert PAYMENT_TYPE_LABELS[PaymentType.CASH] == "Cash"
        assert PAYMENT_TYPE_LABELS[PaymentType.DEBIT_CARD] == "Debit Card"
        assert PAYMENT_TYPE_LABELS[PaymentType.CREDIT_CARD] == "Credit Card"
        assert PAYMENT_TYPE_LABELS[PaymentType.REFUND_TO_DEBIT] == "Refund to Debit"
        assert PAYMENT_TYPE_LABELS[PaymentType.REFUND_TO_CREDIT] == "Refund to Credit"

    def test_operation_type_labels(self):
        assert OPERATION_TYPE_LABELS[OperationType.EXPENSE] == "Expense"
        assert OPERATION_TYPE_LABELS[OperationType.INCOME] == "Income"

    def test_enum_str_behaviour(self):
        # OperationType is str, Enum so can be compared to strings
        assert OperationType.EXPENSE == "expense"
        assert PaymentType.CASH == "cash"
        assert Currency.USD == "USD"
