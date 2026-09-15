# Concurrent POS System

A concurrency-safe Point of Sale (POS) system built with FastAPI and PostgreSQL.

The system manages products, inventory, carts, stock reservations, mock payments, and the complete order lifecycle while preventing inventory overselling during concurrent purchase attempts.

The main engineering focus of this project is reliable transaction handling, concurrency control, stock reservation, payment failure handling, and idempotent order processing.

---

## Overview

Traditional POS systems can face inventory inconsistencies when multiple customers attempt to purchase the same limited-stock product at the same time.

For example:

If a product has only 1 unit available and two customers attempt to purchase it simultaneously, the system must allow only one successful reservation.

This project addresses that problem using:

- PostgreSQL transactions
- Database-level concurrency control
- Atomic inventory updates
- Stock reservations
- Reservation expiration
- Idempotent checkout and payment operations
- Controlled order state transitions

---

## Features

### Product & Inventory Management

- Create products
- Retrieve products
- Retrieve a single product
- Update products
- Delete products
- Track product price
- Track available stock
- View current stock levels

Each product contains:

- Product ID
- Name
- Price
- Available stock
- Created timestamp
- Updated timestamp

### Cart Management

Users can:

- Create a cart
- View a cart
- Add products to a cart
- Update item quantities
- Remove items from a cart
- View current cart contents

Stock is validated before checkout.

### Checkout

The checkout process:

1. Validates the cart
2. Validates product availability
3. Starts a database transaction
4. Reserves the required inventory
5. Creates the order
6. Creates the reservation
7. Starts the payment process

Stock is reserved when the customer enters checkout.

### Concurrency-Safe Stock Reservation

The most important part of this project is preventing overselling.

Example:

Product Stock = 1

Customer A ──────────┐
                     │
                     ├──► Checkout
                     │
Customer B ──────────┘

Only one customer should successfully reserve the available unit.

Expected result:

Customer A → RESERVED
Customer B → OUT OF STOCK

The application does not rely only on:

Check stock
    ↓
Decrease stock

because two simultaneous requests could both read the same stock value.

Instead, inventory operations are protected using database-level transactional mechanisms.

### Stock Reservation

Stock is reserved when checkout begins.

A reservation contains:

- Reservation ID
- Order ID
- Product ID
- Quantity
- Reservation status
- Created timestamp
- Expiration timestamp

Reservations expire automatically after 5 minutes if checkout is not completed.

When a reservation expires:

RESERVED
   ↓
EXPIRED
   ↓
Stock Released

The released quantity becomes available again.

### Reservation Flow

                    Checkout
                       │
                       ▼
                Validate Cart
                       │
                       ▼
                 Reserve Stock
                       │
                       ▼
              Reservation Created
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        Payment Success     5 Minute Timer
              │                 │
              ▼                 ▼
            PAID             EXPIRED
                                │
                                ▼
                          Release Stock

### Mock Payment System

The project includes a mock payment gateway.

The gateway supports:

- Successful payment
- Failed payment
- Payment timeout

#### Successful Payment

RESERVED
   ↓
PAID

The reserved stock remains consumed.

#### Failed Payment

RESERVED
   ↓
FAILED
   ↓
Release Stock

#### Payment Timeout

RESERVED
   ↓
EXPIRED
   ↓
Release Stock

Each payment outcome is handled differently.

### Duplicate Payment Protection

The system prevents duplicate payment attempts from creating multiple charges or inconsistent orders.

An idempotency mechanism is used for payment operations.

Example:

Payment Request #1
       ↓
Payment Processed
       ↓
Payment ID Created

Payment Request #2
       ↓
Same Idempotency Key
       ↓
Existing Payment Returned

The same payment operation must not create multiple successful payments.

### Duplicate Order Protection

The system also protects against duplicate order submissions.

Example:

Checkout Request #1
       ↓
Order Created

Checkout Request #2
       ↓
Same Idempotency Key
       ↓
Existing Order Returned

This prevents duplicate checkout requests from creating multiple orders or deducting inventory multiple times.

### Order Lifecycle

Orders use explicit statuses and controlled state transitions.

Core order states include:

PENDING
   ↓
RESERVED
   ↓
PAID

Failure and expiration paths:

RESERVED → FAILED
RESERVED → EXPIRED
RESERVED → CANCELLED

