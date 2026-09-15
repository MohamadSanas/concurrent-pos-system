import React from 'react';
import type { OrderStatus, ReservationStatus, PaymentStatus } from '../types';

type Status = OrderStatus | ReservationStatus | PaymentStatus;

const LABELS: Record<string, string> = {
  PENDING: 'Pending',
  RESERVED: 'Reserved',
  PAID: 'Paid',
  FAILED: 'Failed',
  EXPIRED: 'Expired',
  CANCELLED: 'Cancelled',
  SUCCESS: 'Success',
  RELEASED: 'Released',
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`badge badge-${status}`}>
      {LABELS[status] ?? status}
    </span>
  );
}
