from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.api.labels import router as labels_router
from app.api.users import router as users_router
from app.api.email_accounts import router as email_accounts_router
from app.api.search import router as search_router
from app.api.kb.articles import router as kb_articles_router
from app.api.kb.categories import router as kb_categories_router
from app.api.kb.tags import router as kb_tags_router
from app.api.portal.auth import router as portal_auth_router
from app.api.portal.tickets import router as portal_tickets_router
from app.api.portal.kb import router as portal_kb_router
from app.api.automation.rules import router as automation_rules_router
from app.api.automation.sla import router as automation_sla_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(tickets_router)
api_router.include_router(labels_router)
api_router.include_router(users_router)
api_router.include_router(email_accounts_router)
api_router.include_router(search_router)
api_router.include_router(kb_articles_router)
api_router.include_router(kb_categories_router)
api_router.include_router(kb_tags_router)
api_router.include_router(portal_auth_router)
api_router.include_router(portal_tickets_router)
api_router.include_router(portal_kb_router)
api_router.include_router(automation_rules_router)
api_router.include_router(automation_sla_router)