Paid orders can be cancelled where permitted:

PAID → CANCELLED

Invalid state transitions are rejected.

### Order State Machine

                  ┌─────────────┐
                  │   PENDING   │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  RESERVED   │
                  └──────┬──────┘
                         │
              ┌──────────┼───────────┐
              │          │           │
              ▼          ▼           ▼
           PAID       FAILED      EXPIRED
              │
              ▼
         CANCELLED

The state machine prevents invalid operations such as:

EXPIRED → PAID
FAILED → PAID
CANCELLED → PAID

### Order Cancellation

The system supports order cancellation.

When a cancellable order is cancelled:

1. Validate the current order status
2. Start a database transaction
3. Update the order status
4. Restore inventory where applicable
5. Update the reservation
6. Commit the transaction

Inventory must remain consistent after cancellation.

---

## Database Transactions

Critical operations use database transactions to prevent partial updates.

For example, checkout should not result in:

Stock Deducted
      ↓
Order Creation Failed
      ↓
Stock Permanently Lost

Instead:

BEGIN TRANSACTION

Reserve Stock
Create Order
Create Reservation

        ↓

Everything Successful
        ↓
COMMIT

If an operation fails:

ROLLBACK

This keeps inventory and order records consistent.

---

## Architecture

┌─────────────────────────────┐
│        React Frontend       │
└──────────────┬──────────────┘
               │
               │ HTTP / REST
               ▼
┌─────────────────────────────┐
│        FastAPI Backend      │
│                             │
│  ┌───────────────────────┐  │
│  │ API Routes            │  │
│  └───────────┬───────────┘  │
│              ▼              │
│  ┌───────────────────────┐  │
│  │ Controllers / Schemas │  │
│  └───────────┬───────────┘  │
│              ▼              │
│  ┌───────────────────────┐  │
│  │ Service Layer         │  │
│  └───────────┬───────────┘  │
│              ▼              │
│  ┌───────────────────────┐  │
│  │ Repository / Database │  │
│  └───────────┬───────────┘  │
└──────────────┼──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       PostgreSQL            │
└─────────────────────────────┘

---

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database

- PostgreSQL

### Frontend

- React
- TypeScript
- Vite

### Testing

- Pytest
- HTTPX

### API Documentation

FastAPI automatically provides:

- Swagger UI
- OpenAPI specification
- ReDoc

### Deployment

Planned deployment:

- Backend: Render
- Frontend: Vercel
- Database: PostgreSQL

---

## Project Structure

concurrent-pos-system/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── products.py
│   │   │   │   ├── carts.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── payments.py
│   │   │   │   └── reservations.py
│   │   │   │
│   │   │   └── router.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   └── reservation.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   └── reservation.py
│   │   │
│   │   ├── services/
│   │   │   ├── product_service.py
│   │   │   ├── cart_service.py
│   │   │   ├── order_service.py
│   │   │   ├── reservation_service.py
│   │   │   └── payment_service.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── product_repository.py
│   │   │   ├── order_repository.py
│   │   │   └── reservation_repository.py
│   │   │
│   │   ├── utils/
│   │   │   ├── idempotency.py
│   │   │   └── state_machine.py
│   │   │
│   │   └── main.py
│   │
│   ├── migrations/
│   │
│   ├── tests/
│   │   ├── test_products.py
│   │   ├── test_cart.py
│   │   ├── test_checkout.py
│   │   ├── test_payments.py
│   │   ├── test_reservations.py
│   │   ├── test_orders.py
│   │   └── test_concurrency.py
│   │
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md

---

## Core Data Model

The main entities are:

Product
   │
   ├───────────────┐
   │               │
   ▼               ▼
CartItem        OrderItem
                   │
                   ▼
                 Order
                   │
          ┌────────┼────────┐
          │        │        │
          ▼        ▼        ▼
    Reservation  Payment  Order Status

### Product

Product
--------
id
name
price
stock
created_at
updated_at

### Cart

Cart
----
id
created_at
updated_at

### Cart Item

CartItem
--------
id
cart_id
product_id
quantity

### Order

Order
-----
id
cart_id
status
total_amount
created_at
updated_at

### Order Item

OrderItem
---------
id
order_id
product_id
quantity
unit_price

### Reservation

Reservation
-----------
id
order_id
product_id
quantity
status
expires_at
created_at
updated_at

