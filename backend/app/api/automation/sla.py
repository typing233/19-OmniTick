from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user, get_tenant_id, require_role
from app.models.user import User
from app.models.user_role import RoleType
from app.models.automation import SlaPolicy, AutomationExecutionLog
from app.models.base import gen_id
from app.schemas.automation import (
    SlaPolicyCreate, SlaPolicyUpdate, SlaPolicyOut,
    AutomationLogOut, AutomationLogListResponse,
)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/sla-policies", response_model=list[SlaPolicyOut])
async def list_sla_policies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(SlaPolicy).where(SlaPolicy.tenant_id == tenant_id)
        .order_by(SlaPolicy.created_at)
    )
    return result.scalars().all()


@router.post("/sla-policies", response_model=SlaPolicyOut, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    body: SlaPolicyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleType.ADMIN)),
    tenant_id: str = Depends(get_tenant_id),
):
    policy = SlaPolicy(
        id=gen_id(),
        tenant_id=tenant_id,
        name=body.name,
        conditions=body.conditions,
        first_response_minutes=body.first_response_minutes,
        resolution_minutes=body.resolution_minutes,
        is_active=body.is_active,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.patch("/sla-policies/{policy_id}", response_model=SlaPolicyOut)
async def update_sla_policy(
    policy_id: str,
    body: SlaPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleType.ADMIN)),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(SlaPolicy).where(SlaPolicy.id == policy_id, SlaPolicy.tenant_id == tenant_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    if body.name is not None:
        policy.name = body.name
    if body.conditions is not None:
        policy.conditions = body.conditions
    if body.first_response_minutes is not None:
        policy.first_response_minutes = body.first_response_minutes
    if body.resolution_minutes is not None:
        policy.resolution_minutes = body.resolution_minutes
    if body.is_active is not None:
        policy.is_active = body.is_active

    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/sla-policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sla_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleType.ADMIN)),
    tenant_id: str = Depends(get_tenant_id),
):
    result = await db.execute(
        select(SlaPolicy).where(SlaPolicy.id == policy_id, SlaPolicy.tenant_id == tenant_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")
    await db.delete(policy)
    await db.commit()


@router.get("/logs", response_model=AutomationLogListResponse)
async def list_execution_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rule_id: Optional[str] = Query(None),
    ticket_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    from app.models.automation import AutomationRule

    base = (
        select(AutomationExecutionLog)
        .join(AutomationRule)
        .where(AutomationRule.tenant_id == tenant_id)
    )
    count_base = (
        select(func.count(AutomationExecutionLog.id))
        .join(AutomationRule)
        .where(AutomationRule.tenant_id == tenant_id)
    )

    if rule_id:
        base = base.where(AutomationExecutionLog.rule_id == rule_id)
        count_base = count_base.where(AutomationExecutionLog.rule_id == rule_id)
    if ticket_id:
        base = base.where(AutomationExecutionLog.ticket_id == ticket_id)
        count_base = count_base.where(AutomationExecutionLog.ticket_id == ticket_id)

    total = (await db.execute(count_base)).scalar() or 0
    result = await db.execute(
        base.order_by(AutomationExecutionLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return AutomationLogListResponse(items=logs, total=total, page=page, page_size=page_size)
