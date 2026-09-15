from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import Reservation


async def create_reservation(
    db: AsyncSession,
    order_id: int,
    product_id: int,
    quantity: int,
    expires_at: datetime,
) -> Reservation:
    reservation = Reservation(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        status="RESERVED",
        expires_at=expires_at,
    )
    db.add(reservation)
    await db.flush()
    await db.refresh(reservation)
    return reservation


async def get_reservations_by_order(
    db: AsyncSession, order_id: int
) -> list[Reservation]:
    result = await db.execute(
        select(Reservation).where(Reservation.order_id == order_id)
    )
    return list(result.scalars().all())


async def get_expired_reservations(db: AsyncSession) -> list[Reservation]:
    """Return RESERVED reservations whose expiry has passed."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Reservation).where(
            Reservation.status == "RESERVED",
            Reservation.expires_at < now,
        )
    )
    return list(result.scalars().all())


async def update_reservation_status(
    db: AsyncSession, reservation: Reservation, status: str
) -> Reservation:
    reservation.status = status
    db.add(reservation)
    await db.flush()
    await db.refresh(reservation)
    return reservation