### Payment

Payment
-------
id
order_id
status
amount
idempotency_key
created_at
updated_at

---

## API Endpoints

### Products

GET    /api/products
GET    /api/products/{product_id}
POST   /api/products
PATCH  /api/products/{product_id}
DELETE /api/products/{product_id}

### Cart

POST   /api/carts
GET    /api/carts/{cart_id}
POST   /api/carts/{cart_id}/items
PATCH  /api/carts/{cart_id}/items/{item_id}
DELETE /api/carts/{cart_id}/items/{item_id}

### Checkout

POST /api/carts/{cart_id}/checkout

An idempotency key is supplied with checkout requests.

Example:

Idempotency-Key: checkout-12345

### Payments

POST /api/orders/{order_id}/payment

Supported outcomes:

success
failure
timeout

### Orders

GET  /api/orders
GET  /api/orders/{order_id}
POST /api/orders/{order_id}/cancel

### Reservations

GET /api/orders/{order_id}/reservation

---

## Checkout Example

Request:

POST /api/carts/{cart_id}/checkout
Idempotency-Key: checkout-12345

Processing:

1. Validate cart
2. Validate product quantities
3. Begin transaction
4. Lock/check inventory
5. Reserve inventory
6. Create order
7. Create reservation
8. Commit transaction
9. Return order

---

## Payment Example

Request:

POST /api/orders/{order_id}/payment
Idempotency-Key: payment-12345

Possible outcomes:

success
   ↓
Order → PAID

failure
   ↓
Order → FAILED
   ↓
Stock Released

timeout
   ↓
Reservation Expires
   ↓
Stock Released

---

## Concurrency Test

One of the most important automated tests simulates simultaneous checkout requests.

Example scenario:

Product stock = 5

10 simultaneous checkout requests
Each requests quantity = 1

Expected result:

Successful orders = 5
Rejected orders = 5
Remaining stock = 0

The system must never produce:

Successful orders > 5

---

## Reservation Expiration Test

Example:

Initial stock = 10

Checkout quantity = 3

Available stock = 7

Reservation expires

Available stock = 10

The system must automatically restore the reserved quantity after the reservation expires.

---

## Payment Failure Test

Example:

Initial stock = 10

Checkout quantity = 3
        ↓
Reserved stock = 3
        ↓
Payment fails
        ↓
Reservation released
        ↓
Available stock = 10

---

## Duplicate Request Test

Example:

Initial stock = 5

Request #1
Idempotency-Key: abc123
        ↓
Order Created

Request #2
Idempotency-Key: abc123
        ↓
Existing Order Returned

Expected:

Orders Created = 1
Stock Deducted = 1 time

---

## Error Handling

The API provides structured errors for cases such as:

- Product not found
- Cart not found
- Order not found
- Insufficient stock
- Reservation expired
- Invalid order state
- Duplicate payment
- Duplicate checkout
- Invalid quantity
- Invalid payment outcome

Example:

{
  "detail": "Insufficient stock for product"
}

---

## Environment Variables

Create a `.env` file inside the backend directory.

DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/pos_system

APP_ENV=development

CORS_ORIGINS=http://localhost:5173

RESERVATION_EXPIRY_MINUTES=5

---

## Local Setup

### Prerequisites

Install:

- Python 3.11+
- Node.js
- npm
- PostgreSQL
- Git

### 1. Clone Repository

git clone https://github.com/YOUR_USERNAME/concurrent-pos-system.git

cd concurrent-pos-system

### 2. Backend Setup

cd backend

Create a virtual environment:

python -m venv venv

Activate on Windows:

venv\Scripts\activate

Activate on Linux/macOS:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

### 3. Configure Environment Variables

Create `.env`:

cp .env.example .env

Configure the PostgreSQL connection inside `.env`.

### 4. Run Database Migrations

alembic upgrade head

### 5. Start FastAPI

uvicorn app.main:app --reload

Backend:

http://localhost:8000

Swagger API Documentation:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc

### 6. Frontend Setup

Open another terminal:

cd frontend

Install dependencies:

npm install

Create environment file:

cp .env.example .env

Configure:

VITE_API_URL=http://localhost:8000

Start development server:

npm run dev

Frontend:

http://localhost:5173

---

## Testing

Backend tests use Pytest.

