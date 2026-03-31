"""Tests for CategoryRepository and CategoryService."""
import pytest

from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService
from app.models.category import CreateCategoryDTO, UpdateCategoryDTO
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestCategoryRepository:
    async def test_create_category(self):
        repo = CategoryRepository()
        dto = CreateCategoryDTO(name="Groceries", color="#00ff00", icon="🛒")
        cat = await repo.create(dto)

        assert cat.id is not None
        assert cat.name == "Groceries"
        assert cat.color == "#00ff00"
        assert cat.icon == "🛒"

    async def test_get_by_id(self, sample_category):
        repo = CategoryRepository()
        cat = await repo.get_by_id(sample_category["id"])
        assert cat is not None
        assert cat.name == sample_category["name"]

    async def test_get_by_name_case_insensitive(self, sample_category):
        repo = CategoryRepository()
        cat = await repo.get_by_name(sample_category["name"].upper())
        assert cat is not None

    async def test_get_all(self, sample_category):
        repo = CategoryRepository()
        cats = await repo.get_all()
        assert len(cats) >= 1

    async def test_update_category(self, sample_category):
        repo = CategoryRepository()
        dto = UpdateCategoryDTO(name="Updated Name", color="#0000ff")
        updated = await repo.update(sample_category["id"], dto)
        assert updated.name == "Updated Name"
        assert updated.color == "#0000ff"

    async def test_soft_delete(self, sample_category):
        repo = CategoryRepository()
        result = await repo.delete(sample_category["id"])
        assert result is True
        assert await repo.get_by_id(sample_category["id"]) is None

    async def test_get_by_id_not_found(self):
        repo = CategoryRepository()
        assert await repo.get_by_id(99999) is None


@pytest.mark.asyncio
class TestCategoryService:
    async def test_create(self):
        svc = CategoryService()
        cat = await svc.create("Food", description="Daily food", color="#ff0000")
        assert cat.name == "Food"

    async def test_create_duplicate_name(self, sample_category):
        svc = CategoryService()
        with pytest.raises(ValidationError) as exc:
            await svc.create(sample_category["name"])
        assert exc.value.field == "name"

    async def test_create_empty_name(self):
        svc = CategoryService()
        with pytest.raises(ValidationError):
            await svc.create("")

    async def test_update(self, sample_category):
        svc = CategoryService()
        updated = await svc.update(sample_category["id"], name="Changed")
        assert updated.name == "Changed"

    async def test_delete(self, sample_category):
        svc = CategoryService()
        result = await svc.delete(sample_category["id"])
        assert result is True

    async def test_cannot_delete_other(self, other_category):
        svc = CategoryService()
        with pytest.raises(ValidationError) as exc:
            await svc.delete(other_category["id"])
        assert "default" in exc.value.message.lower() or "Other" in exc.value.message

    async def test_get_all(self, sample_category):
        svc = CategoryService()
        cats = await svc.get_all()
        assert any(c.id == sample_category["id"] for c in cats)
