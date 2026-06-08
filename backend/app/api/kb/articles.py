from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.kb import (
    KBArticle, KBArticleVersion, KBTag, KBReview, KBAuditLog,
    ArticleStatus, ArticleVisibility, kb_article_tags,
)
from app.models.base import gen_id
from app.schemas.kb import (
    KBArticleCreate, KBArticleUpdate, KBArticleOut, KBArticleListResponse,
    KBArticleListOut, KBVersionOut, KBRollbackRequest, KBReviewOut, KBReviewAction,
)

router = APIRouter(prefix="/kb/articles", tags=["knowledge-base"])


@router.get("", response_model=KBArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[str] = Query(None),
    tag_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    query = select(KBArticle).where(KBArticle.tenant_id == tenant_id)
    count_query = select(func.count(KBArticle.id)).where(KBArticle.tenant_id == tenant_id)

    if status_filter:
        query = query.where(KBArticle.status == ArticleStatus(status_filter))
        count_query = count_query.where(KBArticle.status == ArticleStatus(status_filter))
    if category_id:
        query = query.where(KBArticle.category_id == category_id)
        count_query = count_query.where(KBArticle.category_id == category_id)
    if tag_id:
        query = query.join(kb_article_tags).where(kb_article_tags.c.tag_id == tag_id)
        count_query = count_query.join(kb_article_tags).where(kb_article_tags.c.tag_id == tag_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(KBArticle.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().unique().all()

    return KBArticleListResponse(items=articles, total=total, page=page, page_size=page_size)


@router.post("", response_model=KBArticleOut, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: KBArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    article = KBArticle(
        id=gen_id(),
        tenant_id=tenant_id,
        author_id=current_user.id,
        title=body.title,
        slug=body.slug,
        body_markdown=body.body_markdown,
        body_html=body.body_html,
        category_id=body.category_id,
        visibility=ArticleVisibility(body.visibility),
        current_version=1,
    )
    db.add(article)

    version = KBArticleVersion(
        id=gen_id(),
        article_id=article.id,
        version_number=1,
        title=body.title,
        body_markdown=body.body_markdown,
        body_html=body.body_html,
        author_id=current_user.id,
        change_summary="Initial creation",
    )
    db.add(version)

    if body.tag_ids:
        tag_result = await db.execute(
            select(KBTag).where(KBTag.id.in_(body.tag_ids), KBTag.tenant_id == tenant_id)
        )
        article.tags = list(tag_result.scalars().all())

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="created",
    ))

    await db.commit()
    await db.refresh(article, ["tags", "category", "author"])
    return article


@router.get("/{article_id}", response_model=KBArticleOut)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle)
        .options(selectinload(KBArticle.tags))
        .where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=KBArticleOut)
async def update_article(
    article_id: str,
    body: KBArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle)
        .options(selectinload(KBArticle.tags))
        .where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    content_changed = False
    if body.title is not None and body.title != article.title:
        article.title = body.title
        content_changed = True
    if body.slug is not None:
        article.slug = body.slug
    if body.body_markdown is not None and body.body_markdown != article.body_markdown:
        article.body_markdown = body.body_markdown
        content_changed = True
    if body.body_html is not None:
        article.body_html = body.body_html
    if body.category_id is not None:
        article.category_id = body.category_id
    if body.visibility is not None:
        article.visibility = ArticleVisibility(body.visibility)
    if body.tag_ids is not None:
        tag_result = await db.execute(
            select(KBTag).where(KBTag.id.in_(body.tag_ids), KBTag.tenant_id == tenant_id)
        )
        article.tags = list(tag_result.scalars().all())

    if content_changed:
        article.current_version += 1
        version = KBArticleVersion(
            id=gen_id(),
            article_id=article.id,
            version_number=article.current_version,
            title=article.title,
            body_markdown=article.body_markdown,
            body_html=article.body_html,
            author_id=current_user.id,
            change_summary=body.change_summary,
        )
        db.add(version)

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="updated",
        detail=body.change_summary,
    ))

    await db.commit()
    await db.refresh(article, ["tags"])
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle).where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.status = ArticleStatus.ARCHIVED
    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="archived",
    ))
    await db.commit()


@router.get("/{article_id}/versions", response_model=list[KBVersionOut])
async def list_versions(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle).where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Article not found")

    versions = await db.execute(
        select(KBArticleVersion)
        .where(KBArticleVersion.article_id == article_id)
        .order_by(KBArticleVersion.version_number.desc())
    )
    return versions.scalars().all()