Run all tests:

pytest

Run with verbose output:

pytest -v

Run concurrency tests:

pytest tests/test_concurrency.py -v

Run checkout tests:

pytest tests/test_checkout.py -v

Run payment tests:

pytest tests/test_payments.py -v

---

## Testing Strategy

The project tests both normal and failure scenarios.

### Product Tests

- Create product
- Read product
- Update product
- Delete product
- Invalid product ID

### Cart Tests

- Create cart
- Add item
- Update item
- Remove item
- Invalid quantity

### Checkout Tests

- Successful checkout
- Insufficient inventory
- Empty cart
- Duplicate checkout
- Invalid cart

### Reservation Tests

- Stock reservation
- Reservation expiration
- Stock restoration
- Multiple reservations

### Payment Tests

- Successful payment
- Failed payment
- Payment timeout
- Duplicate payment
- Payment for invalid order state

### Order Tests

- Order creation
- Order status transitions
- Cancellation
- Inventory restoration
- Invalid state transitions

### Concurrency Tests

- Multiple simultaneous purchases
- Limited inventory
- Concurrent reservations
- No overselling
- Correct final stock

---

## API Documentation

FastAPI provides interactive API documentation.

Once the backend is running:

Swagger UI:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc

OpenAPI:

http://localhost:8000/openapi.json

---

## Deployment

The application is designed to be deployed as:

React Frontend
      │
      ▼
   Vercel
      │
      │ HTTPS
      ▼
FastAPI Backend
      │
      ▼
   Render
      │
      ▼
 PostgreSQL

### Frontend

Planned platform:

Vercel

### Backend

Planned platform:

Render

### Database

PostgreSQL

---

## Live Demo

### Frontend

Coming soon.

### Backend API

Coming soon.

### Swagger Documentation

Coming soon.

---

## Engineering Decisions

### Why PostgreSQL?

PostgreSQL provides strong transactional guarantees and concurrency control mechanisms required for reliable inventory management.

### Why FastAPI?

FastAPI provides:

- Strong request validation
- Type-safe API schemas
- Automatic OpenAPI documentation
- High-performance asynchronous support
- Clean dependency injection patterns

### Why Database Transactions?

Inventory and order operations must remain consistent.

For example:

Reserve Stock
Create Order
Create Reservation

These operations should either all succeed or all fail.

### Why Idempotency?

Networks and clients can retry requests.

Without idempotency:

Client Request
     ↓
Server processes request
     ↓
Network timeout
     ↓
Client retries
     ↓
Second order created

Idempotency prevents this behavior.

---

## Security Considerations

The project will include:

- Input validation
- Database constraints
- Controlled state transitions
- Idempotency protection
- Transaction-safe operations
- CORS configuration
- Environment-based secrets
- No sensitive credentials committed to Git

Environment files are excluded from version control.

---

## Project Status

### Backend

- [ ] FastAPI project setup
- [ ] PostgreSQL connection
- [ ] SQLAlchemy models
- [ ] Alembic migrations
- [ ] Product CRUD
- [ ] Cart management
- [ ] Checkout
- [ ] Concurrency-safe inventory
- [ ] Stock reservations
- [ ] Reservation expiration
- [ ] Mock payment gateway
- [ ] Payment failure handling
- [ ] Payment timeout handling
- [ ] Idempotency
- [ ] Order state machine
- [ ] Order cancellation
- [ ] Error handling
- [ ] Automated tests
- [ ] Concurrency tests

### Frontend

- [ ] React setup
- [ ] Product management UI
- [ ] Cart UI
- [ ] Checkout UI
- [ ] Payment simulation UI
- [ ] Order status UI
- [ ] Inventory display
- [ ] Error handling
- [ ] Responsive design

### Deployment

- [ ] PostgreSQL deployment
- [ ] Backend deployment
- [ ] Frontend deployment
- [ ] Environment configuration
- [ ] Production testing
- [ ] API documentation deployment

---

## Future Improvements

Potential future improvements include:

- Authentication and authorization
- User accounts
- Real payment gateway integration
- Redis-based distributed locking
- Message queues for asynchronous payment processing
- Observability and structured logging
- Rate limiting
- Metrics and monitoring
- Docker containerization
- CI/CD pipeline

---

## License

This project is developed as a standalone software engineering project for educational and portfolio purposes.