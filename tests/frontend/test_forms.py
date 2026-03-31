"""Frontend unit tests — form helpers and chart builders."""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.utils.formatters import (
    operation_type_badge,
    payment_type_label,
    format_currency,
    format_month_year,
    month_name,
)
from app.ui.components.charts import (
    _empty_figure,
    income_expense_bar,
    category_pie,
    balance_trend,
)
from app.models.enums import OperationType, PaymentType


class TestCharts:
    def test_empty_figure_returns_fig(self):
        fig = _empty_figure("No data")
        assert fig is not None
        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].text == "No data"

    def test_income_expense_bar_empty(self):
        fig = income_expense_bar([])
        assert fig is not None

    def test_income_expense_bar_with_data(self):
        data = [
            {"year": 2024, "month": 1, "operation_type": "income", "total": 1000},
            {"year": 2024, "month": 1, "operation_type": "expense", "total": 600},
            {"year": 2024, "month": 2, "operation_type": "income", "total": 1200},
        ]
        fig = income_expense_bar(data)
        assert len(fig.data) == 2
        assert fig.data[0].name == "Income"
        assert fig.data[1].name == "Expense"

    def test_category_pie_empty(self):
        fig = category_pie([], "expense")
        assert fig is not None

    def test_category_pie_with_data(self):
        data = [
            {"category_name": "Food", "operation_type": "expense", "total": 300},
            {"category_name": "Transport", "operation_type": "expense", "total": 150},
        ]
        fig = category_pie(data, "expense")
        assert len(fig.data) == 1
        assert len(fig.data[0].labels) == 2

    def test_category_pie_filters_by_type(self):
        data = [
            {"category_name": "Food", "operation_type": "expense", "total": 300},
            {"category_name": "Salary", "operation_type": "income", "total": 1000},
        ]
        expense_fig = category_pie(data, "expense")
        assert len(expense_fig.data[0].labels) == 1
        assert expense_fig.data[0].labels[0] == "Food"

    def test_balance_trend_empty(self):
        fig = balance_trend([])
        assert fig is not None

    def test_balance_trend_with_data(self):
        data = [
            {"year": 2024, "month": 1, "debit_balance": 1000, "credit_balance": 200},
            {"year": 2024, "month": 2, "debit_balance": 1100, "credit_balance": 200},
        ]
        fig = balance_trend(data)
        assert len(fig.data) == 2
        assert "Debit" in fig.data[0].name


class TestFormatters:
    def test_operation_type_badge_expense(self):
        badge = operation_type_badge("expense")
        assert "Expense" in badge
        assert "🔴" in badge

    def test_operation_type_badge_income(self):
        badge = operation_type_badge("income")
        assert "Income" in badge
        assert "🟢" in badge

    def test_payment_type_label_cash(self):
        label = payment_type_label("cash")
        assert "Cash" in label

    def test_payment_type_label_debit(self):
        label = payment_type_label("debit_card")
        assert "Debit" in label

    def test_payment_type_label_unknown(self):
        result = payment_type_label("unknown_type")
        assert result == "unknown_type"

    def test_format_month_year(self):
        result = format_month_year(2024, 6)
        assert "2024" in result
        assert "June" in result

    def test_month_name(self):
        assert month_name(1) == "Jan"
        assert month_name(12) == "Dec"

    def test_format_currency_zero(self):
        assert format_currency(0.0, "USD") == "$0.00"

    def test_format_currency_large_number(self):
        result = format_currency(1_000_000.0, "USD")
        assert "1,000,000.00" in result


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

    def test_operation_type_str(self):
        # str enum should work with string comparison
        assert OperationType.EXPENSE == "expense"

    def test_payment_from_string(self):
        p = PaymentType("cash")
        assert p == PaymentType.CASH
