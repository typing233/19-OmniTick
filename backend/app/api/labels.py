from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.label import Label
from app.models.base import gen_id
from app.schemas.label import LabelCreate, LabelUpdate, LabelOut

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("", response_model=list[LabelOut])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Label).order_by(Label.name))
    return result.scalars().all()


@router.post("", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
async def create_label(
    body: LabelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    existing = await db.execute(select(Label).where(Label.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Label already exists")

    label = Label(id=gen_id(), name=body.name, color=body.color)
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


@router.patch("/{label_id}", response_model=LabelOut)
async def update_label(
    label_id: str,
    body: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    if body.name is not None:
        label.name = body.name
    if body.color is not None:
        label.color = body.color

    await db.commit()
    await db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    await db.delete(label)
    await db.commit()
