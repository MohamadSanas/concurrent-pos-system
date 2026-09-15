from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


async def create_payment(
    db: AsyncSession,
    order_id: int,
    status: str,
    amount: Decimal,
    idempotency_key: str,
) -> Payment:
    payment = Payment(
        order_id=order_id,
        status=status,
        amount=amount,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def get_payment_by_idempotency_key(
    db: AsyncSession, key: str
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(Payment.idempotency_key == key)
    )
    return result.scalar_one_or_none()


async def get_payment_by_order(
    db: AsyncSession, order_id: int
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    return result.scalar_one_or_none()
