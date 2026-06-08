from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, literal_column
from typing import Optional

from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.kb import KBArticle, ArticleStatus, ArticleVisibility
from app.models.search import SearchSynonym
from app.schemas.search import SearchResultItem


async def expand_synonyms(db: AsyncSession, tenant_id: str, query: str) -> list[str]:
    words = query.lower().split()
    result = await db.execute(
        select(SearchSynonym).where(
            SearchSynonym.tenant_id == tenant_id,
            SearchSynonym.word.in_(words),
        )
    )
    synonym_map = {s.word: s.synonyms.split(",") for s in result.scalars().all()}

    all_terms = list(words)
    for word in words:
        if word in synonym_map:
            all_terms.extend(synonym_map[word])
    return all_terms


def build_tsquery(terms: list[str]) -> str:
    sanitized = []
    for t in terms:
        clean = "".join(c for c in t.strip() if c.isalnum() or c == '_')
        if clean:
            sanitized.append(clean)
    if not sanitized:
        return ""
    return " | ".join(sanitized)


async def search_tickets_fulltext(
    db: AsyncSession, tenant_id: str, query: str, page: int, page_size: int,
    filters: Optional[dict] = None, terms: Optional[list[str]] = None,
) -> tuple[list[SearchResultItem], int]:
    if terms is None:
        terms = query.lower().split()
    tsquery_str = build_tsquery(terms)
    if not tsquery_str:
        return [], 0

    msg_subq = (
        select(
            TicketMessage.ticket_id,
            func.string_agg(TicketMessage.body_text, literal_column("' '")).label("msg_text")
        )
        .group_by(TicketMessage.ticket_id)
        .subquery()
    )

    ts_vector = func.to_tsvector(
        literal_column("'simple'"),
        func.coalesce(Ticket.subject, literal_column("''")) +
        literal_column("' '") +
        func.coalesce(msg_subq.c.msg_text, literal_column("''"))
    )
    ts_query = func.to_tsquery(literal_column("'simple'"), text(f"'{tsquery_str}'"))

    base_q = (
        select(Ticket, func.ts_rank(ts_vector, ts_query).label("rank"))
        .outerjoin(msg_subq, Ticket.id == msg_subq.c.ticket_id)
        .where(Ticket.tenant_id == tenant_id)
        .where(ts_vector.op("@@")(ts_query))
    )

    if filters:
        if filters.get("status"):
            base_q = base_q.where(Ticket.status.in_(filters["status"]))

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    data_q = (
        base_q
        .order_by(text("rank DESC"))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(data_q)
    rows = result.all()

    items = []
    for row in rows:
        ticket = row[0]
        rank = float(row[1])

        headline_q = select(
            func.ts_headline(
                literal_column("'simple'"),
                func.coalesce(Ticket.subject, literal_column("''")),
                ts_query,
                literal_column("'StartSel=<mark>, StopSel=</mark>, MaxFragments=1, MaxWords=30'")
            )
        ).where(Ticket.id == ticket.id)
        hl_result = await db.execute(headline_q)
        snippet = hl_result.scalar() or ticket.subject

        items.append(SearchResultItem(
            type="ticket",
            id=ticket.id,
            title=ticket.subject,
            snippet=snippet,
            score=rank,
            metadata={"status": ticket.status.value, "priority": ticket.priority.value},
        ))
    return items, total


async def search_articles_fulltext(
    db: AsyncSession, tenant_id: str, query: str, page: int, page_size: int,
    filters: Optional[dict] = None, public_only: bool = False, terms: Optional[list[str]] = None,
) -> tuple[list[SearchResultItem], int]:
    if terms is None:
        terms = query.lower().split()
    tsquery_str = build_tsquery(terms)
    if not tsquery_str:
        return [], 0

    ts_vector = func.to_tsvector(
        literal_column("'simple'"),
        func.coalesce(KBArticle.title, literal_column("''")) +
        literal_column("' '") +
        func.coalesce(KBArticle.body_markdown, literal_column("''"))
    )
    ts_query = func.to_tsquery(literal_column("'simple'"), text(f"'{tsquery_str}'"))

    base_q = (
        select(KBArticle, func.ts_rank(ts_vector, ts_query).label("rank"))
        .where(KBArticle.tenant_id == tenant_id)
        .where(ts_vector.op("@@")(ts_query))
    )

    if public_only:
        base_q = base_q.where(KBArticle.status == ArticleStatus.PUBLISHED)
        base_q = base_q.where(KBArticle.visibility == ArticleVisibility.PUBLIC)

    if filters and filters.get("category_id"):
        base_q = base_q.where(KBArticle.category_id == filters["category_id"])

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    data_q = (
        base_q
        .order_by(text("rank DESC"))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(data_q)
    rows = result.all()

    items = []
    for row in rows:
        article = row[0]
        rank = float(row[1])

        headline_q = select(
            func.ts_headline(
                literal_column("'simple'"),
                func.coalesce(KBArticle.body_markdown, literal_column("''")),
                ts_query,
                literal_column("'StartSel=<mark>, StopSel=</mark>, MaxFragments=2, MaxWords=40'")
            )
        ).where(KBArticle.id == article.id)
        hl_result = await db.execute(headline_q)
        snippet = hl_result.scalar() or ""

        items.append(SearchResultItem(
            type="article",
            id=article.id,
            title=article.title,
            snippet=snippet,
            score=rank,
            metadata={"status": article.status.value, "slug": article.slug},
        ))
    return items, total


async def hybrid_search(
    db: AsyncSession, tenant_id: str, query: str,
    scope: str, page: int, page_size: int,
    filters: Optional[dict] = None, public_only: bool = False,
) -> tuple[list[SearchResultItem], int]:
    terms = await expand_synonyms(db, tenant_id, query)
    all_items: list[SearchResultItem] = []
    total = 0

    if scope in ("all", "tickets") and not public_only:
        ticket_items, ticket_total = await search_tickets_fulltext(
            db, tenant_id, query, page, page_size, filters, terms
        )
        all_items.extend(ticket_items)
        total += ticket_total

    if scope in ("all", "articles"):
        article_items, article_total = await search_articles_fulltext(
            db, tenant_id, query, page, page_size, filters, public_only, terms
        )
        all_items.extend(article_items)
        total += article_total

    all_items.sort(key=lambda x: x.score, reverse=True)
    return all_items[:page_size], total
