from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CartItemAdd(BaseModel):
    product_id: int = Field(..., gt=0, examples=[1])
    quantity: int = Field(..., ge=1, examples=[2])


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, examples=[3])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_id: int
    product_id: int
    quantity: int


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse] = []

