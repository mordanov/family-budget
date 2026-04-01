from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def get_all(self) -> list[CategoryResponse]:
        cats = await self.repo.get_all_active()
        return [CategoryResponse.model_validate(c) for c in cats]

    async def get_by_id(self, category_id: int) -> CategoryResponse:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        return CategoryResponse.model_validate(cat)

    async def create(self, data: CategoryCreate) -> CategoryResponse:
        if await self.repo.name_exists(data.name):
            raise HTTPException(status_code=400, detail="Category name already exists")
        cat = Category(**data.model_dump())
        cat = await self.repo.create(cat)
        return CategoryResponse.model_validate(cat)

    async def update(self, category_id: int, data: CategoryUpdate) -> CategoryResponse:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        if cat.is_default and data.name and data.name != cat.name:
            raise HTTPException(status_code=400, detail="Cannot rename default category")
        if data.name and await self.repo.name_exists(data.name, exclude_id=category_id):
            raise HTTPException(status_code=400, detail="Category name already exists")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(cat, field, value)
        await self.repo.db.flush()
        await self.repo.db.refresh(cat)
        return CategoryResponse.model_validate(cat)

    async def delete(self, category_id: int) -> None:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        if cat.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete the default category")
        cat.is_active = False
        await self.repo.db.flush()
