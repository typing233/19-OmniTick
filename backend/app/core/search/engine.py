import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, literal_column
from typing import Optional

import numpy as np

from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.kb import KBArticle, ArticleStatus, ArticleVisibility
from app.models.search import SearchIndexTicket, SearchIndexArticle, SearchSynonym
from app.models.base import gen_id
from app.schemas.search import SearchResultItem
from app.config import settings

logger = logging.getLogger(__name__)


async def get_embedding(text_content: str) -> list[float] | None:
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        truncated = text_content[:8000]
        response = await client.embeddings.create(
            input=truncated,
            model=settings.embedding_model,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


async def index_ticket(db: AsyncSession, ticket_id: str, tenant_id: str):
    msg_result = await db.execute(
        select(TicketMessage.body_text)
        .where(TicketMessage.ticket_id == ticket_id)
    )
    messages = [r[0] for r in msg_result.all() if r[0]]

    ticket_result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        return

    content = f"{ticket.subject} {' '.join(messages)}"

    embedding = await get_embedding(content)

    existing = await db.execute(
        select(SearchIndexTicket).where(SearchIndexTicket.ticket_id == ticket_id)
    )
    idx = existing.scalar_one_or_none()
    if idx:
        idx.content = content
        idx.embedding = embedding
    else:
        idx = SearchIndexTicket(
            id=gen_id(),
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            content=content,
            embedding=embedding,
        )
        db.add(idx)


async def index_article(db: AsyncSession, article_id: str, tenant_id: str):
    article_result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = article_result.scalar_one_or_none()
    if not article:
        return

    content = f"{article.title} {article.body_markdown or ''}"
    embedding = await get_embedding(content)

    existing = await db.execute(
        select(SearchIndexArticle).where(SearchIndexArticle.article_id == article_id)
    )
    idx = existing.scalar_one_or_none()
    if idx:
        idx.content = content
        idx.embedding = embedding
    else:
        idx = SearchIndexArticle(
            id=gen_id(),
            article_id=article_id,
            tenant_id=tenant_id,
            content=content,
            embedding=embedding,
        )
        db.add(idx)


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


async def search_tickets_semantic(
    db: AsyncSession, tenant_id: str, query_embedding: list[float],
    page_size: int, filters: Optional[dict] = None,
) -> list[SearchResultItem]:
    q = select(SearchIndexTicket).where(
        SearchIndexTicket.tenant_id == tenant_id,
        SearchIndexTicket.embedding.isnot(None),
    )
    result = await db.execute(q)
    indexes = result.scalars().all()

    scored = []
    for idx in indexes:
        if not idx.embedding:
            continue
        sim = cosine_similarity(query_embedding, idx.embedding)
        if sim > 0.3:
            scored.append((idx, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:page_size]

    items = []
    for idx, sim in scored:
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == idx.ticket_id))
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            continue
        if filters and filters.get("status") and ticket.status.value not in filters["status"]:
            continue

        snippet = (idx.content[:150] + "...") if len(idx.content) > 150 else idx.content
        items.append(SearchResultItem(
            type="ticket",
            id=ticket.id,
            title=ticket.subject,
            snippet=snippet,
            score=sim,
            metadata={"status": ticket.status.value, "priority": ticket.priority.value},
        ))
    return items


async def search_articles_semantic(
    db: AsyncSession, tenant_id: str, query_embedding: list[float],
    page_size: int, filters: Optional[dict] = None, public_only: bool = False,
) -> list[SearchResultItem]:
    q = select(SearchIndexArticle).where(
        SearchIndexArticle.tenant_id == tenant_id,
        SearchIndexArticle.embedding.isnot(None),
    )
    result = await db.execute(q)
    indexes = result.scalars().all()

    scored = []
    for idx in indexes:
        if not idx.embedding:
            continue
        sim = cosine_similarity(query_embedding, idx.embedding)
        if sim > 0.3:
            scored.append((idx, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:page_size]

    items = []
    for idx, sim in scored:
        article_result = await db.execute(select(KBArticle).where(KBArticle.id == idx.article_id))
        article = article_result.scalar_one_or_none()
        if not article:
            continue
        if public_only:
            if article.status != ArticleStatus.PUBLISHED or article.visibility != ArticleVisibility.PUBLIC:
                continue
        if filters and filters.get("category_id") and article.category_id != filters["category_id"]:
            continue

        snippet = (idx.content[:150] + "...") if len(idx.content) > 150 else idx.content
        items.append(SearchResultItem(
            type="article",
            id=article.id,
            title=article.title,
            snippet=snippet,
            score=sim,
            metadata={"status": article.status.value, "slug": article.slug},
        ))
    return items


def _merge_results(
    fulltext_items: list[SearchResultItem],
    semantic_items: list[SearchResultItem],
    page_size: int,
    fulltext_weight: float = 0.6,
    semantic_weight: float = 0.4,
) -> list[SearchResultItem]:
    seen: dict[str, SearchResultItem] = {}
    scores: dict[str, float] = {}

    ft_max = max((item.score for item in fulltext_items), default=1.0) or 1.0
    for item in fulltext_items:
        key = f"{item.type}:{item.id}"
        norm_score = item.score / ft_max
        seen[key] = item
        scores[key] = norm_score * fulltext_weight

    sem_max = max((item.score for item in semantic_items), default=1.0) or 1.0
    for item in semantic_items:
        key = f"{item.type}:{item.id}"
        norm_score = item.score / sem_max
        if key in scores:
            scores[key] += norm_score * semantic_weight
            if not seen[key].snippet and item.snippet:
                seen[key].snippet = item.snippet
        else:
            seen[key] = item
            scores[key] = norm_score * semantic_weight

    for key, item in seen.items():
        item.score = round(scores[key], 4)

    merged = sorted(seen.values(), key=lambda x: x.score, reverse=True)
    return merged[:page_size]


async def hybrid_search(
    db: AsyncSession, tenant_id: str, query: str,
    scope: str, page: int, page_size: int,
    filters: Optional[dict] = None, public_only: bool = False,
) -> tuple[list[SearchResultItem], int]:
    terms = await expand_synonyms(db, tenant_id, query)

    fulltext_items: list[SearchResultItem] = []
    semantic_items: list[SearchResultItem] = []
    total = 0

    # Full-text search
    if scope in ("all", "tickets") and not public_only:
        ticket_items, ticket_total = await search_tickets_fulltext(
            db, tenant_id, query, page, page_size, filters, terms
        )
        fulltext_items.extend(ticket_items)
        total += ticket_total

    if scope in ("all", "articles"):
        article_items, article_total = await search_articles_fulltext(
            db, tenant_id, query, page, page_size, filters, public_only, terms
        )
        fulltext_items.extend(article_items)
        total += article_total

    # Semantic search (if embeddings available)
    query_embedding = await get_embedding(query)
    if query_embedding:
        if scope in ("all", "tickets") and not public_only:
            sem_tickets = await search_tickets_semantic(
                db, tenant_id, query_embedding, page_size, filters
            )
            semantic_items.extend(sem_tickets)

        if scope in ("all", "articles"):
            sem_articles = await search_articles_semantic(
                db, tenant_id, query_embedding, page_size, filters, public_only
            )
            semantic_items.extend(sem_articles)

    # Merge results
    if semantic_items:
        merged = _merge_results(fulltext_items, semantic_items, page_size)
        total = max(total, len(merged))
        return merged, total
    else:
        fulltext_items.sort(key=lambda x: x.score, reverse=True)
        return fulltext_items[:page_size], total
