"""
Seed script: inserts default users and categories if they don't exist.
Run via: python -m scripts.seed
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from sqlalchemy import select, func


DEFAULT_CATEGORIES = [
    {"name": "Other", "color": "#9E9E9E", "icon": "circle", "is_default": True},
    {"name": "Food & Groceries", "color": "#4CAF50", "icon": "shopping-cart"},
    {"name": "Housing & Rent", "color": "#2196F3", "icon": "home"},
    {"name": "Transport", "color": "#FF9800", "icon": "car"},
    {"name": "Healthcare", "color": "#F44336", "icon": "heart"},
    {"name": "Entertainment", "color": "#9C27B0", "icon": "film"},
    {"name": "Utilities", "color": "#00BCD4", "icon": "zap"},
    {"name": "Education", "color": "#3F51B5", "icon": "book"},
    {"name": "Clothing", "color": "#E91E63", "icon": "tag"},
    {"name": "Salary", "color": "#8BC34A", "icon": "briefcase"},
    {"name": "Savings", "color": "#607D8B", "icon": "piggy-bank"},
    {"name": "Travel", "color": "#FF5722", "icon": "plane"},
]


async def seed(db: AsyncSession) -> None:
    # ── Default users ──────────────────────────────────────────────────────────
    users_to_create = [
        {
            "name": settings.DEFAULT_USER1_NAME,
            "email": settings.DEFAULT_USER1_EMAIL,
            "password": settings.DEFAULT_USER1_PASSWORD,
        },
        {
            "name": settings.DEFAULT_USER2_NAME,
            "email": settings.DEFAULT_USER2_EMAIL,
            "password": settings.DEFAULT_USER2_PASSWORD,
        },
    ]

    for u in users_to_create:
        result = await db.execute(select(User).where(User.email == u["email"]))
        existing = result.scalar_one_or_none()
        if not existing:
            user = User(
                name=u["name"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
            )
            db.add(user)
            print(f"  ✓ Created user: {u['email']}")
        else:
            print(f"  · User already exists: {u['email']}")

    # ── Default categories (only if table is empty) ────────────────────────────
    cat_count = await db.scalar(select(func.count()).select_from(Category))
    if cat_count == 0:
        for cat_data in DEFAULT_CATEGORIES:
            db.add(Category(**cat_data))
            print(f"  ✓ Created category: {cat_data['name']}")
    else:
        print(f"  · Categories already exist ({cat_count}), skipping.")

    await db.commit()
    print("\n✅ Seed complete.")


async def main():
    print("🌱 Running database seed...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
