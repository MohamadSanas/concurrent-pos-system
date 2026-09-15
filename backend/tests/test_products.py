# tests/test_products.py
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_create_product(client):
    resp = await client.post("/api/products", json={"name": "Widget", "price": "9.99", "stock": 100})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Widget"
    assert data["stock"] == 100
    assert "id" in data


@pytest.mark.asyncio
async def test_list_products(client):
    await client.post("/api/products", json={"name": "A", "price": "1.00", "stock": 5})
    await client.post("/api/products", json={"name": "B", "price": "2.00", "stock": 10})
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_product(client):
    create = await client.post("/api/products", json={"name": "Gadget", "price": "49.99", "stock": 20})
    product_id = create.json()["id"]
    resp = await client.get(f"/api/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Gadget"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    resp = await client.get("/api/products/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client):
    create = await client.post("/api/products", json={"name": "Old Name", "price": "5.00", "stock": 10})
    product_id = create.json()["id"]
    resp = await client.patch(f"/api/products/{product_id}", json={"name": "New Name", "stock": 25})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["stock"] == 25


@pytest.mark.asyncio
async def test_delete_product(client):
    create = await client.post("/api/products", json={"name": "Doomed", "price": "1.00", "stock": 1})
    product_id = create.json()["id"]
    resp = await client.delete(f"/api/products/{product_id}")
    assert resp.status_code == 204
    # Confirm it's gone
    resp = await client.get(f"/api/products/{product_id}")
    assert resp.status_code == 404

