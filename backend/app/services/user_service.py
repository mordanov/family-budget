from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_all(self) -> list[UserResponse]:
        users = await self.repo.get_active_users()
        return [UserResponse.model_validate(u) for u in users]

    async def get_by_id(self, user_id: int) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    async def create(self, data: UserCreate) -> UserResponse:
        if await self.repo.email_exists(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=get_password_hash(data.password),
        )
        user = await self.repo.create(user)
        return UserResponse.model_validate(user)

    async def update(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if data.email and await self.repo.email_exists(data.email, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="Email already in use")
        if data.name is not None:
            user.name = data.name
        if data.email is not None:
            user.email = data.email
        if data.password is not None:
            user.hashed_password = get_password_hash(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active
        await self.repo.db.flush()
        await self.repo.db.refresh(user)
        return UserResponse.model_validate(user)

    async def delete(self, user_id: int) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = False
        await self.repo.db.flush()
