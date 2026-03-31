"""Frontend test configuration.

These tests use unittest.mock to patch Streamlit components and
verify that page modules behave correctly without launching a browser.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from app.models.user import User
from app.models.category import Category
from app.models.operation import Operation
from app.models.enums import OperationType, PaymentType, Currency
from app.models.balance import MonthlyBalance


@pytest.fixture
def mock_users() -> list[User]:
    return [
        User(id=1, name="Alice", email="alice@test.com", created_at=datetime.now()),
        User(id=2, name="Bob", email="bob@test.com", created_at=datetime.now()),
    ]


@pytest.fixture
def mock_categories() -> list[Category]:
    return [
        Category(id=1, name="Food", icon="🍔", color="#2ecc71", created_at=datetime.now()),
        Category(id=2, name="Transport", icon="🚗", color="#e67e22", created_at=datetime.now()),
    ]


@pytest.fixture
def mock_operations(mock_users, mock_categories) -> list[Operation]:
    return [
        Operation(
            id=1,
            amount=Decimal("150.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=1,
            user_id=1,
            operation_date=datetime.now(),
            description="Test expense",
            category_name="Food",
            user_name="Alice",
            created_at=datetime.now(),
        ),
    ]


@pytest.fixture
def mock_balance() -> MonthlyBalance:
    return MonthlyBalance(
        id=1,
        year=2024,
        month=6,
        debit_balance=Decimal("5000.00"),
        credit_balance=Decimal("1000.00"),
        created_at=datetime.now(),
    )
