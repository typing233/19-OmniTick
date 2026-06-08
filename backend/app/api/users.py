from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.user_role import UserRole, RoleType
from app.models.base import gen_id
from app.core import hash_password
from app.schemas.user import UserOut, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(User).where(User.is_active == True, User.tenant_id == tenant_id)
        .order_by(User.display_name)
    )
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=gen_id(),
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        tenant_id=tenant_id,
    )
    db.add(user)

    role = UserRole(
        id=gen_id(),
        user_id=user.id,
        tenant_id=tenant_id,
        role=RoleType.AGENT,
    )
    db.add(role)

    await db.commit()
    await db.refresh(user)
    return user
