import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.automation import SlaTimer, SlaPolicy, TriggerEvent
from app.models.ticket import Ticket
from app.core.automation.engine import run_automation

logger = logging.getLogger(__name__)


class SlaScheduler:
    def __init__(self, interval: int = 60):
        self.interval = interval
        self._task: asyncio.Task | None = None

    async def start(self):
        self._task = asyncio.create_task(self._run())
        logger.info("SLA scheduler started")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SLA scheduler stopped")

    async def _run(self):
        while True:
            try:
                await self._check_breaches()
            except Exception as e:
                logger.error(f"SLA check error: {e}")
            await asyncio.sleep(self.interval)

    async def _check_breaches(self):
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SlaTimer)
                .where(
                    SlaTimer.breached == False,
                    (
                        (SlaTimer.response_due_at < now) & (SlaTimer.response_met.is_(None))
                    ) | (
                        (SlaTimer.resolution_due_at < now) & (SlaTimer.resolution_met.is_(None))
                    )
                )
            )
            timers = result.scalars().all()

            for timer in timers:
                timer.breached = True
                ticket_result = await db.execute(
                    select(Ticket)
                    .options(selectinload(Ticket.labels))
                    .where(Ticket.id == timer.ticket_id)
                )
                ticket = ticket_result.scalar_one_or_none()
                if ticket:
                    await run_automation(
                        db=db,
                        ticket=ticket,
                        trigger_event=TriggerEvent.ON_SLA_BREACH,
                        tenant_id=ticket.tenant_id,
                    )

            if timers:
                await db.commit()
                logger.info(f"Processed {len(timers)} SLA breaches")
