from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.models.automation import AutomationRule, AutomationExecutionLog, TriggerEvent
from app.models.base import gen_id
from app.schemas.automation import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleOut,
    AutomationLogOut, AutomationLogListResponse,
)

router = APIRouter(prefix="/automation/rules", tags=["automation"])


@router.get("", response_model=list[AutomationRuleOut])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(AutomationRule)
        .where(AutomationRule.tenant_id == tenant_id)
        .order_by(AutomationRule.priority, AutomationRule.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=AutomationRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    rule = AutomationRule(
        id=gen_id(),
        tenant_id=tenant_id,
        name=body.name,
        description=body.description,
        trigger_event=TriggerEvent(body.trigger_event),
        conditions=body.conditions,
        actions=body.actions,
        priority=body.priority,
        is_active=body.is_active,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=AutomationRuleOut)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id, AutomationRule.tenant_id == tenant_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=AutomationRuleOut)
async def update_rule(
    rule_id: str,
    body: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id, AutomationRule.tenant_id == tenant_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if body.name is not None:
        rule.name = body.name
    if body.description is not None:
        rule.description = body.description
    if body.trigger_event is not None:
        rule.trigger_event = TriggerEvent(body.trigger_event)
    if body.conditions is not None:
        rule.conditions = body.conditions
    if body.actions is not None:
        rule.actions = body.actions
    if body.priority is not None:
        rule.priority = body.priority
    if body.is_active is not None:
        rule.is_active = body.is_active

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id, AutomationRule.tenant_id == tenant_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
