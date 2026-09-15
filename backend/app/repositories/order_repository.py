from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


async def create_order(
    db: AsyncSession,
    cart_id: int,
    total_amount: Decimal,
    idempotency_key: str,
) -> Order:
    order = Order(
        cart_id=cart_id,
        status="PENDING",
        total_amount=total_amount,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def add_order_item(
    db: AsyncSession,
    order_id: int,
    product_id: int,
    quantity: int,
    unit_price: Decimal,
) -> OrderItem:
    item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def get_order_by_id(db: AsyncSession, order_id: int) -> Order | None:
    """Fetch an order with items, reservations, and payment eagerly loaded."""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.reservations),
            selectinload(Order.payment),
        )
    )
    return result.scalar_one_or_none()


async def get_order_by_idempotency_key(
    db: AsyncSession, key: str
) -> Order | None:
    result = await db.execute(
        select(Order)
        .where(Order.idempotency_key == key)
        .options(
            selectinload(Order.items),
            selectinload(Order.reservations),
            selectinload(Order.payment),
        )
    )
    return result.scalar_one_or_none()


async def get_all_orders(db: AsyncSession) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id)
    )
    return list(result.scalars().all())


async def update_order_status(
    db: AsyncSession, order: Order, new_status: str
) -> Order:
    order.status = new_status
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order

