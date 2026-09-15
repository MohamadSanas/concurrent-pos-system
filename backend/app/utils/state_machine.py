"""
Order state machine.

Valid transitions:
  PENDING  → RESERVED
  RESERVED → PAID | FAILED | EXPIRED | CANCELLED
  PAID     → CANCELLED
"""

from fastapi import HTTPException, status

VALID_TRANSITIONS: dict[str, list[str]] = {
    "PENDING": ["RESERVED"],
    "RESERVED": ["PAID", "FAILED", "EXPIRED", "CANCELLED"],
    "PAID": ["CANCELLED"],
}


def can_transition(current: str, target: str) -> bool:
    """Return True if moving from *current* to *target* is permitted."""
    return target in VALID_TRANSITIONS.get(current, [])


def transition(order, target: str) -> None:
    """
    Mutate *order.status* to *target* in-place.

    Raises HTTP 409 if the transition is not permitted by the state machine.
    """
    if not can_transition(order.status, target):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot transition order from '{order.status}' to '{target}'. "
                f"Allowed targets: {VALID_TRANSITIONS.get(order.status, [])}"
            ),
        )
    order.status = target

