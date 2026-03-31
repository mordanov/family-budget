from typing import Optional
from decimal import Decimal
from datetime import datetime, date

from app.repositories.operation_repository import OperationRepository
from app.repositories.audit_repository import AuditRepository
from app.models.operation import (
    Operation, CreateOperationDTO, UpdateOperationDTO, OperationFilter
)
from app.models.enums import OperationType, PaymentType, Currency, EXPENSE_PAYMENT_TYPES, INCOME_PAYMENT_TYPES
from app.utils.validators import validate_amount, ValidationError, sanitize_description
from app.utils.logger import get_logger

logger = get_logger("service.operation")


class OperationService:
    def __init__(self):
        self.repo = OperationRepository()
        self.audit = AuditRepository()

    def _validate_payment_type(self, op_type: OperationType, payment_type: PaymentType) -> None:
        if op_type == OperationType.EXPENSE and payment_type not in EXPENSE_PAYMENT_TYPES:
            raise ValidationError(
                "payment_type",
                f"Payment type '{payment_type.value}' is not valid for expenses. "
                f"Valid: {[p.value for p in EXPENSE_PAYMENT_TYPES]}"
            )
        if op_type == OperationType.INCOME and payment_type not in INCOME_PAYMENT_TYPES:
            raise ValidationError(
                "payment_type",
                f"Payment type '{payment_type.value}' is not valid for income. "
                f"Valid: {[p.value for p in INCOME_PAYMENT_TYPES]}"
            )

    async def get_by_id(self, op_id: int) -> Optional[Operation]:
        op = await self.repo.get_by_id(op_id)
        if not op:
            raise ValidationError("id", f"Operation {op_id} not found")
        return op

    async def get_many(
        self,
        f: Optional[OperationFilter] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Operation], int]:
        f = f or OperationFilter()
        ops = await self.repo.get_many(f, limit=limit, offset=offset)
        total = await self.repo.count_many(f)
        return ops, total

    async def create(
        self,
        amount: Decimal,
        currency: Currency,
        operation_type: OperationType,
        payment_type: PaymentType,
        category_id: int,
        user_id: int,
        operation_date: datetime,
        description: Optional[str] = None,
        recurring_rule_id: Optional[int] = None,
        forecast_end_date: Optional[date] = None,
        is_recurring: bool = False,
    ) -> Operation:
        amount = validate_amount(amount)
        self._validate_payment_type(operation_type, payment_type)
        description = sanitize_description(description)

        dto = CreateOperationDTO(
            amount=amount,
            currency=currency,
            operation_type=operation_type,
            payment_type=payment_type,
            category_id=category_id,
            user_id=user_id,
            operation_date=operation_date,
            description=description,
            recurring_rule_id=recurring_rule_id,
            forecast_end_date=forecast_end_date,
            is_recurring=is_recurring,
        )
        op = await self.repo.create(dto)
        await self.audit.log("operations", op.id, "CREATE",
                             new_values=op.to_dict(), user_id=user_id)
        logger.info(f"Created operation id={op.id} type={operation_type.value} amount={amount}")
        return op

    async def update(
        self,
        op_id: int,
        amount: Optional[Decimal] = None,
        currency: Optional[Currency] = None,
        operation_type: Optional[OperationType] = None,
        payment_type: Optional[PaymentType] = None,
        category_id: Optional[int] = None,
        user_id: Optional[int] = None,
        operation_date: Optional[datetime] = None,
        description: Optional[str] = None,
        recurring_rule_id: Optional[int] = None,
        forecast_end_date: Optional[date] = None,
        is_recurring: Optional[bool] = None,
    ) -> Operation:
        existing = await self.repo.get_by_id(op_id)
        if not existing:
            raise ValidationError("id", f"Operation {op_id} not found")

        if amount is not None:
            amount = validate_amount(amount)

        eff_op_type = operation_type or existing.operation_type
        eff_pay_type = payment_type or existing.payment_type
        self._validate_payment_type(eff_op_type, eff_pay_type)

        dto = UpdateOperationDTO(
            amount=amount,
            currency=currency,
            operation_type=operation_type,
            payment_type=payment_type,
            category_id=category_id,
            user_id=user_id,
            operation_date=operation_date,
            description=sanitize_description(description) if description is not None else None,
            recurring_rule_id=recurring_rule_id,
            forecast_end_date=forecast_end_date,
            is_recurring=is_recurring,
        )
        updated = await self.repo.update(op_id, dto)
        await self.audit.log("operations", op_id, "UPDATE",
                             old_values=existing.to_dict(),
                             new_values=updated.to_dict() if updated else None,
                             user_id=existing.user_id)
        return updated

    async def delete(self, op_id: int) -> bool:
        existing = await self.repo.get_by_id(op_id)
        if not existing:
            raise ValidationError("id", f"Operation {op_id} not found")
        result = await self.repo.delete(op_id)
        if result:
            await self.audit.log("operations", op_id, "DELETE",
                                 old_values=existing.to_dict(),
                                 user_id=existing.user_id)
            logger.info(f"Deleted operation id={op_id}")
        return result

    async def get_monthly_summary(self, year: int, month: int) -> dict:
        from datetime import datetime as dt
        import calendar
        start = dt(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = dt(year, month, last_day, 23, 59, 59)

        f = OperationFilter(date_from=start, date_to=end)
        sums = await self.repo.get_sum_by_type(f)

        return {
            "year": year,
            "month": month,
            "total_income": float(sums.get("income", Decimal("0"))),
            "total_expense": float(sums.get("expense", Decimal("0"))),
            "net": float(
                sums.get("income", Decimal("0")) - sums.get("expense", Decimal("0"))
            ),
        }
