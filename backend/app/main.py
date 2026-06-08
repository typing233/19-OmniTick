import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.api.router import api_router
from app.core.email.imap_poller import ImapPoller
from app.core.automation.scheduler import SlaScheduler

logger = logging.getLogger(__name__)

poller = ImapPoller()
sla_scheduler = SlaScheduler(interval=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connected")
    await poller.start()
    await sla_scheduler.start()
    yield
    await sla_scheduler.stop()
    await poller.stop()
    await engine.dispose()


app = FastAPI(title="OmniTick", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
