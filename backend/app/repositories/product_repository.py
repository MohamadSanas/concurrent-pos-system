from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_all(db: AsyncSession) -> list[Product]:
    result = await db.execute(select(Product).order_by(Product.id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(
        name=data.name,
        price=data.price,
        stock=data.stock,
    )
    db.add(product)
    await db.flush()   # writes to DB within the transaction; assigns id
    await db.refresh(product)
    return product


async def update(
    db: AsyncSession, product: Product, data: ProductUpdate
) -> Product:
    # Only update fields that were explicitly provided
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def delete(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.flush()
