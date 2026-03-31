from typing import Optional

from app.repositories.category_repository import CategoryRepository
from app.repositories.audit_repository import AuditRepository
from app.models.category import Category, CreateCategoryDTO, UpdateCategoryDTO
from app.utils.validators import validate_name, ValidationError
from app.utils.logger import get_logger

logger = get_logger("service.category")


class CategoryService:
    def __init__(self):
        self.repo = CategoryRepository()
        self.audit = AuditRepository()

    async def get_all(self) -> list[Category]:
        return await self.repo.get_all()

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise ValidationError("id", f"Category {category_id} not found")
        return cat

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        color: str = "#808080",
        icon: str = "📁",
        created_by: Optional[int] = None,
    ) -> Category:
        name = validate_name(name, "name", min_len=1, max_len=100)

        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValidationError("name", f"Category '{name}' already exists")

        dto = CreateCategoryDTO(
            name=name,
            description=description,
            color=color,
            icon=icon,
            created_by=created_by,
        )
        cat = await self.repo.create(dto)
        await self.audit.log("categories", cat.id, "CREATE", new_values=cat.to_dict())
        logger.info(f"Created category id={cat.id} name={name}")
        return cat

    async def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Category:
        existing = await self.repo.get_by_id(category_id)
        if not existing:
            raise ValidationError("id", f"Category {category_id} not found")

        dto = UpdateCategoryDTO()
        if name is not None:
            name = validate_name(name, "name", min_len=1, max_len=100)
            dup = await self.repo.get_by_name(name)
            if dup and dup.id != category_id:
                raise ValidationError("name", f"Category '{name}' already exists")
            dto.name = name
        if description is not None:
            dto.description = description
        if color is not None:
            dto.color = color
        if icon is not None:
            dto.icon = icon

        updated = await self.repo.update(category_id, dto)
        await self.audit.log("categories", category_id, "UPDATE",
                             old_values=existing.to_dict(),
                             new_values=updated.to_dict() if updated else None)
        return updated

    async def delete(self, category_id: int) -> bool:
        existing = await self.repo.get_by_id(category_id)
        if not existing:
            raise ValidationError("id", f"Category {category_id} not found")
        if existing.name.lower() == "other":
            raise ValidationError("name", "Cannot delete the default 'Other' category")

        result = await self.repo.delete(category_id)
        if result:
            await self.audit.log("categories", category_id, "DELETE",
                                 old_values=existing.to_dict())
        return result
