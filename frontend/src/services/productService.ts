import api from './api';
import type { Product, ProductCreate, ProductUpdate } from '../types';

export const productService = {
  getAll: async (): Promise<Product[]> => {
    const { data } = await api.get('/products');
    return data;
  },

  getById: async (id: number): Promise<Product> => {
    const { data } = await api.get(`/products/${id}`);
    return data;
  },

  create: async (payload: ProductCreate): Promise<Product> => {
    const { data } = await api.post('/products', payload);
    return data;
  },

  update: async (id: number, payload: ProductUpdate): Promise<Product> => {
    const { data } = await api.patch(`/products/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/products/${id}`);
  },
};
