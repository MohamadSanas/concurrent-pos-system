# Concurrent POS System — Implementation Plan

**Stack:** Python · FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL · React · TypeScript · Vite · Pytest

---

## Overview

The project is split into **7 sequential phases**. Each phase produces a testable, runnable slice of the system. No phase starts before the previous one is verified.

```
Phase 1 → Project Setup & Database Foundation
Phase 2 → Product Management (CRUD)
Phase 3 → Cart Management
Phase 4 → Checkout & Concurrency-Safe Stock Reservation
Phase 5 → Mock Payment Gateway & Order Lifecycle
Phase 6 → Automated Test Suite
Phase 7 → React Frontend
```

---

## Phase 1 — Project Setup & Database Foundation

**Goal:** FastAPI server running, PostgreSQL connected, all SQLAlchemy models defined, Alembic migrations applied, health endpoint responding.

### What gets built

#### [MODIFY] [`core/config.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/core/config.py)
- Pydantic `Settings` reading `DATABASE_URL`, `APP_ENV`, `CORS_ORIGINS`, `RESERVATION_EXPIRY_MINUTES` from `.env`

#### [MODIFY] [`core/database.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/core/database.py)
- Async SQLAlchemy engine (`create_async_engine`)
- `AsyncSessionLocal` session factory
- `Base` declarative base
- `get_db()` dependency that yields a session

#### [MODIFY] [`models/product.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/models/product.py)
```
Product
  id          Integer PK
  name        String  NOT NULL
  price       Numeric(10,2) NOT NULL
  stock       Integer NOT NULL  DEFAULT 0
  created_at  DateTime  server_default
  updated_at  DateTime  onupdate
```

#### [MODIFY] [`models/cart.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/models/cart.py)
```
Cart
  id          Integer PK
  created_at  DateTime
  updated_at  DateTime

CartItem
  id          Integer PK
  cart_id     FK → carts.id
  product_id  FK → products.id
  quantity    Integer NOT NULL
```

#### [MODIFY] [`models/order.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/models/order.py)
```
Order
  id              Integer PK
  cart_id         FK → carts.id
  status          String  DEFAULT 'PENDING'
  total_amount    Numeric(10,2)
  idempotency_key String  UNIQUE   ← prevents duplicate checkouts
  created_at      DateTime
  updated_at      DateTime

OrderItem
  id          Integer PK
  order_id    FK → orders.id
  product_id  FK → products.id
  quantity    Integer
  unit_price  Numeric(10,2)
```

#### [MODIFY] [`models/reservation.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/models/reservation.py)
```
Reservation
  id          Integer PK
  order_id    FK → orders.id
  product_id  FK → products.id
  quantity    Integer
  status      String  DEFAULT 'RESERVED'
  expires_at  DateTime NOT NULL
  created_at  DateTime
  updated_at  DateTime
```

#### [MODIFY] [`models/payment.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/models/payment.py)
```
Payment
  id              Integer PK
  order_id        FK → orders.id
  status          String
  amount          Numeric(10,2)
  idempotency_key String  UNIQUE   ← prevents duplicate payments
  created_at      DateTime
  updated_at      DateTime
```

#### [NEW] `backend/alembic.ini` + `backend/migrations/env.py`
- `alembic init migrations` → configure `env.py` to import `Base.metadata` and use the async engine

#### [MODIFY] [`main.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/main.py)
- `GET /health` → `{"status": "ok"}`
- CORS middleware with origins from config

### Verification
```bash
# In backend/
alembic upgrade head          # All 5 tables created in PostgreSQL
uvicorn app.main:app --reload
curl http://localhost:8000/health  # → {"status":"ok"}
curl http://localhost:8000/docs    # Swagger UI loads
```

---

## Phase 2 — Product Management (CRUD)

**Goal:** Full product CRUD with Pydantic validation, proper error handling, tested via Pytest.

### Endpoints
| Method | Path | Action |
|--------|------|--------|
| `GET` | `/api/products` | List all products |
| `GET` | `/api/products/{product_id}` | Get one product |
| `POST` | `/api/products` | Create product |
| `PATCH` | `/api/products/{product_id}` | Update product |
| `DELETE` | `/api/products/{product_id}` | Delete product |

### What gets built

#### [MODIFY] [`schemas/product.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/schemas/product.py)
- `ProductCreate` — `name: str`, `price: Decimal`, `stock: int ≥ 0`
- `ProductUpdate` — all fields optional
- `ProductResponse` — all fields + timestamps

#### [MODIFY] [`repositories/product_repository.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/repositories/product_repository.py)
- `get_all(db)` → list of products
- `get_by_id(db, id)` → product or `None`
- `create(db, data)` → new product
- `update(db, product, data)` → updated product
- `delete(db, product)` → void

