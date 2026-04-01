from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_method import PaymentMethod
from app.repositories.base import BaseRepository


class PaymentMethodRepository(BaseRepository[PaymentMethod]):
    def __init__(self, db: AsyncSession):
        super().__init__(PaymentMethod, db)

    async def get_all_active(self) -> list[PaymentMethod]:
        result = await self.db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.is_active == True)
            .order_by(PaymentMethod.id)
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> PaymentMethod | None:
        result = await self.db.execute(select(PaymentMethod).where(PaymentMethod.key == key))
        return result.scalar_one_or_none()

    async def ensure_defaults(self) -> None:
        defaults = [
            ("cash", "Cash"),
            ("card", "Card"),
            ("bank_transfer", "Bank Transfer"),
            ("other", "Other"),
        ]
        for key, name in defaults:
            if not await self.get_by_key(key):
                self.db.add(PaymentMethod(key=key, name=name, is_active=True))
        await self.db.flush()



