from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.cart import CartItemAdd, CartItemResponse, CartItemUpdate, CartResponse
from app.schemas.order import OrderResponse
from app.services import cart_service, order_service
from app.utils.idempotency import extract_idempotency_key

router = APIRouter()


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cart",
)
async def create_cart(db: AsyncSession = Depends(get_db)):
    return await cart_service.create_cart(db)


@router.get("/{cart_id}", response_model=CartResponse, summary="Get a cart")
async def get_cart(cart_id: int, db: AsyncSession = Depends(get_db)):
    return await cart_service.get_cart(db, cart_id)


@router.post(
    "/{cart_id}/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to the cart (upserts if product already in cart)",
)
async def add_item(
    cart_id: int, data: CartItemAdd, db: AsyncSession = Depends(get_db)
):
    return await cart_service.add_item(db, cart_id, data)


@router.patch(
    "/{cart_id}/items/{item_id}",
    response_model=CartItemResponse,
    summary="Update item quantity",
)
async def update_item(
    cart_id: int,
    item_id: int,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.update_item(db, cart_id, item_id, data)


@router.delete(
    "/{cart_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from the cart",
)
async def remove_item(
    cart_id: int, item_id: int, db: AsyncSession = Depends(get_db)
):
    await cart_service.remove_item(db, cart_id, item_id)


@router.post(
    "/{cart_id}/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout – reserve stock and create an order",
    description=(
        "Requires an **Idempotency-Key** header to prevent duplicate orders. "
        "Returns the existing order if the same key is reused."
    ),
)
async def checkout(
    cart_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    idempotency_key = extract_idempotency_key(request)
    return await order_service.checkout(db, cart_id, idempotency_key)

