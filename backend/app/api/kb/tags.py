from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.kb import KBTag
from app.models.base import gen_id
from app.schemas.kb import KBTagCreate, KBTagOut

router = APIRouter(prefix="/kb/tags", tags=["knowledge-base"])


@router.get("", response_model=list[KBTagOut])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBTag).where(KBTag.tenant_id == tenant_id).order_by(KBTag.name)
    )
    return result.scalars().all()


@router.post("", response_model=KBTagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: KBTagCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    existing = await db.execute(
        select(KBTag).where(KBTag.name == body.name, KBTag.tenant_id == tenant_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = KBTag(id=gen_id(), tenant_id=tenant_id, name=body.name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBTag).where(KBTag.id == tag_id, KBTag.tenant_id == tenant_id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.commit()
