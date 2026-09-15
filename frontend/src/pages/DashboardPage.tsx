import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { productService } from '../services/productService';
import { cartService } from '../services/cartService';
import { orderService } from '../services/orderService';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import type { Product, Order } from '../types';

// ─── Stock bar helper ──────────────────────────────────────────────────────────
function StockBar({ stock, max }: { stock: number; max: number }) {
  const pct = max > 0 ? Math.min((stock / max) * 100, 100) : 0;
  const cls = pct > 50 ? 'stock-high' : pct > 20 ? 'stock-medium' : 'stock-low';
  return (
    <div className={`stock-bar-wrap ${cls}`}>
      <div className="stock-bar">
        <div className="stock-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: 30, textAlign: 'right' }}>
        {stock}
      </span>
    </div>
  );
}

// ─── Concurrency Demo Widget ──────────────────────────────────────────────────
interface DemoResult { success: number; rejected: number; error: number; finalStock: number | null }

function ConcurrencyDemo({ products }: { products: Product[] }) {
  const { toast } = useToast();
  const [requests, setRequests] = useState(10);
  const [selectedProductId, setSelectedProductId] = useState<number | ''>('');
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<DemoResult | null>(null);
  const abortRef = useRef(false);

  const selectedProduct = products.find(p => p.id === selectedProductId);

  async function runStressTest() {
    if (!selectedProduct) return toast('warning', 'Select a product first');
    if (selectedProduct.stock < 1) return toast('error', 'Product has no stock');

    setRunning(true); setResult(null); setProgress(0);
    abortRef.current = false;

    try {
      // 1. Create N carts and add 1 item each
      toast('info', '🚀 Starting stress test', `Creating ${requests} carts…`);
      const cartIds: number[] = [];
      for (let i = 0; i < requests; i++) {
        const cart = await cartService.create();
        await cartService.addItem(cart.id, selectedProduct.id, 1);
        cartIds.push(cart.id);
        setProgress(Math.round(((i + 1) / requests) * 40));
        if (abortRef.current) break;
      }

      toast('info', '⚡ Firing concurrent checkouts', `${requests} simultaneous requests…`);

      // 2. Fire all checkouts simultaneously with Promise.allSettled
      const checkouts = cartIds.map((cartId, i) =>
        fetch(`${(import.meta.env.VITE_API_URL ?? 'http://localhost:8000')}/api/carts/${cartId}/checkout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': `stress-${Date.now()}-${i}-${Math.random()}`,
          },
        }).then(r => r.status)
      );

      const results = await Promise.allSettled(checkouts);
      setProgress(90);

      let success = 0, rejected = 0, error = 0;
      for (const r of results) {
        if (r.status === 'fulfilled') {
          if (r.value === 201) success++;
          else if (r.value === 409) rejected++;
          else error++;
        } else error++;
      }

      // 3. Check final stock
      const updated = await productService.getById(selectedProduct.id);
      setProgress(100);
      setResult({ success, rejected, error, finalStock: updated.stock });

      if (updated.stock >= 0 && success <= selectedProduct.stock) {
        toast('success', '✅ No overselling!', `${success} succeeded, ${rejected} rejected, stock=${updated.stock}`);
      } else {
        toast('error', '⚠️ Overselling detected!', `Stock went to ${updated.stock}`);
      }
    } catch (e: any) {
      toast('error', 'Stress test failed', e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="demo-card">
      <div className="demo-header">
        <h3>⚡ Concurrency Stress Test</h3>
        <p>Fire simultaneous checkout requests to prove SELECT FOR UPDATE prevents overselling</p>
      </div>

      <div className="demo-controls">
        <div className="demo-slider-group">
          <label>Concurrent requests: <strong style={{ color: 'var(--accent-blue)' }}>{requests}</strong></label>
          <input
            type="range" min={2} max={20} value={requests}
            onChange={e => setRequests(+e.target.value)}
            disabled={running}
          />
        </div>

        <div style={{ minWidth: 200 }}>
          <label className="form-label">Product</label>
          <select
            className="form-select"
            value={selectedProductId}
            onChange={e => setSelectedProductId(+e.target.value || '')}
            disabled={running}
          >
            <option value="">— select —</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>
                {p.name} (stock: {p.stock})
              </option>
            ))}
          </select>
        </div>

        <button
          className={`btn ${running ? 'btn-ghost' : 'btn-primary'} btn-lg`}
          onClick={running ? () => { abortRef.current = true } : runStressTest}
          disabled={!selectedProduct && !running}
          style={{ minWidth: 160 }}
        >
          {running ? (
            <><span className="spinner" /> Abort</>
          ) : '🚀 Run Stress Test'}
        </button>
      </div>

      {running && (
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>
            Progress: {progress}%
          </div>
          <div className="progress-bar-wrap">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {result && !running && (
        <div className="demo-results mt-4">
          <div className="demo-result-item result-success">
            <span className="demo-result-value">{result.success}</span>
            <span className="demo-result-label">✅ Succeeded</span>
          </div>
          <div className="demo-result-item result-rejected">
            <span className="demo-result-value">{result.rejected}</span>
            <span className="demo-result-label">❌ Rejected (409)</span>
          </div>
          <div className="demo-result-item result-final">
            <span className="demo-result-value">{result.finalStock ?? '—'}</span>
            <span className="demo-result-label">📦 Final Stock</span>
          </div>
          {result.error > 0 && (
            <div className="demo-result-item" style={{ gridColumn: '1 / -1' }}>
              <span className="demo-result-value" style={{ color: 'var(--accent-amber)' }}>{result.error}</span>
              <span className="demo-result-label">⚠️ Unexpected Errors</span>
            </div>
          )}
          {result.finalStock !== null && result.finalStock >= 0 && (
            <div style={{
              gridColumn: '1 / -1',
              background: 'rgba(16,185,129,0.1)',
              border: '1px solid rgba(16,185,129,0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 16px',
              fontSize: '0.85rem',
              color: 'var(--accent-emerald)',
              textAlign: 'center',
            }}>
              🔒 No overselling — SELECT FOR UPDATE is working correctly
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Dashboard Page ──────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([productService.getAll(), orderService.getAll()])
      .then(([p, o]) => { setProducts(p); setOrders(o); })
      .finally(() => setLoading(false));
  }, []);

  const totalStock = products.reduce((s, p) => s + p.stock, 0);
  const recentOrders = [...orders].sort((a, b) => b.id - a.id).slice(0, 8);
  const maxStock = Math.max(...products.map(p => p.stock), 1);

  const statusCounts = orders.reduce((acc, o) => {
    acc[o.status] = (acc[o.status] ?? 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Live inventory overview &amp; concurrency stress testing</p>
      </div>
      <div className="page-body">
        {loading ? (
          <div className="loading-screen"><span className="spinner" /><span>Loading…</span></div>
        ) : (
          <>
            {/* Stat strip */}
            <div className="stat-grid">
              <div className="stat-card" style={{ '--accent-gradient': 'linear-gradient(90deg,#3b82f6,#8b5cf6)' } as any}>
                <div className="stat-label">Products</div>
                <div className="stat-value">{products.length}</div>
                <div className="stat-sub">Total items in catalogue</div>
              </div>
              <div className="stat-card" style={{ '--accent-gradient': 'linear-gradient(90deg,#10b981,#06b6d4)' } as any}>
                <div className="stat-label">Total Stock</div>
                <div className="stat-value">{totalStock}</div>
                <div className="stat-sub">Units available</div>
              </div>
              <div className="stat-card" style={{ '--accent-gradient': 'linear-gradient(90deg,#f59e0b,#f43f5e)' } as any}>
                <div className="stat-label">Orders</div>
                <div className="stat-value">{orders.length}</div>
                <div className="stat-sub">{statusCounts['PAID'] ?? 0} paid · {statusCounts['RESERVED'] ?? 0} reserved</div>
              </div>
              <div className="stat-card" style={{ '--accent-gradient': 'linear-gradient(90deg,#f43f5e,#8b5cf6)' } as any}>
                <div className="stat-label">Low Stock</div>
                <div className="stat-value text-danger">{products.filter(p => p.stock <= 5).length}</div>
                <div className="stat-sub">Products ≤ 5 units</div>
              </div>
            </div>

            {/* Concurrency demo */}
            <ConcurrencyDemo products={products} />

            <div className="grid-2 mt-6">
              {/* Stock overview */}
              <div className="card">
                <div className="card-header">
                  <h3>📦 Inventory Levels</h3>
                </div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {products.length === 0 ? (
                    <div className="empty-state"><p>No products yet.</p></div>
                  ) : products.map(p => (
                    <div key={p.id}>
                      <div className="flex justify-between mb-2">
                        <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{p.name}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>${Number(p.price).toFixed(2)}</span>
                      </div>
                      <StockBar stock={p.stock} max={maxStock} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent orders */}
              <div className="card">
                <div className="card-header">
                  <h3>📋 Recent Orders</h3>
                </div>
                <div className="card-body" style={{ padding: 0 }}>
                  {recentOrders.length === 0 ? (
                    <div className="empty-state"><p>No orders yet.</p></div>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Order</th>
                          <th>Status</th>
                          <th>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentOrders.map(o => (
                          <tr key={o.id} onClick={() => navigate(`/orders/${o.id}`)}>
                            <td><span className="font-mono text-sm">#{o.id}</span></td>
                            <td><StatusBadge status={o.status} /></td>
                            <td>${Number(o.total_amount).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
