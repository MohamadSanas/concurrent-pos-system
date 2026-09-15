from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.repositories import cart_repository, product_repository
from app.schemas.cart import CartItemAdd, CartItemUpdate


async def create_cart(db: AsyncSession) -> Cart:
    cart = await cart_repository.create_cart(db)
    await db.commit()
    # Reload with items relationship eagerly loaded
    return await cart_repository.get_cart_by_id(db, cart.id)


async def get_cart(db: AsyncSession, cart_id: int) -> Cart:
    """Return the cart (with items) or raise HTTP 404."""
    cart = await cart_repository.get_cart_by_id(db, cart_id)
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart with id {cart_id} not found",
        )
    return cart


async def add_item(db: AsyncSession, cart_id: int, data: CartItemAdd) -> CartItem:
    # Ensure the cart exists
    await get_cart(db, cart_id)

    # Ensure the product exists
    product = await product_repository.get_by_id(db, data.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {data.product_id} not found",
        )

    # Upsert: if the product is already in the cart, add to its quantity
    existing = await cart_repository.get_cart_item_by_product(
        db, cart_id, data.product_id
    )
    if existing is not None:
        new_qty = existing.quantity + data.quantity
        item = await cart_repository.update_item(db, existing, new_qty)
    else:
        item = await cart_repository.add_item(db, cart_id, data.product_id, data.quantity)

    await db.commit()
    # Reload item fresh after commit (refresh to get cart_id populated)
    return await cart_repository.get_cart_item(db, cart_id, item.id)


async def update_item(
    db: AsyncSession, cart_id: int, item_id: int, data: CartItemUpdate
) -> CartItem:
    await get_cart(db, cart_id)

    item = await cart_repository.get_cart_item(db, cart_id, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with id {item_id} not found in cart {cart_id}",
        )

    item = await cart_repository.update_item(db, item, data.quantity)
    await db.commit()
    return await cart_repository.get_cart_item(db, cart_id, item.id)


async def remove_item(db: AsyncSession, cart_id: int, item_id: int) -> None:
    await get_cart(db, cart_id)

    item = await cart_repository.get_cart_item(db, cart_id, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with id {item_id} not found in cart {cart_id}",
        )

    await cart_repository.delete_item(db, item)
    await db.commit()

