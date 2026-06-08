"""Seed script to create initial admin user and run migrations."""
import asyncio

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.user import User
from app.models.base import gen_id
from app.core import hash_password


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


async def seed_admin():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "admin@omnitick.local"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            id=gen_id(),
            email="admin@omnitick.local",
            display_name="Admin",
            password_hash=hash_password("admin123"),
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user created: admin@omnitick.local / admin123")


async def main():
    await init_db()
    await seed_admin()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