#### [MODIFY] [`services/product_service.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/services/product_service.py)
- Calls repository; raises `HTTPException(404)` when product not found
- Validates `stock >= 0`, `price > 0`

#### [MODIFY] [`api/routes/products.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/products.py)
- All 5 endpoints wired to service

#### [MODIFY] [`tests/test_products.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_products.py)
- Create, read all, read one, update, delete, 404 for missing product

### Verification
```bash
pytest tests/test_products.py -v   # All pass
```

---

## Phase 3 — Cart Management

**Goal:** Customers can build a cart with items, quantities are validated against current stock.

### Endpoints
| Method | Path | Action |
|--------|------|--------|
| `POST` | `/api/carts` | Create empty cart |
| `GET` | `/api/carts/{cart_id}` | Get cart with items |
| `POST` | `/api/carts/{cart_id}/items` | Add item to cart |
| `PATCH` | `/api/carts/{cart_id}/items/{item_id}` | Update item quantity |
| `DELETE` | `/api/carts/{cart_id}/items/{item_id}` | Remove item |

### What gets built

#### [MODIFY] [`schemas/cart.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/schemas/cart.py)
- `CartItemAdd` — `product_id: int`, `quantity: int ≥ 1`
- `CartItemUpdate` — `quantity: int ≥ 1`
- `CartItemResponse`, `CartResponse`

#### [MODIFY] [`services/cart_service.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/services/cart_service.py)
- `create_cart`, `get_cart`, `add_item`, `update_item`, `remove_item`
- Validates `product_id` exists and `quantity > 0`
- Does **not** validate stock at cart-add time (only at checkout)

#### [MODIFY] [`api/routes/carts.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/carts.py)
- All 5 endpoints

#### [MODIFY] [`tests/test_cart.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_cart.py)
- Create cart, add item, view cart, update quantity, remove item, invalid quantity (0 / negative), invalid product ID

### Verification
```bash
pytest tests/test_cart.py -v   # All pass
```

---

## Phase 4 — Checkout & Concurrency-Safe Stock Reservation

**Goal:** This is the core engineering challenge. Checkout must atomically reserve stock inside a database transaction. Concurrent requests for the same last unit must result in exactly one success and the rest getting a 409 / stock-exhausted error.

> [!IMPORTANT]
> Stock reservation uses `SELECT ... FOR UPDATE` (pessimistic locking) inside an `async with db.begin()` transaction block. This is the mechanism that prevents overselling. It must never be replaced with an application-level read-then-write.

### Endpoint
| Method | Path | Header | Action |
|--------|------|--------|--------|
| `POST` | `/api/carts/{cart_id}/checkout` | `Idempotency-Key: <key>` | Create order + reserve stock |

### Checkout flow (inside one DB transaction)
1. Check idempotency key → if already used, return existing order (idempotent)
2. Validate cart is not empty
3. For each cart item: `SELECT ... FOR UPDATE` on `products` row
4. Validate `product.stock >= requested_quantity` → 409 if not
5. Deduct stock: `product.stock -= quantity`
6. Create `Order` (status=`RESERVED`, `idempotency_key` set)
7. Create `OrderItem` rows
8. Create `Reservation` rows (`expires_at = now + 5 min`)
9. COMMIT → return order

### What gets built

#### [MODIFY] [`utils/state_machine.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/utils/state_machine.py)
```python
VALID_TRANSITIONS = {
    "PENDING":  ["RESERVED"],
    "RESERVED": ["PAID", "FAILED", "EXPIRED", "CANCELLED"],
    "PAID":     ["CANCELLED"],
}

def transition(current: str, next: str) -> None:
    """Raises HTTPException(409) if transition is invalid."""
```

#### [MODIFY] [`utils/idempotency.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/utils/idempotency.py)
- `check_idempotency_key(db, key)` → existing `Order` or `None`
- Used by checkout and payment services

#### [MODIFY] [`services/reservation_service.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/services/reservation_service.py)
- `create_reservations(db, order_id, items, expiry_minutes)` — called inside checkout transaction
- `expire_reservations(db)` — scans for expired `RESERVED` rows, releases stock, marks `EXPIRED` (called by background task or endpoint)

#### [MODIFY] [`services/order_service.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/services/order_service.py)
- `checkout(db, cart_id, idempotency_key)` — full atomic checkout
- `cancel_order(db, order_id)` — validate state, restore stock, update reservation, commit
- `get_order`, `list_orders`

#### [MODIFY] [`repositories/order_repository.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/repositories/order_repository.py)
- `get_by_id`, `get_by_idempotency_key`, `create`, `update_status`

