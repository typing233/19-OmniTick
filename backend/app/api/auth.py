from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.user_role import UserRole
from app.core import verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    role_result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.tenant_id == user.tenant_id,
        )
    )
    user_role = role_result.scalar_one_or_none()
    role_str = user_role.role.value if user_role else "agent"

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=role_str,
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
