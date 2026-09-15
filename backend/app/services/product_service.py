from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories import product_repository
from app.schemas.product import ProductCreate, ProductUpdate


async def get_all_products(db: AsyncSession) -> list[Product]:
    return await product_repository.get_all(db)


async def get_product(db: AsyncSession, product_id: int) -> Product:
    """Returns the product or raises HTTP 404."""
    product = await product_repository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = await product_repository.create(db, data)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, product_id: int, data: ProductUpdate
) -> Product:
    product = await get_product(db, product_id)  # raises 404 if missing
    product = await product_repository.update(db, product, data)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> None:
    product = await get_product(db, product_id)  # raises 404 if missing
    await product_repository.delete(db, product)
    await db.commit()
