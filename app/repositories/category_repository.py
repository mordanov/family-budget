from typing import Optional
import asyncpg

from app.repositories.base_repository import BaseRepository
from app.models.category import Category, CreateCategoryDTO, UpdateCategoryDTO


class CategoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("categories")

    async def get_by_id(
        self, category_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Category]:
        query = """
            SELECT id, name, description, color, icon, created_by,
                   created_at, updated_at, deleted_at
            FROM categories
            WHERE id = $1 AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, category_id, conn=conn)
        return Category.from_record(dict(record)) if record else None

    async def get_all(
        self, conn: Optional[asyncpg.Connection] = None
    ) -> list[Category]:
        query = """
            SELECT id, name, description, color, icon, created_by,
                   created_at, updated_at, deleted_at
            FROM categories
            WHERE deleted_at IS NULL
            ORDER BY name ASC
        """
        records = await self.fetch_many(query, conn=conn)
        return [Category.from_record(dict(r)) for r in records]

    async def get_by_name(
        self, name: str, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Category]:
        query = """
            SELECT id, name, description, color, icon, created_by,
                   created_at, updated_at, deleted_at
            FROM categories
            WHERE LOWER(name) = LOWER($1) AND deleted_at IS NULL
        """
        record = await self.fetch_one(query, name, conn=conn)
        return Category.from_record(dict(record)) if record else None

    async def create(
        self, dto: CreateCategoryDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Category:
        query = """
            INSERT INTO categories (name, description, color, icon, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, description, color, icon, created_by,
                      created_at, updated_at, deleted_at
        """
        record = await self.fetch_one(
            query, dto.name, dto.description, dto.color, dto.icon, dto.created_by,
            conn=conn
        )
        return Category.from_record(dict(record))

    async def update(
        self, category_id: int, dto: UpdateCategoryDTO, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Category]:
        fields = []
        values = []
        idx = 1

        if dto.name is not None:
            fields.append(f"name = ${idx}")
            values.append(dto.name)
            idx += 1
        if dto.description is not None:
            fields.append(f"description = ${idx}")
            values.append(dto.description)
            idx += 1
        if dto.color is not None:
            fields.append(f"color = ${idx}")
            values.append(dto.color)
            idx += 1
        if dto.icon is not None:
            fields.append(f"icon = ${idx}")
            values.append(dto.icon)
            idx += 1

        if not fields:
            return await self.get_by_id(category_id, conn=conn)

        fields.append("updated_at = NOW()")
        values.append(category_id)

        query = f"""
            UPDATE categories
            SET {', '.join(fields)}
            WHERE id = ${idx} AND deleted_at IS NULL
            RETURNING id, name, description, color, icon, created_by,
                      created_at, updated_at, deleted_at
        """
        record = await self.fetch_one(query, *values, conn=conn)
        return Category.from_record(dict(record)) if record else None

    async def delete(
        self, category_id: int, conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        return await self.soft_delete(category_id, conn=conn)
