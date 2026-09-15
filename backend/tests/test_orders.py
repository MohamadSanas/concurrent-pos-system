# tests/test_orders.py
import pytest
import uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_order(client, stock=10, quantity=2):
    key = f"ord-checkout-{uuid.uuid4()}"
    p_r = await client.post("/api/products", json={"name": "Order Product", "price": "15.00", "stock": stock})
    product = p_r.json()
    c_r = await client.post("/api/carts")
    cart_id = c_r.json()["id"]
    await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product["id"], "quantity": quantity})
    o_r = await client.post(f"/api/carts/{cart_id}/checkout", headers={"Idempotency-Key": key})
    return product, o_r.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_orders(client):
    await _setup_order(client)
    resp = await client.get("/api/orders")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_order(client):
    _, order = await _setup_order(client)
    resp = await client.get(f"/api/orders/{order['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order["id"]
    assert resp.json()["status"] == "RESERVED"


@pytest.mark.asyncio
async def test_get_order_not_found(client):
    resp = await client.get("/api/orders/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_reserved_order_restores_stock(client):
    product, order = await _setup_order(client, stock=10, quantity=3)
    # Stock is now 7 after checkout
    cancel_resp = await client.post(f"/api/orders/{order['id']}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Stock should be restored to 10
    p = await client.get(f"/api/products/{product['id']}")
    assert p.json()["stock"] == 10


@pytest.mark.asyncio
async def test_cancel_paid_order(client):
    _, order = await _setup_order(client, stock=5, quantity=1)
    # Pay it
    pay_key = f"pay-cancel-{uuid.uuid4()}"
    await client.post(
        f"/api/orders/{order['id']}/payment",
        json={"outcome": "success"},
        headers={"Idempotency-Key": pay_key},
    )
    cancel_resp = await client.post(f"/api/orders/{order['id']}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_cancel_failed_order_is_rejected(client):
    """FAILED → CANCELLED is not a valid transition."""
    _, order = await _setup_order(client, stock=5, quantity=1)
    pay_key = f"pay-fail-cancel-{uuid.uuid4()}"
    await client.post(
        f"/api/orders/{order['id']}/payment",
        json={"outcome": "failure"},
        headers={"Idempotency-Key": pay_key},
    )
    cancel_resp = await client.post(f"/api/orders/{order['id']}/cancel")
    assert cancel_resp.status_code == 409


@pytest.mark.asyncio
async def test_cancel_order_not_found(client):
    resp = await client.post("/api/orders/999999/cancel")
    assert resp.status_code == 404


