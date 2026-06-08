from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.core.search.engine import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def unified_search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    items, total = await hybrid_search(
        db=db,
        tenant_id=tenant_id,
        query=body.query,
        scope=body.scope,
        page=body.page,
        page_size=body.page_size,
        filters=body.filters,
    )
    return SearchResponse(items=items, total=total, page=body.page, page_size=body.page_size)