#### [MODIFY] [`repositories/reservation_repository.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/repositories/reservation_repository.py)
- `create`, `get_by_order_id`, `get_expired`, `update_status`

#### [MODIFY] [`api/routes/carts.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/carts.py)
- Add `POST /api/carts/{cart_id}/checkout`

#### [MODIFY] [`api/routes/orders.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/orders.py)
- `GET /api/orders`, `GET /api/orders/{order_id}`
- `POST /api/orders/{order_id}/cancel`
- `GET /api/orders/{order_id}/reservation`

#### [MODIFY] [`tests/test_checkout.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_checkout.py)
- Successful checkout → order status `RESERVED`, stock decreased
- Insufficient stock → 409
- Empty cart → 422
- Duplicate idempotency key → same order returned, stock deducted only once
- Invalid cart ID → 404

#### [MODIFY] [`tests/test_concurrency.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_concurrency.py)
- 10 concurrent `asyncio.gather` checkout requests for a product with stock=5, qty=1 each
- Assert exactly 5 succeed (HTTP 200), 5 fail (HTTP 409)
- Assert final `product.stock == 0`
- Assert no overselling under any condition

### Verification
```bash
pytest tests/test_checkout.py -v
pytest tests/test_concurrency.py -v
```

---

## Phase 5 — Mock Payment Gateway & Full Order Lifecycle

**Goal:** Payment endpoint accepts a simulated outcome. Each outcome drives the order through the state machine. Failed/expired payments release stock. Duplicate payments are rejected via idempotency key.

### Endpoint
| Method | Path | Header | Body | Action |
|--------|------|--------|------|--------|
| `POST` | `/api/orders/{order_id}/payment` | `Idempotency-Key: <key>` | `{"outcome": "success"\|"failure"\|"timeout"}` | Process payment |

### Payment outcome logic

| Outcome | Order Status | Reservation Status | Stock |
|---------|-------------|-------------------|-------|
| `success` | `PAID` | `RESERVED` (consumed) | stays deducted |
| `failure` | `FAILED` | `RELEASED` | restored |
| `timeout` | `EXPIRED` | `EXPIRED` | restored |

### What gets built

#### [MODIFY] [`schemas/payment.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/schemas/payment.py)
- `PaymentRequest` — `outcome: Literal["success", "failure", "timeout"]`
- `PaymentResponse` — id, order_id, status, amount, idempotency_key, created_at

#### [MODIFY] [`schemas/order.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/schemas/order.py)
- `OrderResponse` — id, status, total_amount, items, created_at, updated_at
- `OrderCancelResponse`

#### [MODIFY] [`schemas/reservation.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/schemas/reservation.py)
- `ReservationResponse` — id, order_id, product_id, quantity, status, expires_at

#### [MODIFY] [`services/payment_service.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/services/payment_service.py)
- `process_payment(db, order_id, outcome, idempotency_key)`:
  1. Check idempotency key → return existing payment if found
  2. Validate order is in `RESERVED` state (else 409 invalid state)
  3. Run outcome logic inside DB transaction:
     - `success` → `Order.status = PAID`
     - `failure` → `Order.status = FAILED`, restore stock, mark reservation `RELEASED`
     - `timeout` → `Order.status = EXPIRED`, restore stock, mark reservation `EXPIRED`
  4. Create `Payment` record
  5. COMMIT

#### [MODIFY] [`api/routes/payments.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/payments.py)
- `POST /api/orders/{order_id}/payment`

#### [MODIFY] [`api/routes/orders.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/app/api/routes/orders.py)
- Wire up cancel endpoint and reservation retrieval
- Reject invalid state transitions with descriptive 409 errors

### Verification
```bash
pytest tests/test_payments.py -v
pytest tests/test_orders.py -v
pytest tests/test_reservations.py -v
```

---

## Phase 6 — Automated Test Suite

**Goal:** Complete, green test suite covering all normal and failure paths. Tests use a dedicated test database and are fully isolated (rollback after each test).

### Test infrastructure

#### [NEW] `backend/tests/conftest.py`
- `pytest-asyncio` fixtures
- `AsyncClient` (HTTPX) pointed at the FastAPI test app
- In-memory or test-schema PostgreSQL setup
- Per-test database rollback using `db.begin()` → `db.rollback()` pattern

### Full test matrix

