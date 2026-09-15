# tests/test_reservations.py
import pytest


async def _create_product(client, stock=10):
    r = await client.post("/api/products", json={"name": "Reserved Product", "price": "5.00", "stock": stock})
    return r.json()


async def _create_cart_and_checkout(client, product_id, quantity=1, key="res-key-001"):
    cart_r = await client.post("/api/carts")
    cart_id = cart_r.json()["id"]
    await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": quantity})
    order_r = await client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"Idempotency-Key": key},
    )
    return order_r.json()


@pytest.mark.asyncio
async def test_reservation_created_on_checkout(client):
    product = await _create_product(client, stock=5)
    order = await _create_cart_and_checkout(client, product["id"], quantity=2, key="res-checkout-1")

    assert order["status"] == "RESERVED"

    reservations_resp = await client.get(f"/api/orders/{order['id']}/reservation")
    assert reservations_resp.status_code == 200
    reservations = reservations_resp.json()
    assert len(reservations) == 1

    r = reservations[0]
    assert r["order_id"] == order["id"]
    assert r["product_id"] == product["id"]
    assert r["quantity"] == 2
    assert r["status"] == "RESERVED"
    assert "expires_at" in r


@pytest.mark.asyncio
async def test_reservation_stock_is_deducted(client):
    product = await _create_product(client, stock=10)
    await _create_cart_and_checkout(client, product["id"], quantity=3, key="res-stock-1")

    # Stock should be 7 now
    p = await client.get(f"/api/products/{product['id']}")
    assert p.json()["stock"] == 7


@pytest.mark.asyncio
async def test_reservation_not_found_for_unknown_order(client):
    resp = await client.get("/api/orders/999999/reservation")
    # Returns empty list (order doesn't exist but no error)
    assert resp.status_code == 200
    assert resp.json() == []
