"""
Order service.

The checkout path is the most critical piece of this system.
It uses SELECT ... FOR UPDATE to obtain row-level locks on every product
being purchased, preventing two concurrent transactions from both seeing
the same stock value and both succeeding when only one should.

Sequence inside checkout():
  1. Idempotency check – return existing order if key was already used.
  2. Load & validate cart (must be non-empty).
  3. BEGIN transaction (the AsyncSession is already a transaction context).
  4. For each cart item:
       a. Lock the product row  (SELECT ... FOR UPDATE)
       b. Validate stock ≥ quantity  (raises 409 if insufficient)
       c. Deduct stock in-place
  5. Create Order (PENDING), OrderItems, Reservations in the same transaction.
  6. Transition order PENDING → RESERVED.
  7. Commit.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.cart import CartItem
from app.models.order import Order
from app.models.product import Product
from app.repositories import (
    cart_repository,
    order_repository,
    reservation_repository,
)
from app.utils.state_machine import transition


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


async def get_order(db: AsyncSession, order_id: int) -> Order:
    order = await order_repository.get_order_by_id(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )
    return order


async def get_all_orders(db: AsyncSession) -> list[Order]:
    return await order_repository.get_all_orders(db)


# ---------------------------------------------------------------------------
# Checkout (concurrency-critical path)
# ---------------------------------------------------------------------------


async def checkout(db: AsyncSession, cart_id: int, idempotency_key: str) -> Order:
    # ------------------------------------------------------------------
    # 1. Idempotency – return existing order if key was already used
    # ------------------------------------------------------------------
    existing = await order_repository.get_order_by_idempotency_key(db, idempotency_key)
    if existing is not None:
        return existing

    # ------------------------------------------------------------------
    # 2. Load & validate cart
    # ------------------------------------------------------------------
    cart = await cart_repository.get_cart_by_id(db, cart_id)
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart with id {cart_id} not found",
        )
    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot checkout an empty cart",
        )

    # ------------------------------------------------------------------
    # 3-4. Lock each product row and validate / deduct stock
    #      SELECT ... FOR UPDATE serialises concurrent checkout attempts
    #      for the same product.
    # ------------------------------------------------------------------
    total_amount = Decimal("0.00")
    locked_items: list[tuple[CartItem, Product]] = []

    for cart_item in cart.items:
        # Acquire row-level lock
        result = await db.execute(
            select(Product)
            .where(Product.id == cart_item.product_id)
            .with_for_update()
        )
        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {cart_item.product_id} not found",
            )

        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient stock for product '{product.name}'. "
                    f"Available: {product.stock}, requested: {cart_item.quantity}"
                ),
            )

        # Deduct stock immediately (still inside the transaction)
        product.stock -= cart_item.quantity
        db.add(product)

        total_amount += Decimal(str(product.price)) * cart_item.quantity
        locked_items.append((cart_item, product))

    # ------------------------------------------------------------------
    # 5. Create Order + OrderItems in the same transaction
    # ------------------------------------------------------------------
    order = await order_repository.create_order(
        db,
        cart_id=cart_id,
        total_amount=total_amount,
        idempotency_key=idempotency_key,
    )

    for cart_item, product in locked_items:
        await order_repository.add_order_item(
            db,
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            unit_price=Decimal(str(product.price)),
        )

    # ------------------------------------------------------------------
    # 6. Create Reservations
    # ------------------------------------------------------------------
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESERVATION_EXPIRY_MINUTES
    )
    for cart_item, product in locked_items:
        await reservation_repository.create_reservation(
            db,
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            expires_at=expires_at,
        )

    # ------------------------------------------------------------------
    # 7. PENDING → RESERVED and commit
    # ------------------------------------------------------------------
    transition(order, "RESERVED")
    db.add(order)

    await db.commit()

    # Reload the order with all relationships for the response
    return await order_repository.get_order_by_id(db, order.id)


# ---------------------------------------------------------------------------
# Cancel order
# ---------------------------------------------------------------------------


async def cancel_order(db: AsyncSession, order_id: int) -> Order:
    order = await get_order(db, order_id)

    # Validate the current status allows cancellation
    transition(order, "CANCELLED")  # raises 409 if not allowed

    # Restore stock only for the RESERVED → CANCELLED path.
    # For PAID → CANCELLED the stock was already definitively consumed.
    # We detect the original state by checking whether any reservations are
    # still in RESERVED status.
    reservations = await reservation_repository.get_reservations_by_order(db, order_id)
    for reservation in reservations:
        if reservation.status == "RESERVED":
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

            await reservation_repository.update_reservation_status(
                db, reservation, "RELEASED"
            )

    db.add(order)
    await db.commit()

    return await order_repository.get_order_by_id(db, order.id)

