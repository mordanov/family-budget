"""Tests for UserRepository and UserService."""
import pytest
import pytest_asyncio

from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.utils.validators import ValidationError


@pytest.mark.asyncio
class TestUserRepository:
    async def test_create_user(self, db_pool):
        repo = UserRepository()
        from app.models.user import CreateUserDTO
        dto = CreateUserDTO(name="Test User", email="test@example.com")
        user = await repo.create(dto)

        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.deleted_at is None

    async def test_get_by_id(self, sample_user):
        repo = UserRepository()
        user = await repo.get_by_id(sample_user["id"])
        assert user is not None
        assert user.id == sample_user["id"]

    async def test_get_by_email(self, sample_user):
        repo = UserRepository()
        user = await repo.get_by_email(sample_user["email"])
        assert user is not None
        assert user.email == sample_user["email"]

    async def test_get_all(self, sample_users):
        repo = UserRepository()
        users = await repo.get_all()
        assert len(users) == 2

    async def test_get_by_id_not_found(self):
        repo = UserRepository()
        user = await repo.get_by_id(99999)
        assert user is None

    async def test_update_user(self, sample_user):
        repo = UserRepository()
        from app.models.user import UpdateUserDTO
        dto = UpdateUserDTO(name="Updated Name")
        updated = await repo.update(sample_user["id"], dto)
        assert updated.name == "Updated Name"
        assert updated.email == sample_user["email"]

    async def test_soft_delete(self, sample_user):
        repo = UserRepository()
        result = await repo.delete(sample_user["id"])
        assert result is True

        # Should not be found after soft delete
        user = await repo.get_by_id(sample_user["id"])
        assert user is None

    async def test_delete_nonexistent(self):
        repo = UserRepository()
        result = await repo.delete(99999)
        assert result is False

    async def test_exists(self, sample_user):
        repo = UserRepository()
        assert await repo.exists(sample_user["id"]) is True
        assert await repo.exists(99999) is False


@pytest.mark.asyncio
class TestUserService:
    async def test_create_user(self):
        svc = UserService()
        user = await svc.create("Alice Smith", "alice@example.com")
        assert user.name == "Alice Smith"
        assert user.email == "alice@example.com"

    async def test_create_duplicate_email(self, sample_user):
        svc = UserService()
        with pytest.raises(ValidationError) as exc:
            await svc.create("Another User", sample_user["email"])
        assert exc.value.field == "email"

    async def test_create_invalid_email(self):
        svc = UserService()
        with pytest.raises(ValidationError) as exc:
            await svc.create("User", "not-an-email")
        assert exc.value.field == "email"

    async def test_create_name_too_short(self):
        svc = UserService()
        with pytest.raises(ValidationError) as exc:
            await svc.create("A", "valid@email.com")
        assert exc.value.field == "name"

    async def test_update_user(self, sample_user):
        svc = UserService()
        updated = await svc.update(sample_user["id"], name="New Name")
        assert updated.name == "New Name"

    async def test_update_nonexistent(self):
        svc = UserService()
        with pytest.raises(ValidationError):
            await svc.update(99999, name="X")

    async def test_delete_user(self, sample_user):
        svc = UserService()
        result = await svc.delete(sample_user["id"])
        assert result is True

    async def test_get_all(self, sample_users):
        svc = UserService()
        users = await svc.get_all()
        assert len(users) == 2

    async def test_email_normalised_to_lowercase(self):
        svc = UserService()
        user = await svc.create("Test", "TEST@EXAMPLE.COM")
        assert user.email == "test@example.com"
