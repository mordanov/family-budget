from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation, PaymentType
from app.repositories.operation_repository import OperationRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.repositories.user_repository import UserRepository
from app.schemas.operation import (
    OperationCreate, OperationUpdate, OperationResponse,
    OperationListResponse, OperationFilter,
)
from app.services.attachment_service import AttachmentService
from app.services.balance_service import BalanceService


class OperationService:
    def __init__(self, db: AsyncSession):
        self.repo = OperationRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.pm_repo = PaymentMethodRepository(db)
        self.user_repo = UserRepository(db)
        self.attachment_service = AttachmentService(db)
        self.balance_service = BalanceService(db)

    async def _resolve_payment_method(self, payment_type: str | None, payment_method_id: int | None = None) -> tuple[int, PaymentType]:
        await self.pm_repo.ensure_defaults()
        pm = None
        if payment_method_id is not None:
            pm = await self.pm_repo.get_by_id(payment_method_id)
            if not pm or not pm.is_active:
                raise HTTPException(status_code=400, detail="Payment method not found")
        elif payment_type:
            payment_type_str = payment_type.value if hasattr(payment_type, "value") else str(payment_type)
            pm = await self.pm_repo.get_by_key(payment_type_str)
            if not pm or not pm.is_active:
                raise HTTPException(status_code=400, detail="Payment method not found")
        else:
            pm = await self.pm_repo.get_by_key("card")
        if not pm:
            raise HTTPException(status_code=400, detail="Payment method not found")
        try:
            legacy_payment_type = PaymentType(pm.key)
        except ValueError:
            legacy_payment_type = PaymentType.other
        return pm.id, legacy_payment_type

    async def _resolve_payment_method_for_update(
        self,
        op: Operation,
        payment_type: str | None = None,
        payment_method_id: int | None = None,
    ) -> tuple[int, PaymentType]:
        if payment_type is None and payment_method_id is None:
            return op.payment_method_id, op.payment_type
        return await self._resolve_payment_method(payment_type, payment_method_id)

    async def _validate_refs(self, category_id: int, user_id: int):
        cat = await self.cat_repo.get_by_id(category_id)
        if not cat or not cat.is_active:
            raise HTTPException(status_code=404, detail="Category not found")
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=404, detail="User not found")

    async def get_list(self, filters: OperationFilter) -> OperationListResponse:
        skip = (filters.page - 1) * filters.size
        items, total = await self.repo.get_filtered(
            date_from=filters.date_from,
            date_to=filters.date_to,
            type=filters.type,
            payment_type=filters.payment_type,
            payment_method_id=filters.payment_method_id,
            category_id=filters.category_id,
            user_id=filters.user_id,
            is_recurring=filters.is_recurring,
            skip=skip,
            limit=filters.size,
        )
        pages = (total + filters.size - 1) // filters.size if total > 0 else 1
        return OperationListResponse(
            items=[OperationResponse.model_validate(i) for i in items],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=pages,
        )

    async def get_by_id(self, op_id: int) -> OperationResponse:
        op = await self.repo.get_by_id_with_relations(op_id)
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        return OperationResponse.model_validate(op)

    async def create(self, data: OperationCreate) -> OperationResponse:
        await self._validate_refs(data.category_id, data.user_id)
        payload = data.model_dump()
        payment_method_id, payment_type = await self._resolve_payment_method(
            payload.pop("payment_type", None),
            payload.get("payment_method_id"),
        )
        payload["payment_method_id"] = payment_method_id
        payload["payment_type"] = payment_type
        op = Operation(**payload)
        op = await self.repo.create(op)
        op = await self.repo.get_by_id_with_relations(op.id)
        await self.balance_service.recalculate_month(
            op.operation_date.year, op.operation_date.month
        )
        return OperationResponse.model_validate(op)

    async def create_with_attachments(
        self, data: OperationCreate, files: list[UploadFile]
    ) -> OperationResponse:
        created = await self.create(data)
        if files:
            await self.attachment_service.upload_many(created.id, files)
            op = await self.repo.get_by_id_with_relations(created.id)
            return OperationResponse.model_validate(op)
        return created

    async def update(self, op_id: int, data: OperationUpdate) -> OperationResponse:
        op = await self.repo.get_by_id_with_relations(op_id)
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        if data.category_id:
            await self._validate_refs(data.category_id, op.user_id)
        if data.user_id:
            await self._validate_refs(op.category_id, data.user_id)
        old_year, old_month = op.operation_date.year, op.operation_date.month
        payload = data.model_dump(exclude_none=True)
        if "payment_type" in payload or "payment_method_id" in payload:
            payment_method_id, payment_type = await self._resolve_payment_method_for_update(
                op,
                payload.pop("payment_type", None),
                payload.get("payment_method_id"),
            )
            payload["payment_method_id"] = payment_method_id
            payload["payment_type"] = payment_type
        for field, value in payload.items():
            setattr(op, field, value)
        await self.repo.db.flush()
        await self.repo.db.refresh(op)
        op = await self.repo.get_by_id_with_relations(op_id)
        await self.balance_service.recalculate_month(old_year, old_month)
        if op.operation_date.year != old_year or op.operation_date.month != old_month:
            await self.balance_service.recalculate_month(
                op.operation_date.year, op.operation_date.month
            )
        return OperationResponse.model_validate(op)

    async def delete(self, op_id: int) -> None:
        op = await self.repo.get_by_id_with_relations(op_id)
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        year, month = op.operation_date.year, op.operation_date.month
        await self.repo.soft_delete(op)
        await self.balance_service.recalculate_month(year, month)
