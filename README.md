# Concurrent POS System

A concurrency-safe Point of Sale (POS) system designed to handle inventory management, cart-based ordering, stock reservations, mock payments, and complete order lifecycle management.

The system focuses on preventing inventory overselling when multiple customers attempt to purchase limited-stock products simultaneously.

## Features

### Product & Inventory Management

- Create products
- View products
- Update products
- Delete products
- Track available inventory
- View accurate stock levels

### Cart & Checkout

- Add products to cart
- Update cart quantities
- Remove products from cart
- Validate stock availability
- Convert cart into an order
- Prevent duplicate order submissions

### Concurrency-Safe Stock Reservation

- Reserve inventory when checkout begins
- Prevent overselling during concurrent purchases
- Use database transactions for inventory operations
- Automatically expire reservations after 5 minutes
- Release reserved inventory when a reservation expires

### Mock Payment System

Simulates different payment gateway outcomes:

- Successful payment
- Failed payment
- Payment timeout
- Duplicate payment prevention

Payment outcomes are handled independently:

SUCCESS
  ↓
PAID

FAILURE
  ↓
FAILED
  ↓
Stock Released

TIMEOUT
  ↓
EXPIRED
  ↓
Stock Released

### Order Lifecycle

Orders follow controlled state transitions:

PENDING
  ↓
RESERVED
  ↓
PAID
  ↓
COMPLETED

Failure and cancellation paths:

RESERVED → FAILED
RESERVED → EXPIRED
RESERVED → CANCELLED
PAID → CANCELLED

Invalid state transitions are rejected.

### Idempotency

The system prevents duplicate operations from creating:

- Multiple orders
- Multiple payments
- Multiple stock deductions

Repeated requests for the same operation are handled safely.

### Order Cancellation

- Cancel eligible orders
- Restore inventory correctly
- Handle cancellation according to the current order state

## Architecture

                    ┌───────────────┐
                    │    React UI   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Express API   │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Product Service  Cart Service  Order Service
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                   Reservation Service
                            │
                            ▼
                    Payment Service
                            │
                            ▼
                  PostgreSQL Database

## Tech Stack

### Backend

- Node.js
- Express.js
- TypeScript
- Prisma ORM

### Frontend

- React
- Vite
- TypeScript

### Database

- PostgreSQL

### Testing

- Jest
- Supertest

### Deployment

- Backend: Render
- Frontend: Vercel
- Database: PostgreSQL

## Project Structure

concurrent-pos-system/
│
├── backend/
│   ├── prisma/
│   │   ├── schema.prisma
│   │   └── migrations/
│   │
│   ├── src/
│   │   ├── config/
│   │   ├── controllers/
│   │   ├── middleware/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── utils/
│   │   ├── types/
│   │   └── server.ts
│   │
│   ├── tests/
│   ├── .env.example
│   ├── package.json
│   └── tsconfig.json
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   │
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md

## Order Processing Flow

Customer
  │
  ▼
Add Products to Cart
  │
  ▼
Checkout
  │
  ▼
Validate Cart
  │
  ▼
Reserve Stock
  │
  ├───────────────┐
  │               │
  ▼               ▼
Payment         Reservation
Attempt         Timer (5 min)
  │
  ├──────────────┼───────────────┐
  ▼              ▼               ▼
SUCCESS        FAILURE          TIMEOUT
  │              │               │
  ▼              ▼               ▼
PAID           FAILED          EXPIRED
  │              │               │
  │              └───────┬───────┘
  │                      ▼
  │                 Release Stock
  │
  ▼
Order Confirmed

## Concurrency Handling

A major goal of this project is preventing overselling.

For example, if only 1 unit of a product is available and two customers attempt to purchase it at the same time:

Initial Stock = 1

Customer A ──────┐
                 ├──► Database Transaction
Customer B ──────┘

Only ONE transaction can successfully reserve the
available inventory.

Result:

Customer A → RESERVED
Customer B → OUT OF STOCK

The implementation relies on database-level transactional guarantees rather than application-level stock checks alone.

## Stock Reservation

When a customer enters checkout:

Available Stock
      │
      ▼
Reserve Quantity
      │
      ▼
Reservation Created
      │
      ├── Payment Success
      │       ↓
      │     PAID
      │
      ├── Payment Failure
      │       ↓
      │   Stock Released
      │
      └── 5 Minute Timeout
              ↓
          Stock Released

## Mock Payment Scenarios

### Successful Payment

RESERVED → PAID

The reserved inventory remains consumed.

### Failed Payment

RESERVED → FAILED
              ↓
        Release Inventory

### Payment Timeout

RESERVED → EXPIRED
              ↓
        Release Inventory

## Idempotency

The system protects against duplicate requests.

Example:

POST /orders

Request #1
     ↓
Order Created

Request #2
     ↓
Same Idempotency Key
     ↓
Existing Order Returned

The same checkout operation must not create multiple orders or charge the customer multiple times.

## Testing

The test suite covers:

- Product CRUD
- Stock validation
- Cart operations
- Successful checkout
- Insufficient inventory
- Concurrent checkout requests
- Stock reservation
- Reservation expiration
- Successful payment
- Failed payment
- Payment timeout
- Duplicate payment requests
- Duplicate order requests
- Order cancellation
- Inventory restoration
- Invalid order state transitions

Run tests with:

npm test

## Local Development

### Prerequisites

Make sure you have installed:

- Node.js
- npm
- PostgreSQL

### 1. Clone the Repository

git clone https://github.com/YOUR_USERNAME/concurrent-pos-system.git

cd concurrent-pos-system

### 2. Setup Backend

cd backend

npm install

### 3. Configure Environment Variables

Create a .env file:

DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/pos_system"
PORT=5000

### 4. Run Database Migrations

npx prisma migrate dev

### 5. Start Backend

npm run dev

Backend:

http://localhost:5000

### 6. Setup Frontend

Open another terminal:

cd frontend

npm install

npm run dev

Frontend:

http://localhost:5173

## API Overview

### Products

GET    /api/products
GET    /api/products/:id
POST   /api/products
PATCH  /api/products/:id
DELETE /api/products/:id

### Cart

POST   /api/carts
GET    /api/carts/:id
POST   /api/carts/:id/items
PATCH  /api/carts/:id/items/:itemId
DELETE /api/carts/:id/items/:itemId

### Checkout

POST /api/carts/:id/checkout

### Payments

POST /api/orders/:id/payment

### Orders

GET  /api/orders
GET  /api/orders/:id
POST /api/orders/:id/cancel

## Engineering Goals

This project focuses on:

- Database transactions
- Concurrency control
- Inventory consistency
- Idempotent operations
- State-machine based order processing
- Reservation expiration
- Failure handling
- Clean service architecture
- API validation
- Automated testing

## Live Demo

Frontend:
Coming soon

Backend API:
Coming soon

API Documentation:
Coming soon

## Project Status

- [ ] Project setup
- [ ] Database schema
- [ ] Product management
- [ ] Cart management
- [ ] Stock reservation
- [ ] Concurrency handling
- [ ] Mock payment gateway
- [ ] Order lifecycle
- [ ] Idempotency
- [ ] Automated tests
- [ ] React frontend
- [ ] API documentation
- [ ] Deployment

## License

This project is developed as a standalone software engineering project for educational and portfolio purposes.
