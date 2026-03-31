"""Tests for CategoryService (mock-based, no database required)."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from app.services.category_service import CategoryService
from app.models.category import Category
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestCategoryService:
    def _make_svc(self):
        svc = CategoryService()
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        return svc

    async def test_create(self):
        svc = self._make_svc()
        svc.repo.get_by_name.return_value = None
        svc.repo.create.return_value = Category(id=1, name="Food", description="Daily food", color="#ff0000", created_at=datetime.now())

        cat = await svc.create("Food", description="Daily food", color="#ff0000")

        assert cat.name == "Food"
        svc.repo.create.assert_awaited_once()

    async def test_create_duplicate_name(self, sample_category):
        svc = self._make_svc()
        svc.repo.get_by_name.return_value = sample_category

        with pytest.raises(ValidationError) as exc:
            await svc.create(sample_category.name)
        assert exc.value.field == "name"

    async def test_create_empty_name(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError):
            await svc.create("")
        svc.repo.get_by_name.assert_not_awaited()

    async def test_update(self, sample_category):
        updated = Category(id=sample_category.id, name="Changed", color=sample_category.color, created_at=sample_category.created_at)
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_category
        svc.repo.get_by_name.return_value = None
        svc.repo.update.return_value = updated

        result = await svc.update(sample_category.id, name="Changed")

        assert result.name == "Changed"

    async def test_update_nonexistent(self):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = None

        with pytest.raises(ValidationError):
            await svc.update(99999, name="New")

    async def test_delete(self, sample_category):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_category
        svc.repo.delete.return_value = True

        result = await svc.delete(sample_category.id)

        assert result is True
        svc.repo.delete.assert_awaited_once_with(sample_category.id)

    async def test_cannot_delete_other(self, other_category):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = other_category

        with pytest.raises(ValidationError) as exc:
            await svc.delete(other_category.id)
        assert "default" in exc.value.message.lower() or "Other" in exc.value.message
        svc.repo.delete.assert_not_awaited()

    async def test_get_all(self, sample_category):
        svc = self._make_svc()
        svc.repo.get_all.return_value = [sample_category]

        cats = await svc.get_all()

        assert any(c.id == sample_category.id for c in cats)

    async def test_audit_logged_on_create(self):
        svc = self._make_svc()
        svc.repo.get_by_name.return_value = None
        svc.repo.create.return_value = Category(id=1, name="Sports", created_at=datetime.now())

        await svc.create("Sports")

        svc.audit.log.assert_awaited_once()
