from typing import Optional
import asyncpg

from app.repositories.base_repository import BaseRepository
from app.models.user import User, CreateUserDTO, UpdateUserDTO


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    async def get_by_id(
        self, user_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[User]:
        query = """
            SELECT id, name, email, created_at, updated_at, deleted_at
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, user_id, conn=conn)
        return User.from_record(dict(record)) if record else None

    async def get_by_email(
        self, email: str, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[User]:
        query = """
            SELECT id, name, email, created_at, updated_at, deleted_at
            FROM users
            WHERE email = $1 AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, email, conn=conn)
        return User.from_record(dict(record)) if record else None

    async def get_all(
        self, conn: Optional[asyncpg.Connection] = None
    ) -> list[User]:
        query = """
            SELECT id, name, email, created_at, updated_at, deleted_at
            FROM users
            WHERE deleted_at IS NULL
            ORDER BY name ASC
        """
        records = await self.fetch_many(query, conn=conn)
        return [User.from_record(dict(r)) for r in records]

    async def create(
        self, dto: CreateUserDTO, conn: Optional[asyncpg.Connection] = None
    ) -> User:
        query = """
            INSERT INTO users (name, email)
            VALUES ($1, $2)
            RETURNING id, name, email, created_at, updated_at, deleted_at
        """
        record = await self.fetch_one(query, dto.name, dto.email, conn=conn)
        return User.from_record(dict(record))

    async def update(
        self, user_id: int, dto: UpdateUserDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[User]:
        fields = []
        values = []
        idx = 1

        if dto.name is not None:
            fields.append(f"name = ${idx}")
            values.append(dto.name)
            idx += 1
        if dto.email is not None:
            fields.append(f"email = ${idx}")
            values.append(dto.email)
            idx += 1

        if not fields:
            return await self.get_by_id(user_id, conn=conn)

        fields.append(f"updated_at = NOW()")
        values.append(user_id)

        query = f"""
            UPDATE users
            SET {', '.join(fields)}
            WHERE id = ${idx} AND deleted_at IS NULL
            RETURNING id, name, email, created_at, updated_at, deleted_at
        """
        record = await self.fetch_one(query, *values, conn=conn)
        return User.from_record(dict(record)) if record else None

    async def delete(
        self, user_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        return await self.soft_delete(user_id, conn=conn)
