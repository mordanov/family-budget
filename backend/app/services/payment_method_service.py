import re

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_method import PaymentMethod
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodResponse, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, db: AsyncSession):
        self.repo = PaymentMethodRepository(db)

    async def get_all(self) -> list[PaymentMethodResponse]:
        await self.repo.ensure_defaults()
        items = await self.repo.get_all_active()
        return [PaymentMethodResponse.model_validate(item) for item in items]

    async def get_by_id(self, payment_method_id: int) -> PaymentMethodResponse:
        await self.repo.ensure_defaults()
        item = await self.repo.get_by_id(payment_method_id)
        if not item or not item.is_active:
            raise HTTPException(status_code=404, detail="Payment method not found")
        return PaymentMethodResponse.model_validate(item)

    def _slugify(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
        return slug or "payment_method"

    async def _build_unique_key(self, name: str) -> str:
        base_key = self._slugify(name)
        candidate = base_key
        index = 2
        while await self.repo.get_by_key(candidate):
            candidate = f"{base_key}_{index}"
            index += 1
        return candidate

    async def create(self, data: PaymentMethodCreate) -> PaymentMethodResponse:
        await self.repo.ensure_defaults()
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise HTTPException(status_code=400, detail="Payment method name already exists")
        item = PaymentMethod(
            key=await self._build_unique_key(name),
            name=name,
            is_active=True,
        )
        item = await self.repo.create(item)
        return PaymentMethodResponse.model_validate(item)

    async def update(self, payment_method_id: int, data: PaymentMethodUpdate) -> PaymentMethodResponse:
        item = await self.repo.get_by_id(payment_method_id)
        if not item or not item.is_active:
            raise HTTPException(status_code=404, detail="Payment method not found")
        name = data.name.strip()
        if await self.repo.get_by_name(name, exclude_id=payment_method_id):
            raise HTTPException(status_code=400, detail="Payment method name already exists")
        item.name = name
        await self.repo.db.flush()
        await self.repo.db.refresh(item)
        return PaymentMethodResponse.model_validate(item)

    async def delete(self, payment_method_id: int) -> None:
        await self.repo.ensure_defaults()
        item = await self.repo.get_by_id(payment_method_id)
        if not item or not item.is_active:
            raise HTTPException(status_code=404, detail="Payment method not found")
        if await self.repo.count_active() <= 1:
            raise HTTPException(status_code=400, detail="At least one payment method must remain active")
        item.is_active = False
        await self.repo.db.flush()

