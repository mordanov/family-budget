"""
Shared fixtures for backend unit tests.
All tests use mocks — no database connection required.
"""
from datetime import datetime
from decimal import Decimal

import pytest

from app.models.user import User
from app.models.category import Category
from app.models.operation import Operation
from app.models.enums import OperationType, PaymentType, Currency


@pytest.fixture
def sample_user() -> User:
    return User(id=1, name="Test User", email="test@example.com", created_at=datetime.now())


@pytest.fixture
def sample_users() -> list[User]:
    return [
        User(id=1, name="Alice", email="alice@test.com", created_at=datetime.now()),
        User(id=2, name="Bob", email="bob@test.com", created_at=datetime.now()),
    ]


@pytest.fixture
def sample_category() -> Category:
    return Category(id=1, name="Test Category", color="#ff0000", icon="🧪", created_at=datetime.now())


@pytest.fixture
def other_category() -> Category:
    return Category(id=2, name="Other", created_at=datetime.now())


@pytest.fixture
def sample_operation(sample_user, sample_category) -> Operation:
    return Operation(
        id=1,
        amount=Decimal("100.00"),
        currency=Currency.USD,
        operation_type=OperationType.EXPENSE,
        payment_type=PaymentType.DEBIT_CARD,
        category_id=sample_category.id,
        user_id=sample_user.id,
        operation_date=datetime.now(),
        created_at=datetime.now(),
        category_name=sample_category.name,
        user_name=sample_user.name,
    )
