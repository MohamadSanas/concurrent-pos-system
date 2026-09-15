from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class PaymentRequest(BaseModel):
    outcome: Literal["success", "failure", "timeout"] = Field(
        ...,
        examples=["success"],
        description="Simulated payment gateway outcome",
    )


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    status: str
    amount: Decimal
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

