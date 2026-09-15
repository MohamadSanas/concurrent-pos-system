"""
Payment service – mock payment gateway.

Supported outcomes:
  success  → order=PAID,    payment=SUCCESS,  reservations stay RESERVED
  failure  → order=FAILED,  payment=FAILED,   stock restored, reservations RELEASED
  timeout  → order=EXPIRED, payment=EXPIRED,  stock restored, reservations EXPIRED
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.product import Product
from app.repositories import (
    order_repository,
    payment_repository,
    reservation_repository,
)
from app.utils.state_machine import transition


async def process_payment(
    db: AsyncSession,
    order_id: int,
    outcome: str,
    idempotency_key: str,
) -> Payment:
    # ------------------------------------------------------------------
    # 1. Idempotency – return existing payment if key was already used
    # ------------------------------------------------------------------
    existing = await payment_repository.get_payment_by_idempotency_key(db, idempotency_key)
    if existing is not None:
        return existing

    # ------------------------------------------------------------------
    # 2. Load order and validate it is in RESERVED state
    # ------------------------------------------------------------------
    order = await order_repository.get_order_by_id(db, order_id)
    if order is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    # ------------------------------------------------------------------
    # 3. Map outcome to order status and payment status
    # ------------------------------------------------------------------
    outcome_map = {
        "success": ("PAID",    "SUCCESS"),
        "failure": ("FAILED",  "FAILED"),
        "timeout": ("EXPIRED", "EXPIRED"),
    }
    new_order_status, payment_status = outcome_map[outcome]

    # Validate the transition is allowed (raises 409 if not)
    transition(order, new_order_status)

    # ------------------------------------------------------------------
    # 4. For non-success outcomes: restore stock and update reservations
    # ------------------------------------------------------------------
    if outcome != "success":
        reservation_final_status = "RELEASED" if outcome == "failure" else "EXPIRED"

        reservations = await reservation_repository.get_reservations_by_order(db, order_id)
        for reservation in reservations:
            if reservation.status == "RESERVED":
                # Restore stock with a row lock
                result = await db.execute(
                    select(Product)
                    .where(Product.id == reservation.product_id)
                    .with_for_update()
                )
                product = result.scalar_one_or_none()
                if product is not None:
                    product.stock += reservation.quantity
                    db.add(product)

                await reservation_repository.update_reservation_status(
                    db, reservation, reservation_final_status
                )

    db.add(order)

    # ------------------------------------------------------------------
    # 5. Create payment record
    # ------------------------------------------------------------------
    payment = await payment_repository.create_payment(
        db,
        order_id=order_id,
        status=payment_status,
        amount=order.total_amount,
        idempotency_key=idempotency_key,
    )

    await db.commit()
    await db.refresh(payment)
    return payment

