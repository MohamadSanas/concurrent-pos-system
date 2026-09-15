"""
Idempotency utilities.

Usage inside a route:
    key = extract_idempotency_key(request)
"""

from fastapi import HTTPException, Request, status


def extract_idempotency_key(request: Request) -> str:
    """
    Read the ``Idempotency-Key`` header from the incoming request.

    Raises HTTP 400 if the header is absent or blank.
    """
    key = request.headers.get("Idempotency-Key", "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required header: Idempotency-Key",
        )
    return key


