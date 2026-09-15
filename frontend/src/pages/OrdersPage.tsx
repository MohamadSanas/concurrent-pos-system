import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { orderService } from '../services/orderService';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import type { Order } from '../types';

export default function OrdersPage() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    orderService.getAll()
      .then(data => setOrders([...data].sort((a, b) => b.id - a.id)))
      .catch(e => toast('error', 'Failed to load orders', e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Orders</h1>
        <p>All order history with status and totals</p>
      </div>
      <div className="page-body">
        {loading ? (
          <div className="loading-screen"><span className="spinner" /><span>Loading…</span></div>
        ) : orders.length === 0 ? (
          <div className="empty-state card" style={{ padding: 60 }}>
            <div className="empty-icon">📋</div>
            <p>No orders yet. Go to Cart to place an order.</p>
          </div>
        ) : (
          <div className="table-wrap card">
            <table>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Cart ID</th>
                  <th>Status</th>
                  <th>Items</th>
                  <th>Total</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id} onClick={() => navigate(`/orders/${o.id}`)}>
                    <td><span className="font-mono text-sm" style={{ fontWeight: 700 }}>#{o.id}</span></td>
                    <td className="td-muted font-mono">#{o.cart_id}</td>
                    <td><StatusBadge status={o.status} /></td>
                    <td className="td-muted">{o.items.length} item{o.items.length !== 1 ? 's' : ''}</td>
                    <td style={{ fontWeight: 600 }}>${Number(o.total_amount).toFixed(2)}</td>
                    <td className="td-muted">{new Date(o.created_at).toLocaleString()}</td>
                    <td>
                      <span style={{ color: 'var(--accent-blue)', fontSize: '0.8rem' }}>View →</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
