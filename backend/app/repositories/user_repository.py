from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active_users(self) -> list[User]:
        result = await self.db.execute(select(User).where(User.is_active == True))
        return list(result.scalars().all())

    async def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        q = select(User).where(User.email == email)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none() is not None
