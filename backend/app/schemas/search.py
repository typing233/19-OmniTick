from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    query: str
    scope: str = "all"  # all, tickets, articles
    mode: str = "fulltext"  # fulltext, semantic, hybrid
    page: int = 1
    page_size: int = 20
    filters: Optional[dict] = None


class SearchResultItem(BaseModel):
    type: str  # ticket, article
    id: str
    title: str
    snippet: str
    score: float
    metadata: dict = {}

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
