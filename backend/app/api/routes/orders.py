from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.order import OrderResponse
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.schemas.reservation import ReservationResponse
from app.services import order_service, payment_service, reservation_service
from app.utils.idempotency import extract_idempotency_key

router = APIRouter()


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@router.get("", response_model=list[OrderResponse], summary="List all orders")
async def list_orders(db: AsyncSession = Depends(get_db)):
    return await order_service.get_all_orders(db)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get an order")
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    return await order_service.get_order(db, order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an order",
    description="Cancels a RESERVED or PAID order. Stock is restored if the order was RESERVED.",
)
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    return await order_service.cancel_order(db, order_id)


# ---------------------------------------------------------------------------
# Payments (nested under /orders/{order_id}/payment)
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/payment",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process a mock payment for an order",
    description=(
        "Simulates a payment gateway outcome: **success**, **failure**, or **timeout**. "
        "Requires an **Idempotency-Key** header."
    ),
)
async def process_payment(
    order_id: int,
    data: PaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    idempotency_key = extract_idempotency_key(request)
    return await payment_service.process_payment(db, order_id, data.outcome, idempotency_key)


# ---------------------------------------------------------------------------
# Reservations (nested under /orders/{order_id}/reservation)
# ---------------------------------------------------------------------------


@router.get(
    "/{order_id}/reservation",
    response_model=list[ReservationResponse],
    summary="Get reservations for an order",
)
async def get_reservation(order_id: int, db: AsyncSession = Depends(get_db)):
    return await reservation_service.get_reservations_for_order(db, order_id)
