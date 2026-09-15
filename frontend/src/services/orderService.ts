import api from './api';
import type { Order, Reservation } from '../types';

export const orderService = {
  getAll: async (): Promise<Order[]> => {
    const { data } = await api.get('/orders');
    return data;
  },

  getById: async (id: number): Promise<Order> => {
    const { data } = await api.get(`/orders/${id}`);
    return data;
  },

  cancel: async (id: number): Promise<Order> => {
    const { data } = await api.post(`/orders/${id}/cancel`);
    return data;
  },

  getReservations: async (orderId: number): Promise<Reservation[]> => {
    const { data } = await api.get(`/orders/${orderId}/reservation`);
    return data;
  },
};
