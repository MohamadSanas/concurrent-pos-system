from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------


async def create_cart(db: AsyncSession) -> Cart:
    cart = Cart()
    db.add(cart)
    await db.flush()
    await db.refresh(cart)
    return cart


async def get_cart_by_id(db: AsyncSession, cart_id: int) -> Cart | None:
    """Fetch a cart with its items eagerly loaded."""
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items))
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Cart Items
# ---------------------------------------------------------------------------


async def get_cart_item(
    db: AsyncSession, cart_id: int, item_id: int
) -> CartItem | None:
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id, CartItem.cart_id == cart_id
        )
    )
    return result.scalar_one_or_none()


async def get_cart_item_by_product(
    db: AsyncSession, cart_id: int, product_id: int
) -> CartItem | None:
    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart_id, CartItem.product_id == product_id
        )
    )
    return result.scalar_one_or_none()


async def add_item(
    db: AsyncSession, cart_id: int, product_id: int, quantity: int
) -> CartItem:
    item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_item(db: AsyncSession, item: CartItem, quantity: int) -> CartItem:
    item.quantity = quantity
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: CartItem) -> None:
    await db.delete(item)
    await db.flush()
