# tests/test_checkout.py
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_product(client, name="Product", price="10.00", stock=10):
    r = await client.post("/api/products", json={"name": name, "price": price, "stock": stock})
    return r.json()


async def _create_cart(client):
    r = await client.post("/api/carts")
    return r.json()["id"]


async def _add_item(client, cart_id, product_id, quantity=1):
    await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": quantity})


async def _checkout(client, cart_id, key="idem-key-001"):
    return await client.post(
        f"/api/carts/{cart_id}/checkout",
        headers={"Idempotency-Key": key},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_checkout(client):
    product = await _create_product(client, stock=5)
    cart_id = await _create_cart(client)
    await _add_item(client, cart_id, product["id"], quantity=2)

    resp = await _checkout(client, cart_id, key="checkout-success-1")
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "RESERVED"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

    # Stock should now be 3
    product_resp = await client.get(f"/api/products/{product['id']}")
    assert product_resp.json()["stock"] == 3


@pytest.mark.asyncio
async def test_checkout_empty_cart(client):
    cart_id = await _create_cart(client)
    resp = await _checkout(client, cart_id, key="checkout-empty-1")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_checkout_insufficient_stock(client):
    product = await _create_product(client, stock=1)
    cart_id = await _create_cart(client)
    await _add_item(client, cart_id, product["id"], quantity=5)  # requesting 5 but only 1 available

    resp = await _checkout(client, cart_id, key="checkout-insuf-1")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_checkout_missing_idempotency_header(client):
    product = await _create_product(client, stock=5)
    cart_id = await _create_cart(client)
    await _add_item(client, cart_id, product["id"], quantity=1)
    resp = await client.post(f"/api/carts/{cart_id}/checkout")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_checkout_duplicate_idempotency_key(client):
    """Second checkout with the same key returns the existing order; stock deducted only once."""
    product = await _create_product(client, stock=10)
    cart_id = await _create_cart(client)
    await _add_item(client, cart_id, product["id"], quantity=3)

    key = "checkout-idem-dup-1"
    r1 = await _checkout(client, cart_id, key=key)
    r2 = await _checkout(client, cart_id, key=key)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]

    # Stock deducted only once
    product_resp = await client.get(f"/api/products/{product['id']}")
    assert product_resp.json()["stock"] == 7


@pytest.mark.asyncio
async def test_checkout_invalid_cart(client):
    resp = await _checkout(client, 999999, key="checkout-invalid-cart-1")
    assert resp.status_code == 404
