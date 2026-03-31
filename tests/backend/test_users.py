"""Tests for UserService (mock-based, no database required)."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from app.services.user_service import UserService
from app.models.user import User
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestUserService:
    def _make_svc(self):
        svc = UserService()
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        return svc

    async def test_create_user(self):
        svc = self._make_svc()
        svc.repo.get_by_email.return_value = None
        svc.repo.create.return_value = User(id=1, name="Alice Smith", email="alice@example.com", created_at=datetime.now())

        user = await svc.create("Alice Smith", "alice@example.com")

        assert user.name == "Alice Smith"
        assert user.email == "alice@example.com"
        svc.repo.create.assert_awaited_once()

    async def test_create_duplicate_email(self, sample_user):
        svc = self._make_svc()
        svc.repo.get_by_email.return_value = sample_user

        with pytest.raises(ValidationError) as exc:
            await svc.create("Another User", sample_user.email)
        assert exc.value.field == "email"

    async def test_create_invalid_email(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError) as exc:
            await svc.create("User", "not-an-email")
        assert exc.value.field == "email"
        svc.repo.get_by_email.assert_not_awaited()

    async def test_create_name_too_short(self):
        svc = self._make_svc()

        with pytest.raises(ValidationError) as exc:
            await svc.create("A", "valid@email.com")
        assert exc.value.field == "name"
        svc.repo.get_by_email.assert_not_awaited()

    async def test_update_user(self, sample_user):
        updated = User(id=sample_user.id, name="New Name", email=sample_user.email, created_at=sample_user.created_at)
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_user
        svc.repo.update.return_value = updated

        result = await svc.update(sample_user.id, name="New Name")

        assert result.name == "New Name"

    async def test_update_nonexistent(self):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = None

        with pytest.raises(ValidationError):
            await svc.update(99999, name="X")

    async def test_delete_user(self, sample_user):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_user
        svc.repo.delete.return_value = True

        result = await svc.delete(sample_user.id)

        assert result is True
        svc.repo.delete.assert_awaited_once_with(sample_user.id)

    async def test_get_all(self, sample_users):
        svc = self._make_svc()
        svc.repo.get_all.return_value = sample_users

        users = await svc.get_all()

        assert len(users) == 2

    async def test_email_normalised_to_lowercase(self):
        svc = self._make_svc()
        svc.repo.get_by_email.return_value = None
        svc.repo.create.return_value = User(id=1, name="Test", email="test@example.com", created_at=datetime.now())

        user = await svc.create("Test", "TEST@EXAMPLE.COM")

        assert user.email == "test@example.com"
        # Verify the DTO passed to create used the normalised email
        dto = svc.repo.create.call_args[0][0]
        assert dto.email == "test@example.com"

    async def test_audit_logged_on_create(self):
        svc = self._make_svc()
        svc.repo.get_by_email.return_value = None
        svc.repo.create.return_value = User(id=5, name="Bob", email="bob@example.com", created_at=datetime.now())

        await svc.create("Bob", "bob@example.com")

        svc.audit.log.assert_awaited_once()

    async def test_audit_logged_on_delete(self, sample_user):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = sample_user
        svc.repo.delete.return_value = True

        await svc.delete(sample_user.id)

        svc.audit.log.assert_awaited_once()
