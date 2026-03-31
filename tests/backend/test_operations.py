"""Tests for OperationService (mock-based, no database required)."""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock

from app.services.operation_service import OperationService
from app.models.operation import Operation, OperationFilter
from app.models.enums import OperationType, PaymentType, Currency
from app.utils.validators import ValidationError


def _make_op(
    id=1,
    amount=Decimal("100.00"),
    op_type=OperationType.EXPENSE,
    pay_type=PaymentType.CASH,
    category_id=1,
    user_id=1,
):
    return Operation(
        id=id,
        amount=amount,
        currency=Currency.USD,
        operation_type=op_type,
        payment_type=pay_type,
        category_id=category_id,
        user_id=user_id,
        operation_date=datetime.now(),
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
class TestOperationService:
    def _make_svc(self):
        svc = OperationService()
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        return svc

    async def test_create_expense(self, sample_user, sample_category):
        svc = self._make_svc()
        expected = _make_op(amount=Decimal("150.00"), op_type=OperationType.EXPENSE, pay_type=PaymentType.CASH, category_id=sample_category.id, user_id=sample_user.id)
        svc.repo.create.return_value = expected

        op = await svc.create(
            amount=Decimal("150.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category.id,
            user_id=sample_user.id,
            operation_date=datetime.now(),
            description="Lunch",
        )

        assert op.amount == Decimal("150.00")
        assert op.operation_type == OperationType.EXPENSE
        svc.repo.create.assert_awaited_once()

    async def test_create_income(self, sample_user, sample_category):
        svc = self._make_svc()
        expected = _make_op(amount=Decimal("2500.00"), op_type=OperationType.INCOME, pay_type=PaymentType.DEBIT_CARD)
        svc.repo.create.return_value = expected

        op = await svc.create(
            amount=Decimal("2500.00"),
            currency=Currency.USD,
            operation_type=OperationType.INCOME,
            payment_type=PaymentType.DEBIT_CARD,
            category_id=sample_category.id,
            user_id=sample_user.id,
            operation_date=datetime.now(),
        )

        assert op.operation_type == OperationType.INCOME

    async def test_invalid_payment_type_for_expense(self, sample_user, sample_category):
        svc = self._make_svc()

        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("100.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.REFUND_TO_DEBIT,  # invalid for expense
                category_id=sample_category.id,
                user_id=sample_user.id,
                operation_date=datetime.now(),
            )
        assert exc.value.field == "payment_type"
        svc.repo.create.assert_not_awaited()

    async def test_invalid_payment_type_for_income(self, sample_user, sample_category):
        svc = self._make_svc()

        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("100.00"),
                currency=Currency.USD,
                operation_type=OperationType.INCOME,
                payment_type=PaymentType.CREDIT_CARD,  # invalid for income
                category_id=sample_category.id,
                user_id=sample_user.id,
                operation_date=datetime.now(),
            )
        assert exc.value.field == "payment_type"
        svc.repo.create.assert_not_awaited()

    async def test_negative_amount_rejected(self, sample_user, sample_category):
        svc = self._make_svc()

        with pytest.raises(ValidationError) as exc:
            await svc.create(
                amount=Decimal("-100.00"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category.id,
                user_id=sample_user.id,
                operation_date=datetime.now(),
            )
        assert exc.value.field == "amount"
        svc.repo.create.assert_not_awaited()

    async def test_zero_amount_rejected(self, sample_user, sample_category):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.create(
                amount=Decimal("0"),
                currency=Currency.USD,
                operation_type=OperationType.EXPENSE,
                payment_type=PaymentType.CASH,
                category_id=sample_category.id,
                user_id=sample_user.id,
                operation_date=datetime.now(),
            )
        svc.repo.create.assert_not_awaited()

    async def test_delete_operation(self, sample_operation):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_operation
        svc.repo.delete.return_value = True

        result = await svc.delete(sample_operation.id)

        assert result is True
        svc.repo.delete.assert_awaited_once_with(sample_operation.id)

    async def test_delete_nonexistent(self):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = None

        with pytest.raises(ValidationError):
            await svc.delete(99999)
        svc.repo.delete.assert_not_awaited()

    async def test_monthly_summary(self):
        svc = self._make_svc()
        now = datetime.now()
        svc.repo.get_sum_by_type.return_value = {
            "income": Decimal("1000.00"),
            "expense": Decimal("300.00"),
        }

        summary = await svc.get_monthly_summary(now.year, now.month)

        assert summary["total_income"] == 1000.0
        assert summary["total_expense"] == 300.0
        assert summary["net"] == 700.0

    async def test_amount_precision(self, sample_user, sample_category):
        svc = self._make_svc()
        rounded_op = _make_op(amount=Decimal("100.00"), category_id=sample_category.id, user_id=sample_user.id)
        svc.repo.create.return_value = rounded_op

        await svc.create(
            amount=Decimal("99.999"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category.id,
            user_id=sample_user.id,
            operation_date=datetime.now(),
        )

        dto = svc.repo.create.call_args[0][0]
        assert dto.amount == Decimal("100.00")

    async def test_get_many_paginated(self, sample_operation):
        svc = self._make_svc()
        page1_ops = [sample_operation] * 3
        page2_ops = [sample_operation] * 2
        svc.repo.get_many.side_effect = [page1_ops, page2_ops]
        svc.repo.count_many.return_value = 5

        page1, total = await svc.get_many(limit=3, offset=0)
        assert len(page1) == 3
        assert total == 5

        page2, _ = await svc.get_many(limit=3, offset=3)
        assert len(page2) == 2

    async def test_audit_logged_on_create(self, sample_user, sample_category):
        svc = self._make_svc()
        svc.repo.create.return_value = _make_op(category_id=sample_category.id, user_id=sample_user.id)

        await svc.create(
            amount=Decimal("50.00"),
            currency=Currency.USD,
            operation_type=OperationType.EXPENSE,
            payment_type=PaymentType.CASH,
            category_id=sample_category.id,
            user_id=sample_user.id,
            operation_date=datetime.now(),
        )

        svc.audit.log.assert_awaited_once()
