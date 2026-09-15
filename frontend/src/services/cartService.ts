import api from './api';
import type { Cart, CartItem, Order } from '../types';

export const cartService = {
  create: async (): Promise<Cart> => {
    const { data } = await api.post('/carts');
    return data;
  },

  getById: async (id: number): Promise<Cart> => {
    const { data } = await api.get(`/carts/${id}`);
    return data;
  },

  addItem: async (cartId: number, productId: number, quantity: number): Promise<CartItem> => {
    const { data } = await api.post(`/carts/${cartId}/items`, {
      product_id: productId,
      quantity,
    });
    return data;
  },

  updateItem: async (cartId: number, itemId: number, quantity: number): Promise<CartItem> => {
    const { data } = await api.patch(`/carts/${cartId}/items/${itemId}`, { quantity });
    return data;
  },

  removeItem: async (cartId: number, itemId: number): Promise<void> => {
    await api.delete(`/carts/${cartId}/items/${itemId}`);
  },

  checkout: async (cartId: number, idempotencyKey: string): Promise<Order> => {
    const { data } = await api.post(
      `/carts/${cartId}/checkout`,
      {},
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return data;
  },
};
