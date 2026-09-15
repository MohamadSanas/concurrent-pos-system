import api from './api';
import type { Payment, PaymentOutcome } from '../types';

export const paymentService = {
  process: async (orderId: number, outcome: PaymentOutcome, idempotencyKey: string): Promise<Payment> => {
    const { data } = await api.post(
      `/orders/${orderId}/payment`,
      { outcome },
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return data;
  },
};
