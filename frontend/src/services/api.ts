import axios from 'axios';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL ?? 'http://localhost:8000') + '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Global error interceptor – surfaces detail from FastAPI error responses
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ??
      err.response?.data?.message ??
      err.message ??
      'Unknown error';
    return Promise.reject(new Error(Array.isArray(msg) ? msg.map((m: any) => m.msg).join(', ') : msg));
  }
);

export default api;
