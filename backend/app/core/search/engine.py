from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import Optional

from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.kb import KBArticle, ArticleStatus
from app.models.search import SearchIndexTicket, SearchIndexArticle, SearchSynonym
from app.models.base import gen_id
from app.schemas.search import SearchResultItem


async def expand_synonyms(db: AsyncSession, tenant_id: str, query: str) -> str:
    words = query.split()
    result = await db.execute(
        select(SearchSynonym).where(
            SearchSynonym.tenant_id == tenant_id,
            SearchSynonym.word.in_(words),
        )
    )
    synonym_map = {s.word: s.synonyms.split(",") for s in result.scalars().all()}

    expanded = []
    for word in words:
        expanded.append(word)
        if word in synonym_map:
            expanded.extend(synonym_map[word])
    return " | ".join(expanded)


def highlight_snippet(text_content: str, query: str, max_length: int = 200) -> str:
    query_words = query.lower().split()
    if not text_content:
        return ""

    best_pos = 0
    for word in query_words:
        pos = text_content.lower().find(word)
        if pos >= 0:
            best_pos = max(0, pos - 50)
            break

    snippet = text_content[best_pos:best_pos + max_length]
    for word in query_words:
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        snippet = pattern.sub(f"<mark>{word}</mark>", snippet)

    if best_pos > 0:
        snippet = "..." + snippet
    if best_pos + max_length < len(text_content):
        snippet = snippet + "..."
    return snippet


async def search_tickets_fulltext(
    db: AsyncSession, tenant_id: str, query: str, page: int, page_size: int,
    filters: Optional[dict] = None,
) -> tuple[list[SearchResultItem], int]:
    like_pattern = f"%{query}%"

    count_q = (
        select(func.count(Ticket.id))
        .where(Ticket.tenant_id == tenant_id)
        .where(
            (Ticket.subject.ilike(like_pattern)) |
            Ticket.id.in_(
                select(TicketMessage.ticket_id)
                .where(TicketMessage.body_text.ilike(like_pattern))
            )
        )
    )

    if filters:
        if filters.get("status"):
            count_q = count_q.where(Ticket.status.in_(filters["status"]))

    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(Ticket)
        .where(Ticket.tenant_id == tenant_id)
        .where(
            (Ticket.subject.ilike(like_pattern)) |
            Ticket.id.in_(
                select(TicketMessage.ticket_id)
                .where(TicketMessage.body_text.ilike(like_pattern))
            )
        )
        .order_by(Ticket.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if filters:
        if filters.get("status"):
            q = q.where(Ticket.status.in_(filters["status"]))

    result = await db.execute(q)
    tickets = result.scalars().all()

    items = []
    for ticket in tickets:
        snippet = highlight_snippet(ticket.subject, query)
        items.append(SearchResultItem(
            type="ticket",
            id=ticket.id,
            title=ticket.subject,
            snippet=snippet,
            score=1.0,
            metadata={"status": ticket.status.value, "priority": ticket.priority.value},
        ))
    return items, total


async def search_articles_fulltext(
    db: AsyncSession, tenant_id: str, query: str, page: int, page_size: int,
    filters: Optional[dict] = None, public_only: bool = False,
) -> tuple[list[SearchResultItem], int]:
    like_pattern = f"%{query}%"

    base_filter = [KBArticle.tenant_id == tenant_id]
    if public_only:
        base_filter.append(KBArticle.status == ArticleStatus.PUBLISHED)
        base_filter.append(KBArticle.visibility == "public")

    content_filter = (
        (KBArticle.title.ilike(like_pattern)) |
        (KBArticle.body_markdown.ilike(like_pattern))
    )

    count_q = select(func.count(KBArticle.id)).where(*base_filter).where(content_filter)
    if filters and filters.get("category_id"):
        count_q = count_q.where(KBArticle.category_id == filters["category_id"])

    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(KBArticle)
        .where(*base_filter)
        .where(content_filter)
        .order_by(KBArticle.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if filters and filters.get("category_id"):
        q = q.where(KBArticle.category_id == filters["category_id"])

    result = await db.execute(q)
    articles = result.scalars().all()

    items = []
    for article in articles:
        snippet = highlight_snippet(article.body_markdown, query)
        items.append(SearchResultItem(
            type="article",
            id=article.id,
            title=article.title,
            snippet=snippet,
            score=1.0,
            metadata={"status": article.status.value, "slug": article.slug},
        ))
    return items, total


async def hybrid_search(
    db: AsyncSession, tenant_id: str, query: str,
    scope: str, page: int, page_size: int,
    filters: Optional[dict] = None, public_only: bool = False,
) -> tuple[list[SearchResultItem], int]:
    expanded_query = await expand_synonyms(db, tenant_id, query)
    all_items: list[SearchResultItem] = []
    total = 0

    if scope in ("all", "tickets") and not public_only:
        ticket_items, ticket_total = await search_tickets_fulltext(
            db, tenant_id, expanded_query.split("|")[0].strip(), page, page_size, filters
        )
        all_items.extend(ticket_items)
        total += ticket_total

    if scope in ("all", "articles"):
        article_items, article_total = await search_articles_fulltext(
            db, tenant_id, expanded_query.split("|")[0].strip(), page, page_size, filters, public_only
        )
        all_items.extend(article_items)
        total += article_total

    all_items.sort(key=lambda x: x.score, reverse=True)
    return all_items[:page_size], total
