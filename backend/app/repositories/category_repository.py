from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)

    async def get_all_active(self) -> list[Category]:
        result = await self.db.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def get_default(self) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.is_default == True))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        q = select(Category).where(Category.name == name)
        if exclude_id:
            q = q.where(Category.id != exclude_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none() is not None
