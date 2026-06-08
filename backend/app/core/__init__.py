from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: str,
    tenant_id: str | None = None,
    role: str | None = None,
    audience: str = "agent",
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload: dict = {"sub": user_id, "exp": expire, "aud": audience}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, audience: str = "agent") -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=audience,
        )
        return payload
    except JWTError:
        return None


def create_customer_token(customer_id: str, tenant_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": customer_id,
        "tenant_id": tenant_id,
        "aud": "portal",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
