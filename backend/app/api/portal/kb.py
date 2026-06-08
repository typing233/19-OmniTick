from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_customer, get_portal_tenant_id
from app.models.customer import Customer
from app.models.kb import KBArticle, KBCategory, ArticleStatus, ArticleVisibility
from app.schemas.portal import PortalArticleOut, PortalArticleListResponse
from app.schemas.kb import KBCategoryTree, KBCategoryOut
from app.schemas.search import SearchRequest, SearchResponse
from app.core.search.engine import hybrid_search

router = APIRouter(prefix="/portal/kb", tags=["portal-kb"])


@router.get("/articles", response_model=PortalArticleListResponse)
async def list_published_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    base = [
        KBArticle.tenant_id == tenant_id,
        KBArticle.status == ArticleStatus.PUBLISHED,
        KBArticle.visibility == ArticleVisibility.PUBLIC,
    ]
    if category_id:
        base.append(KBArticle.category_id == category_id)

    count_q = select(func.count(KBArticle.id)).where(*base)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(KBArticle)
        .where(*base)
        .order_by(KBArticle.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(q)
    articles = result.scalars().all()

    return PortalArticleListResponse(items=articles, total=total, page=page, page_size=page_size)


@router.get("/articles/{slug}", response_model=PortalArticleOut)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    result = await db.execute(
        select(KBArticle).where(
            KBArticle.tenant_id == tenant_id,
            KBArticle.slug == slug,
            KBArticle.status == ArticleStatus.PUBLISHED,
            KBArticle.visibility == ArticleVisibility.PUBLIC,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/categories", response_model=list[KBCategoryTree])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
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


@router.post("/search", response_model=SearchResponse)
async def portal_search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    items, total = await hybrid_search(
        db=db,
        tenant_id=tenant_id,
        query=body.query,
        scope="articles",
        page=body.page,
        page_size=body.page_size,
        filters=body.filters,
        public_only=True,
    )
    return SearchResponse(items=items, total=total, page=body.page, page_size=body.page_size)
