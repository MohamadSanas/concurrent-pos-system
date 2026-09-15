import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { orderService } from '../services/orderService';
import { paymentService } from '../services/paymentService';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import type { Order, Reservation, PaymentOutcome } from '../types';

// ─── Countdown timer ──────────────────────────────────────────────────────────
function Countdown({ expiresAt }: { expiresAt: string }) {
  const [remaining, setRemaining] = useState('');

  useEffect(() => {
    function update() {
      const diff = new Date(expiresAt).getTime() - Date.now();
      if (diff <= 0) { setRemaining('Expired'); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(`${m}m ${s}s`);
    }
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  const isExpiring = new Date(expiresAt).getTime() - Date.now() < 60000;
  return (
    <span style={{ color: isExpiring ? 'var(--accent-rose)' : 'var(--accent-emerald)', fontWeight: 600 }}>
      {remaining}
    </span>
  );
}

// ─── Payment Panel ────────────────────────────────────────────────────────────
function PaymentPanel({ order, onUpdate }: { order: Order; onUpdate: () => void }) {
  const { toast } = useToast();
  const [processing, setProcessing] = useState<PaymentOutcome | null>(null);

  const OUTCOMES: { outcome: PaymentOutcome; label: string; cls: string; icon: string; desc: string }[] = [
    { outcome: 'success', label: 'Successful Payment', cls: 'btn-success', icon: '✅', desc: 'Order → PAID, stock consumed' },
    { outcome: 'failure', label: 'Failed Payment',    cls: 'btn-danger',  icon: '❌', desc: 'Order → FAILED, stock released' },
    { outcome: 'timeout', label: 'Payment Timeout',   cls: 'btn-warning', icon: '⏱️', desc: 'Order → EXPIRED, stock released' },
  ];

  async function simulate(outcome: PaymentOutcome) {
    setProcessing(outcome);
    try {
      const key = `payment-${order.id}-${outcome}-${crypto.randomUUID()}`;
      await paymentService.process(order.id, outcome, key);
      toast('success', 'Payment processed', `Outcome: ${outcome}`);
      onUpdate();
    } catch (e: any) {
      toast('error', 'Payment failed', e.message);
    } finally { setProcessing(null); }
  }

  if (order.status !== 'RESERVED') return null;

  return (
    <div className="card mt-6">
      <div className="card-header">
        <h3>💳 Simulate Payment</h3>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Mock gateway</span>
      </div>
      <div className="card-body">
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 20 }}>
          Choose an outcome to simulate the payment gateway response:
        </p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {OUTCOMES.map(({ outcome, label, cls, icon, desc }) => (
            <button
              key={outcome}
              className={`btn ${cls}`}
              onClick={() => simulate(outcome)}
              disabled={processing !== null}
              style={{ flex: 1, minWidth: 160, flexDirection: 'column', height: 'auto', padding: '14px 16px', gap: 6 }}
            >
              {processing === outcome ? (
                <span className="spinner" />
              ) : (
                <>
                  <span style={{ fontSize: '1.4rem' }}>{icon}</span>
                  <span>{label}</span>
                  <span style={{ fontSize: '0.72rem', opacity: 0.8, fontWeight: 400 }}>{desc}</span>
                </>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Order Detail Page ────────────────────────────────────────────────────────
export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [order, setOrder] = useState<Order | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [o, r] = await Promise.all([
        orderService.getById(Number(id)),
        orderService.getReservations(Number(id)),
      ]);
      setOrder(o);
      setReservations(r);
    } catch (e: any) {
      toast('error', 'Could not load order', e.message);
    } finally { setLoading(false); }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function cancelOrder() {
    if (!order) return;
    setCancelling(true);
    try {
      const updated = await orderService.cancel(order.id);
      setOrder(updated);
      toast('info', 'Order cancelled');
      load(); // refresh reservations too
    } catch (e: any) {
      toast('error', 'Cancel failed', e.message);
    } finally { setCancelling(false); }
  }

  const CANCELLABLE: Order['status'][] = ['RESERVED', 'PAID'];

  if (loading) return (
    <div className="loading-screen" style={{ minHeight: '60vh' }}>
      <span className="spinner" /><span>Loading order…</span>
    </div>
  );

  if (!order) return (
    <div className="page-body">
      <div className="empty-state card" style={{ padding: 60 }}>
        <div className="empty-icon">❌</div>
        <p>Order not found.</p>
      </div>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="flex items-center gap-3">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/orders')}>← Back</button>
          <h1>Order #{order.id}</h1>
          <StatusBadge status={order.status} />
        </div>
        <p>Created {new Date(order.created_at).toLocaleString()} · Last updated {new Date(order.updated_at).toLocaleString()}</p>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ gap: 20, alignItems: 'start' }}>

          {/* Left column */}
          <div>
            {/* Summary */}
            <div className="card mb-4">
              <div className="card-header"><h3>📋 Summary</h3></div>
              <div className="card-body">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  {[
                    ['Order ID', `#${order.id}`],
                    ['Cart ID', `#${order.cart_id}`],
                    ['Status', null],
                    ['Total', `$${Number(order.total_amount).toFixed(2)}`],
                  ].map(([label, value]) => (
                    <div key={label as string}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                        {label}
                      </div>
                      {label === 'Status'
                        ? <StatusBadge status={order.status} />
                        : <div style={{ fontWeight: 600 }}>{value}</div>
                      }
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  Key: {order.idempotency_key}
                </div>
              </div>
            </div>

            {/* Items */}
            <div className="card">
              <div className="card-header"><h3>🛍️ Items</h3></div>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map(item => (
                    <tr key={item.id}>
                      <td className="td-muted font-mono">#{item.product_id}</td>
                      <td>{item.quantity}</td>
                      <td>${Number(item.unit_price).toFixed(2)}</td>
                      <td style={{ fontWeight: 600 }}>${(Number(item.unit_price) * item.quantity).toFixed(2)}</td>
                    </tr>
                  ))}
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-secondary)' }}>Total</td>
                    <td style={{ fontWeight: 700, fontSize: '1.05rem' }}>${Number(order.total_amount).toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Right column */}
          <div>
            {/* Reservations */}
            <div className="card">
              <div className="card-header"><h3>🔒 Reservations</h3></div>
              {reservations.length === 0 ? (
                <div className="empty-state"><p>No reservations.</p></div>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Qty</th>
                      <th>Status</th>
                      <th>Expires</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reservations.map(r => (
                      <tr key={r.id}>
                        <td className="td-muted font-mono">#{r.product_id}</td>
                        <td>{r.quantity}</td>
                        <td><StatusBadge status={r.status} /></td>
                        <td>
                          {r.status === 'RESERVED'
                            ? <Countdown expiresAt={r.expires_at} />
                            : <span className="td-muted">{new Date(r.expires_at).toLocaleTimeString()}</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Actions */}
            {CANCELLABLE.includes(order.status) && (
              <div className="card mt-4">
                <div className="card-header"><h3>⚙️ Actions</h3></div>
                <div className="card-body">
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 14 }}>
                    Cancelling a RESERVED order will release stock back to inventory.
                  </p>
                  <button
                    className="btn btn-danger"
                    style={{ width: '100%' }}
                    onClick={cancelOrder}
                    disabled={cancelling}
                  >
                    {cancelling ? <><span className="spinner" /> Cancelling…</> : '🚫 Cancel Order'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Payment simulation panel */}
        <PaymentPanel order={order} onUpdate={load} />
      </div>
    </>
  );
}
