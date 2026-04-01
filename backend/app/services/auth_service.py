from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, Token, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def login(self, login: str, password: str) -> Token:
        user = await self.repo.get_by_login_identifier(login)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token, user=UserResponse.model_validate(user))

    async def register(self, data: UserCreate) -> UserResponse:
        if await self.repo.email_exists(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        from app.models.user import User
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=get_password_hash(data.password),
        )
        user = await self.repo.create(user)
        return UserResponse.model_validate(user)
