from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get("", response_model=list[ProductResponse], summary="List all products")
async def list_products(db: AsyncSession = Depends(get_db)):
    return await product_service.get_all_products(db)


@router.get("/{product_id}", response_model=ProductResponse, summary="Get a product")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await product_service.get_product(db, product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await product_service.create_product(db, data)


@router.patch("/{product_id}", response_model=ProductResponse, summary="Update a product")
async def update_product(
    product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    return await product_service.update_product(db, product_id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    await product_service.delete_product(db, product_id)