| File | Tests |
|------|-------|
| [`test_products.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_products.py) | Create, read, update, delete, 404, invalid price, invalid stock |
| [`test_cart.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_cart.py) | Create, add item, update qty, remove, invalid qty, invalid product |
| [`test_checkout.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_checkout.py) | Success, insufficient stock, empty cart, duplicate key, invalid cart |
| [`test_reservations.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_reservations.py) | Reservation created, expiration releases stock, multiple reservations |
| [`test_payments.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_payments.py) | Success → PAID, failure → stock restored, timeout → expired, duplicate key, wrong state |
| [`test_orders.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_orders.py) | Lifecycle states, cancellation, stock restored on cancel, invalid transition rejected |
| [`test_concurrency.py`](file:///c:/Users/sanas/Desktop/my%20learn/Projects/concurrent-pos-system/backend/tests/test_concurrency.py) | 10 concurrent checkouts on stock=5 → exactly 5 succeed, stock=0, no oversell |

### Verification
```bash
pytest -v                          # All tests pass
pytest tests/test_concurrency.py  # Concurrency test specifically confirmed
```

---

## Phase 7 — React Frontend

**Goal:** A polished React UI that lets users manage products, build a cart, checkout, simulate payments, and view order status.

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Products | `/` | List all products with stock levels; add to cart |
| Cart | `/cart` | View cart items; update quantities; proceed to checkout |
| Checkout | `/checkout` | Confirm order; submit checkout; display reservation timer |
| Payment | `/orders/:id/payment` | Choose simulated outcome (success / failure / timeout) |
| Orders | `/orders` | List all orders with status badges |
| Order Detail | `/orders/:id` | Full order info + reservation status |

### What gets built

#### [NEW] `frontend/src/types/index.ts`
- TypeScript interfaces: `Product`, `Cart`, `CartItem`, `Order`, `OrderItem`, `Reservation`, `Payment`

#### [NEW] `frontend/src/services/api.ts`
- Axios (or fetch) client pointing at `VITE_API_URL`
- Functions for every backend endpoint

#### [NEW] `frontend/src/hooks/`
- `useProducts.ts` — fetch + mutate products
- `useCart.ts` — cart state management
- `useOrder.ts` — order + payment actions

#### [NEW] `frontend/src/components/`
- `ProductCard.tsx` — product display + "Add to Cart" button
- `CartItem.tsx` — item row with quantity controls
- `OrderStatusBadge.tsx` — colored badge by status
- `ReservationTimer.tsx` — countdown to reservation expiry
- `PaymentSimulator.tsx` — three outcome buttons

#### [NEW] `frontend/src/pages/`
- `ProductsPage.tsx`
- `CartPage.tsx`
- `CheckoutPage.tsx`
- `PaymentPage.tsx`
- `OrdersPage.tsx`
- `OrderDetailPage.tsx`

#### [MODIFY] `frontend/src/App.tsx`
- React Router setup with all routes

### Verification
```bash
npm run dev    # Starts on http://localhost:5173
# Manual walkthrough:
# 1. Create a product via UI
# 2. Add to cart
# 3. Checkout → order shows RESERVED + timer
# 4. Simulate payment success → order shows PAID
# 5. Simulate payment failure → stock restored
```

---

## Verification Plan — End to End

### After Phase 4 (checkout)
Run the concurrency test to confirm the database transaction + `FOR UPDATE` locking is working correctly:
```bash
pytest tests/test_concurrency.py -v
```
Expected: Exactly `stock` successful reservations, zero overselling.

### After Phase 5 (payments)
```bash
pytest -v
```
Expected: All tests green.

### After Phase 7 (frontend)
Manual walkthrough with the full flow:
1. Products page → create product (stock=5)
2. Add 2 units to cart → checkout
3. Open a second browser tab → try to checkout the same cart again (idempotency test)
4. Go to payment page → choose **success** → order goes to PAID
5. Create a new cart → add product → checkout → choose **failure** → stock restored
6. Create a new cart → add product → checkout → choose **timeout** → reservation expires

---

## Open Questions

> [!IMPORTANT]
> **Q1 — Reservation expiry mechanism:** The 5-minute expiry can be triggered in two ways:
> - **On-demand**: Check for expired reservations whenever a relevant endpoint is called (simpler, no background process needed)
> - **Background task**: FastAPI `BackgroundTasks` or APScheduler polling every 30s (accurate, runs independently)
>
> Which approach do you prefer to start with?

> [!IMPORTANT]
> **Q2 — Test database:** Should the test suite use:
> - A **separate PostgreSQL database** (e.g., `pos_system_test`) — closer to production
> - **SQLite in-memory** — faster, no PostgreSQL setup needed but limited async support
>
> Recommended: separate PostgreSQL test database.

> [!IMPORTANT]
> **Q3 — Frontend state management:** Should the cart state be:
> - **Stored in the backend** (already modelled — `Cart` + `CartItem` tables)
> - **Local React state** (simpler frontend, no persistence)
>
> The backend model already supports persistent carts. Recommended: use backend-stored carts.
