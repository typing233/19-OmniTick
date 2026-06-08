"""Seed script to create initial admin user and run migrations."""
import asyncio

from sqlalchemy import select
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.user_role import UserRole, RoleType
from app.models.base import gen_id
from app.core import hash_password

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


async def seed_tenant():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.id == DEFAULT_TENANT_ID))
        if result.scalar_one_or_none():
            print("Default tenant already exists.")
            return
        tenant = Tenant(
            id=DEFAULT_TENANT_ID,
            name="Default",
            slug="default",
        )
        db.add(tenant)
        await db.commit()
        print(f"Default tenant created: {DEFAULT_TENANT_ID}")


async def seed_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@omnitick.local"))
        existing = result.scalar_one_or_none()
        if existing:
            if not existing.tenant_id:
                existing.tenant_id = DEFAULT_TENANT_ID
                await db.commit()
            role_result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == existing.id,
                    UserRole.tenant_id == DEFAULT_TENANT_ID,
                )
            )
            if not role_result.scalar_one_or_none():
                db.add(UserRole(
                    id=gen_id(),
                    user_id=existing.id,
                    tenant_id=DEFAULT_TENANT_ID,
                    role=RoleType.ADMIN,
                ))
                await db.commit()
            print("Admin user already exists.")
            return

        admin = User(
            id=gen_id(),
            email="admin@omnitick.local",
            display_name="Admin",
            password_hash=hash_password("admin123"),
            tenant_id=DEFAULT_TENANT_ID,
        )
        db.add(admin)
        await db.flush()

        role = UserRole(
            id=gen_id(),
            user_id=admin.id,
            tenant_id=DEFAULT_TENANT_ID,
            role=RoleType.ADMIN,
        )
        db.add(role)
        await db.commit()
        print(f"Admin user created: admin@omnitick.local / admin123")


async def main():
    await init_db()
    await seed_tenant()
    await seed_admin()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
