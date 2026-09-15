# tests/test_cart.py
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_product(client, name="Test Product", price="10.00", stock=50):
    r = await client.post("/api/products", json={"name": name, "price": price, "stock": stock})
    return r.json()["id"]


async def _create_cart(client):
    r = await client.post("/api/carts")
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_cart(client):
    resp = await client.post("/api/carts")
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_cart(client):
    cart_id = await _create_cart(client)
    resp = await client.get(f"/api/carts/{cart_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cart_id


@pytest.mark.asyncio
async def test_get_cart_not_found(client):
    resp = await client.get("/api/carts/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_item_to_cart(client):
    product_id = await _create_product(client)
    cart_id = await _create_cart(client)
    resp = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 3})
    assert resp.status_code == 201
    data = resp.json()
    assert data["product_id"] == product_id
    assert data["quantity"] == 3


@pytest.mark.asyncio
async def test_add_item_upsert(client):
    """Adding the same product twice should sum the quantities."""
    product_id = await _create_product(client)
    cart_id = await _create_cart(client)
    await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 2})
    resp = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 3})
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 5


@pytest.mark.asyncio
async def test_update_item(client):
    product_id = await _create_product(client)
    cart_id = await _create_cart(client)
    add = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
    item_id = add.json()["id"]
    resp = await client.patch(f"/api/carts/{cart_id}/items/{item_id}", json={"quantity": 7})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 7


@pytest.mark.asyncio
async def test_remove_item(client):
    product_id = await _create_product(client)
    cart_id = await _create_cart(client)
    add = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
    item_id = add.json()["id"]
    resp = await client.delete(f"/api/carts/{cart_id}/items/{item_id}")
    assert resp.status_code == 204
    # Cart should now be empty
    cart = await client.get(f"/api/carts/{cart_id}")
    assert cart.json()["items"] == []


@pytest.mark.asyncio
async def test_add_invalid_quantity(client):
    product_id = await _create_product(client)
    cart_id = await _create_cart(client)
    resp = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 0})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_nonexistent_product(client):
    cart_id = await _create_cart(client)
    resp = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": 999999, "quantity": 1})
    assert resp.status_code == 404

