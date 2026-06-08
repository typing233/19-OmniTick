from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.kb import KBCategory
from app.models.base import gen_id
from app.schemas.kb import KBCategoryCreate, KBCategoryUpdate, KBCategoryOut, KBCategoryTree

router = APIRouter(prefix="/kb/categories", tags=["knowledge-base"])


@router.get("", response_model=list[KBCategoryTree])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBCategory)
        .where(KBCategory.tenant_id == tenant_id)
        .order_by(KBCategory.sort_order, KBCategory.name)
    )
    all_cats = result.scalars().all()

    cat_map = {c.id: KBCategoryTree.model_validate(c) for c in all_cats}
    roots = []
    for cat in cat_map.values():
        if cat.parent_id and cat.parent_id in cat_map:
            cat_map[cat.parent_id].children.append(cat)
        else:
            roots.append(cat)
    return roots


@router.post("", response_model=KBCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: KBCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    category = KBCategory(
        id=gen_id(),
        tenant_id=tenant_id,
        name=body.name,
        slug=body.slug,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=KBCategoryOut)
async def update_category(
    category_id: str,
    body: KBCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBCategory).where(
            KBCategory.id == category_id, KBCategory.tenant_id == tenant_id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if body.name is not None:
        category.name = body.name
    if body.slug is not None:
        category.slug = body.slug
    if body.parent_id is not None:
        category.parent_id = body.parent_id
    if body.sort_order is not None:
        category.sort_order = body.sort_order

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBCategory).where(
            KBCategory.id == category_id, KBCategory.tenant_id == tenant_id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()
