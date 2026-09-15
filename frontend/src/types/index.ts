// ─── Enums ────────────────────────────────────────────────────────────────────

export type OrderStatus =
  | 'PENDING'
  | 'RESERVED'
  | 'PAID'
  | 'FAILED'
  | 'EXPIRED'
  | 'CANCELLED';

export type ReservationStatus = 'RESERVED' | 'RELEASED' | 'EXPIRED';

export type PaymentStatus = 'SUCCESS' | 'FAILED' | 'EXPIRED';

export type PaymentOutcome = 'success' | 'failure' | 'timeout';

// ─── Domain Models ────────────────────────────────────────────────────────────

export interface Product {
  id: number;
  name: string;
  price: string;   // Decimal comes back as string from FastAPI
  stock: number;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
}

export interface Cart {
  id: number;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: string;
}

export interface Order {
  id: number;
  cart_id: number;
  status: OrderStatus;
  total_amount: string;
  idempotency_key: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface Reservation {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  status: ReservationStatus;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  order_id: number;
  status: PaymentStatus;
  amount: string;
  idempotency_key: string;
  created_at: string;
  updated_at: string;
}

// ─── Request / DTO types ──────────────────────────────────────────────────────

export interface ProductCreate {
  name: string;
  price: string;
  stock: number;
}

export interface ProductUpdate {
  name?: string;
  price?: string;
  stock?: number;
}
