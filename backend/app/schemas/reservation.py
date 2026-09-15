from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int | None
    quantity: int
    status: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