@router.get("/{article_id}/versions/{version_number}", response_model=KBVersionOut)
async def get_version(
    article_id: str,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticleVersion).where(
            KBArticleVersion.article_id == article_id,
            KBArticleVersion.version_number == version_number,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/{article_id}/rollback", response_model=KBArticleOut)
async def rollback_article(
    article_id: str,
    body: KBRollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle)
        .options(selectinload(KBArticle.tags))
        .where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    target = await db.execute(
        select(KBArticleVersion).where(
            KBArticleVersion.article_id == article_id,
            KBArticleVersion.version_number == body.version_number,
        )
    )
    target_version = target.scalar_one_or_none()
    if not target_version:
        raise HTTPException(status_code=404, detail="Target version not found")

    article.title = target_version.title
    article.body_markdown = target_version.body_markdown
    article.body_html = target_version.body_html
    article.current_version += 1

    new_version = KBArticleVersion(
        id=gen_id(),
        article_id=article.id,
        version_number=article.current_version,
        title=article.title,
        body_markdown=article.body_markdown,
        body_html=article.body_html,
        author_id=current_user.id,
        change_summary=f"Rollback to version {body.version_number}",
    )
    db.add(new_version)

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="rollback",
        detail=f"Rolled back to version {body.version_number}",
    ))

    await db.commit()
    await db.refresh(article, ["tags"])
    return article


@router.post("/{article_id}/submit-review", response_model=KBReviewOut)
async def submit_for_review(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle).where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status not in (ArticleStatus.DRAFT, ArticleStatus.ARCHIVED):
        raise HTTPException(status_code=400, detail="Article must be in draft to submit for review")

    article.status = ArticleStatus.IN_REVIEW

    review = KBReview(
        id=gen_id(),
        article_id=article.id,
        version_number=article.current_version,
        status="pending",
    )
    db.add(review)

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="submitted_for_review",
    ))

    await db.commit()
    await db.refresh(review)
    return review


@router.post("/{article_id}/approve", response_model=KBArticleOut)
async def approve_article(
    article_id: str,
    body: KBReviewAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle)
        .options(selectinload(KBArticle.tags))
        .where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status != ArticleStatus.IN_REVIEW:
        raise HTTPException(status_code=400, detail="Article is not in review")

    article.status = ArticleStatus.PUBLISHED
    article.published_at = datetime.now(timezone.utc)

    review_result = await db.execute(
        select(KBReview).where(
            KBReview.article_id == article_id, KBReview.status == "pending"
        ).order_by(KBReview.created_at.desc()).limit(1)
    )
    review = review_result.scalar_one_or_none()
    if review:
        review.status = "approved"
        review.reviewer_id = current_user.id
        review.comment = body.comment
        review.resolved_at = datetime.now(timezone.utc)

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="approved",
        detail=body.comment,
    ))

    await db.commit()
    await db.refresh(article, ["tags"])
    return article


@router.post("/{article_id}/reject", response_model=KBArticleOut)
async def reject_article(
    article_id: str,
    body: KBReviewAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBArticle)
        .options(selectinload(KBArticle.tags))
        .where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status != ArticleStatus.IN_REVIEW:
        raise HTTPException(status_code=400, detail="Article is not in review")

    article.status = ArticleStatus.DRAFT

    review_result = await db.execute(
        select(KBReview).where(
            KBReview.article_id == article_id, KBReview.status == "pending"
        ).order_by(KBReview.created_at.desc()).limit(1)
    )
    review = review_result.scalar_one_or_none()
    if review:
        review.status = "rejected"
        review.reviewer_id = current_user.id
        review.comment = body.comment
        review.resolved_at = datetime.now(timezone.utc)

    db.add(KBAuditLog(
        id=gen_id(),
        tenant_id=tenant_id,
        article_id=article.id,
        actor_id=current_user.id,
        action="rejected",
        detail=body.comment,
    ))

    await db.commit()
    await db.refresh(article, ["tags"])
    return article


@router.get("/reviews/pending", response_model=list[KBReviewOut])
async def list_pending_reviews(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(KBReview)
        .join(KBArticle)
        .where(KBArticle.tenant_id == tenant_id, KBReview.status == "pending")
        .order_by(KBReview.created_at)
    )
    return result.scalars().all()
