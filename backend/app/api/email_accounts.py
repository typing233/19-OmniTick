from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.email_account import EmailAccount
from app.models.base import gen_id

router = APIRouter(prefix="/email-accounts", tags=["email-accounts"])


class EmailAccountCreate(BaseModel):
    name: str
    email_address: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    poll_interval_seconds: int = 60


class EmailAccountUpdate(BaseModel):
    name: Optional[str] = None
    email_address: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    poll_interval_seconds: Optional[int] = None


class EmailAccountOut(BaseModel):
    id: str
    name: str
    email_address: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    username: str
    is_active: bool
    poll_interval_seconds: int
    last_polled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[EmailAccountOut])
async def list_email_accounts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.tenant_id == tenant_id)
        .order_by(EmailAccount.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=EmailAccountOut, status_code=status.HTTP_201_CREATED)
async def create_email_account(
    body: EmailAccountCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    account = EmailAccount(
        id=gen_id(),
        name=body.name,
        email_address=body.email_address,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        smtp_host=body.smtp_host,
        smtp_port=body.smtp_port,
        username=body.username,
        password_encrypted=body.password,
        poll_interval_seconds=body.poll_interval_seconds,
        tenant_id=tenant_id,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.patch("/{account_id}", response_model=EmailAccountOut)
async def update_email_account(
    account_id: str,
    body: EmailAccountUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id, EmailAccount.tenant_id == tenant_id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    if body.name is not None:
        account.name = body.name
    if body.email_address is not None:
        account.email_address = body.email_address
    if body.imap_host is not None:
        account.imap_host = body.imap_host
    if body.imap_port is not None:
        account.imap_port = body.imap_port
    if body.smtp_host is not None:
        account.smtp_host = body.smtp_host
    if body.smtp_port is not None:
        account.smtp_port = body.smtp_port
    if body.username is not None:
        account.username = body.username
    if body.password is not None:
        account.password_encrypted = body.password
    if body.is_active is not None:
        account.is_active = body.is_active
    if body.poll_interval_seconds is not None:
        account.poll_interval_seconds = body.poll_interval_seconds

    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id, EmailAccount.tenant_id == tenant_id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    await db.delete(account)
    await db.commit()
