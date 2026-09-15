"""
Reservation service.

expire_reservations() can be called by a background task or a cron job
to clean up RESERVED reservations whose expiry time has passed and return
the stock to inventory.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.reservation import Reservation
from app.repositories import reservation_repository


async def get_reservations_for_order(
    db: AsyncSession, order_id: int
) -> list[Reservation]:
    return await reservation_repository.get_reservations_by_order(db, order_id)


async def expire_reservations(db: AsyncSession) -> int:
    """
    Find all RESERVED reservations past their expiry, mark them EXPIRED,
    restore stock, and mark the parent order EXPIRED.

    Returns the number of reservations that were expired.
    """
    from app.models.order import Order
    from app.utils.state_machine import can_transition

    expired = await reservation_repository.get_expired_reservations(db)

    for reservation in expired:
        # Restore stock
        result = await db.execute(
            select(Product)
            .where(Product.id == reservation.product_id)
            .with_for_update()
        )
        product = result.scalar_one_or_none()
        if product is not None:
            product.stock += reservation.quantity
            db.add(product)

        # Mark reservation as EXPIRED
        await reservation_repository.update_reservation_status(db, reservation, "EXPIRED")

        # Mark the parent order as EXPIRED (if still in a state that allows it)
        order_result = await db.execute(
            select(Order).where(Order.id == reservation.order_id)
        )
        order = order_result.scalar_one_or_none()
        if order is not None and can_transition(order.status, "EXPIRED"):
            order.status = "EXPIRED"
            db.add(order)

    if expired:
        await db.commit()

    return len(expired)

