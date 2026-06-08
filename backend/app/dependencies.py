from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Callable

from app.database import get_db
from app.core import decode_access_token
from app.models.user import User
from app.models.customer import Customer
from app.models.user_role import UserRole, RoleType

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials, audience="agent")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user._tenant_id = payload.get("tenant_id")
    user._role = payload.get("role")
    return user


def get_tenant_id(user: User = Depends(get_current_user)) -> str:
    tenant_id = getattr(user, "_tenant_id", None) or user.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    return tenant_id


def require_role(*allowed_roles: RoleType) -> Callable:
    async def checker(user: User = Depends(get_current_user)) -> User:
        role_str = getattr(user, "_role", None)
        if not role_str or RoleType(role_str) not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return checker


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    payload = decode_access_token(credentials.credentials, audience="portal")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    customer_id = payload.get("sub")
    if not customer_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")
    customer._tenant_id = payload.get("tenant_id")
    return customer


def get_portal_tenant_id(customer: Customer = Depends(get_current_customer)) -> str:
    return getattr(customer, "_tenant_id", None) or customer.tenant_id
