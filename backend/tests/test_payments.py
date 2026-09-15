# tests/test_payments.py
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_order(client, stock=10, quantity=2, checkout_key=None):
    """Create a product, cart, add item, and checkout. Returns (product, order)."""
    import uuid
    key = checkout_key or f"pay-checkout-{uuid.uuid4()}"
    p_r = await client.post("/api/products", json={"name": "Pay Product", "price": "20.00", "stock": stock})
    product = p_r.json()
    c_r = await client.post("/api/carts")
    cart_id = c_r.json()["id"]
    await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product["id"], "quantity": quantity})
    o_r = await client.post(f"/api/carts/{cart_id}/checkout", headers={"Idempotency-Key": key})
    return product, o_r.json()


async def _pay(client, order_id, outcome="success", key=None):
    import uuid
    key = key or f"pay-{uuid.uuid4()}"
    return await client.post(
        f"/api/orders/{order_id}/payment",
        json={"outcome": outcome},
        headers={"Idempotency-Key": key},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_payment_success(client):
    product, order = await _setup_order(client, stock=5, quantity=2)
    resp = await _pay(client, order["id"], outcome="success")
    assert resp.status_code == 201
    assert resp.json()["status"] == "SUCCESS"

    # Order should be PAID
    order_resp = await client.get(f"/api/orders/{order['id']}")
    assert order_resp.json()["status"] == "PAID"

    # Stock remains at 3 (not restored)
    p = await client.get(f"/api/products/{product['id']}")
    assert p.json()["stock"] == 3


@pytest.mark.asyncio
async def test_payment_failure(client):
    product, order = await _setup_order(client, stock=5, quantity=2)
    resp = await _pay(client, order["id"], outcome="failure")
    assert resp.status_code == 201
    assert resp.json()["status"] == "FAILED"

    # Order should be FAILED
    order_resp = await client.get(f"/api/orders/{order['id']}")
    assert order_resp.json()["status"] == "FAILED"

    # Stock should be restored to 5
    p = await client.get(f"/api/products/{product['id']}")
    assert p.json()["stock"] == 5


@pytest.mark.asyncio
async def test_payment_timeout(client):
    product, order = await _setup_order(client, stock=10, quantity=3)
    resp = await _pay(client, order["id"], outcome="timeout")
    assert resp.status_code == 201
    assert resp.json()["status"] == "EXPIRED"

    # Order should be EXPIRED
    order_resp = await client.get(f"/api/orders/{order['id']}")
    assert order_resp.json()["status"] == "EXPIRED"

    # Stock restored to 10
    p = await client.get(f"/api/products/{product['id']}")
    assert p.json()["stock"] == 10


@pytest.mark.asyncio
async def test_duplicate_payment_idempotency(client):
    """Sending the same payment key twice should not process payment twice."""
    _, order = await _setup_order(client, stock=5, quantity=1)
    key = "pay-idem-dup-1"
    r1 = await _pay(client, order["id"], outcome="success", key=key)
    r2 = await _pay(client, order["id"], outcome="success", key=key)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_payment_on_paid_order_is_rejected(client):
    """Attempting a payment on an already-PAID order (different key) should fail."""
    _, order = await _setup_order(client, stock=5, quantity=1)
    await _pay(client, order["id"], outcome="success", key="pay-first-1")
    resp = await _pay(client, order["id"], outcome="success", key="pay-second-1")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_payment_on_nonexistent_order(client):
    resp = await _pay(client, 999999, outcome="success")
    assert resp.status_code == 404
