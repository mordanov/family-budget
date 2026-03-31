"""Tests for OperationRepository and OperationService."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.repositories.operation_repository import OperationRepository
from app.services.operation_service import OperationService
from app.models.operation import CreateOperationDTO, UpdateOperationDTO, OperationFilter
from app.models.enums import OperationType, PaymentType, Currency
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestOperationRepository:
    async def test_create_operation(self, sample_user, sample_category):
        repo = OperationRepository()
        dto = CreateOperationDTO(
            amount=Decimal("250.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
            description="Test purchase",
        )
        op = await repo.create(dto)
        assert op.id is not None
        assert op.amount == Decimal("250.00")
        assert op.operation_type == OperationType.EXPENSE
        assert op.category_name == sample_category["name"]
        assert op.user_name == sample_user["name"]

    async def test_get_by_id(self, sample_operation):
        repo = OperationRepository()
        op = await repo.get_by_id(sample_operation["id"])
        assert op is not None
        assert op.id == sample_operation["id"]

    async def test_get_by_id_not_found(self):
        repo = OperationRepository()
        assert await repo.get_by_id(99999) is None

    async def test_get_many_no_filter(self, sample_operation):
        repo = OperationRepository()
        f = OperationFilter()
        ops = await repo.get_many(f, limit=10)
        assert len(ops) >= 1

    async def test_filter_by_type(self, sample_operation, sample_user, sample_category):
        repo = OperationRepository()

        # Create income operation
        dto = CreateOperationDTO(
            amount=Decimal("500.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
        )
        await repo.create(dto)

        expense_filter = OperationFilter(operation_type=OperationType.EXPENSE)
        expenses = await repo.get_many(expense_filter)
        assert all(op.operation_type == OperationType.EXPENSE for op in expenses)

        income_filter = OperationFilter(operation_type=OperationType.INCOME)
        incomes = await repo.get_many(income_filter)
        assert all(op.operation_type == OperationType.INCOME for op in incomes)

    async def test_filter_by_date_range(self, sample_user, sample_category):
        repo = OperationRepository()
        now = datetime.now()

        # Create operation in past
        past_dto = CreateOperationDTO(
            amount=Decimal("100.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now - timedelta(days=60),
        )
        await repo.create(past_dto)

        # Create recent operation
        recent_dto = CreateOperationDTO(
            amount=Decimal("200.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )
        await repo.create(recent_dto)

        date_filter = OperationFilter(
            date_from=now - timedelta(days=1),
            date_to=now + timedelta(days=1),
        )
        filtered = await repo.get_many(date_filter)
        assert len(filtered) == 1
        assert float(filtered[0].amount) == 200.0

    async def test_soft_delete(self, sample_operation):
        repo = OperationRepository()
        result = await repo.delete(sample_operation["id"])
        assert result is True
        assert await repo.get_by_id(sample_operation["id"]) is None

    async def test_count_many(self, sample_operation):
        repo = OperationRepository()
        f = OperationFilter()
        count = await repo.count_many(f)
        assert count >= 1

    async def test_get_sum_by_type(self, sample_user, sample_category):
        repo = OperationRepository()
        for amount in ["100.00", "200.00", "150.00"]:
            dto = CreateOperationDTO(
                amount=Decimal(amount),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )
            await repo.create(dto)

        f = OperationFilter()
        sums = await repo.get_sum_by_type(f)
        assert "expense" in sums
        assert sums["expense"] == Decimal("450.00")

    async def test_update_operation(self, sample_operation):
        repo = OperationRepository()
        dto = UpdateOperationDTO(amount=Decimal("999.99"), description="Updated")
        updated = await repo.update(sample_operation["id"], dto)
        assert updated is not None
        assert updated.amount == Decimal("999.99")
        assert updated.description == "Updated"

    async def test_get_recurring(self, sample_user, sample_category):
        repo = OperationRepository()
        dto = CreateOperationDTO(
            amount=Decimal("50.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
            is_recurring=True,
        )
        await repo.create(dto)
        recurring = await repo.get_recurring()
        assert len(recurring) == 1
        assert recurring[0].is_recurring is True


@pytest.mark.asyncio
class TestOperationService:
    async def test_create_expense(self, sample_user, sample_category):
        svc = OperationService()
        op = await svc.create(
            amount=Decimal("150.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
            description="Lunch",
        )
        assert op.id is not None
        assert op.amount == Decimal("150.00")

    async def test_create_income(self, sample_user, sample_category):
        svc = OperationService()
        op = await svc.create(
            amount=Decimal("2500.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
        )
        assert op.operation_type == OperationType.INCOME

    async def test_invalid_payment_type_for_expense(self, sample_user, sample_category):
        svc = OperationService()
        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("100.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.REFUND_TO_DEBIT,  # invalid for expense
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )
        assert exc.value.field == "payment_type"

    async def test_invalid_payment_type_for_income(self, sample_user, sample_category):
        svc = OperationService()
        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("100.00"),
                currency=Currency.USD,
                operation_type=OperationType.INCOME,
                payment_type=PaymentType.CREDIT_CARD,  # invalid for income
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )
        assert exc.value.field == "payment_type"

    async def test_negative_amount_rejected(self, sample_user, sample_category):
        svc = OperationService()
        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("-100.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )
        assert exc.value.field == "amount"

    async def test_zero_amount_rejected(self, sample_user, sample_category):
        svc = OperationService()
        with pytest.raises(ValidationError):
            await svc.create(
                amount=Decimal("0"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )

    async def test_delete_operation(self, sample_operation):
        svc = OperationService()
        result = await svc.delete(sample_operation["id"])
        assert result is True

    async def test_delete_nonexistent(self):
        svc = OperationService()
        with pytest.raises(ValidationError):
            await svc.delete(99999)

    async def test_monthly_summary(self, sample_user, sample_category):
        svc = OperationService()
        now = datetime.now()

        await svc.create(
            amount=Decimal("1000.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )
        await svc.create(
            amount=Decimal("300.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=now,
        )

        summary = await svc.get_monthly_summary(now.year, now.month)
        assert summary["total_income"] == 1000.0
        assert summary["total_expense"] == 300.0
        assert summary["net"] == 700.0

    async def test_amount_precision(self, sample_user, sample_category):
        svc = OperationService()
        op = await svc.create(
            amount=Decimal("99.999"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category["id"],
            user_id=sample_user["id"],
            operation_date=datetime.now(),
        )
        # Should be rounded to 2 decimal places
        assert op.amount == Decimal("100.00")

    async def test_get_many_paginated(self, sample_user, sample_category):
        svc = OperationService()
        for i in range(5):
            await svc.create(
                amount=Decimal(f"{(i + 1) * 10}.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category["id"],
                user_id=sample_user["id"],
                operation_date=datetime.now(),
            )

        page1, total = await svc.get_many(limit=3, offset=0)
        assert len(page1) == 3
        assert total == 5

        page2, _ = await svc.get_many(limit=3, offset=3)
        assert len(page2) == 2
