from typing import Optional

from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.models.user import User, CreateUserDTO, UpdateUserDTO
from app.utils.validators import validate_name, validate_email, ValidationError
from app.utils.logger import get_logger

logger = get_logger("service.user")


class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.audit = AuditRepository()

    async def get_all(self) -> list[User]:
        return await self.repo.get_all()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.repo.get_by_id(user_id)

    async def create(self, name: str, email: str) -> User:
        name = validate_name(name, "name", min_len=2, max_len=100)
        email = validate_email(email)

        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValidationError("email", f"User with email '{email}' already exists")

        dto = CreateUserDTO(name=name, email=email)
        user = await self.repo.create(dto)
        await self.audit.log("users", user.id, "CREATE", new_values=user.to_dict())
        logger.info(f"Created user id={user.id} email={email}")
        return user

    async def update(self, user_id: int, name: Optional[str] = None, email: Optional[str] = None) -> User:
        existing = await self.repo.get_by_id(user_id)
        if not existing:
            raise ValidationError("id", f"User {user_id} not found")

        dto = UpdateUserDTO()
        if name is not None:
            dto.name = validate_name(name, "name", min_len=2, max_len=100)
        if email is not None:
            dto.email = validate_email(email)
            dup = await self.repo.get_by_email(dto.email)
            if dup and dup.id != user_id:
                raise ValidationError("email", f"Email '{email}' already in use")

        updated = await self.repo.update(user_id, dto)
        await self.audit.log("users", user_id, "UPDATE",
                             old_values=existing.to_dict(),
                             new_values=updated.to_dict() if updated else None)
        return updated

    async def delete(self, user_id: int) -> bool:
        existing = await self.repo.get_by_id(user_id)
        if not existing:
            raise ValidationError("id", f"User {user_id} not found")
        result = await self.repo.delete(user_id)
        if result:
            await self.audit.log("users", user_id, "DELETE", old_values=existing.to_dict())
            logger.info(f"Deleted user id={user_id}")
        return result
