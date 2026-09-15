from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Laptop"])
    price: Decimal = Field(..., gt=0, decimal_places=2, examples=[999.99])
    stock: int = Field(0, ge=0, examples=[50])


class ProductUpdate(BaseModel):
    """All fields are optional — only provided fields are updated."""

    name: str | None = Field(None, min_length=1, max_length=255)
    price: Decimal | None = Field(None, gt=0, decimal_places=2)
    stock: int | None = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    stock: int
    created_at: datetime
    updated_at: datetime
