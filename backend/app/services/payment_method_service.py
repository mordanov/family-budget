from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payment_method_repository import PaymentMethodRepository
from app.schemas.payment_method import PaymentMethodResponse, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, db: AsyncSession):
        self.repo = PaymentMethodRepository(db)

    async def get_all(self) -> list[PaymentMethodResponse]:
        await self.repo.ensure_defaults()
        items = await self.repo.get_all_active()
        return [PaymentMethodResponse.model_validate(item) for item in items]

    async def update(self, payment_method_id: int, data: PaymentMethodUpdate) -> PaymentMethodResponse:
        item = await self.repo.get_by_id(payment_method_id)
        if not item:
            raise HTTPException(status_code=404, detail="Payment method not found")
        item.name = data.name.strip()
        await self.repo.db.flush()
        await self.repo.db.refresh(item)
        return PaymentMethodResponse.model_validate(item)

