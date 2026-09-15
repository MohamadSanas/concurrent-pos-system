from fastapi import APIRouter
from app.api.routes import products, carts, orders

api_router = APIRouter()

api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(carts.router,    prefix="/carts",    tags=["carts"])
# Orders router also handles /orders/{id}/payment and /orders/{id}/reservation
api_router.include_router(orders.router,   prefix="/orders",   tags=["orders"])

