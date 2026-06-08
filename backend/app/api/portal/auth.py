from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.customer import Customer
from app.models.base import gen_id
from app.core import hash_password, verify_password, create_customer_token
from app.schemas.portal import CustomerRegister, CustomerLogin, CustomerTokenResponse, CustomerOut
from app.dependencies import get_current_customer

router = APIRouter(prefix="/portal/auth", tags=["portal-auth"])

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/register", response_model=CustomerTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: CustomerRegister, db: AsyncSession = Depends(get_db)):
    tenant_id = DEFAULT_TENANT_ID

    existing = await db.execute(
        select(Customer).where(Customer.email == body.email, Customer.tenant_id == tenant_id)
    )
    customer = existing.scalar_one_or_none()

    if customer and customer.is_registered:
        raise HTTPException(status_code=400, detail="Email already registered")

    if customer and not customer.is_registered:
        customer.password_hash = hash_password(body.password)
        customer.display_name = body.display_name or customer.display_name
        customer.is_registered = True
    else:
        customer = Customer(
            id=gen_id(),
            tenant_id=tenant_id,
            email=body.email,
            display_name=body.display_name or body.email.split("@")[0],
            password_hash=hash_password(body.password),
            is_registered=True,
        )
        db.add(customer)

    await db.commit()
    await db.refresh(customer)
    token = create_customer_token(customer.id, tenant_id)
    return CustomerTokenResponse(access_token=token)


@router.post("/login", response_model=CustomerTokenResponse)
async def login(body: CustomerLogin, db: AsyncSession = Depends(get_db)):
    tenant_id = DEFAULT_TENANT_ID

    result = await db.execute(
        select(Customer).where(
            Customer.email == body.email,
            Customer.tenant_id == tenant_id,
            Customer.is_registered == True,
        )
    )
    customer = result.scalar_one_or_none()
    if not customer or not customer.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_customer_token(customer.id, tenant_id)
    return CustomerTokenResponse(access_token=token)


@router.get("/me", response_model=CustomerOut)
async def me(customer: Customer = Depends(get_current_customer)):
    return customer
