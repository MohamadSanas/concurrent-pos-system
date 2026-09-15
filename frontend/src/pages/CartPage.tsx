import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cartService } from '../services/cartService';
import { productService } from '../services/productService';
import { useToast } from '../hooks/useToast';
import type { Cart, Product } from '../types';

const CART_KEY = 'pos_cart_id';

function getStoredCartId(): number | null {
  const v = localStorage.getItem(CART_KEY);
  return v ? Number(v) : null;
}

export default function CartPage() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [cart, setCart] = useState<Cart | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [search, setSearch] = useState('');
  const [addingProduct, setAddingProduct] = useState<number | null>(null);
  const [productMap, setProductMap] = useState<Record<number, Product>>({});

  // Load or create cart
  const loadCart = useCallback(async () => {
    const stored = getStoredCartId();
    try {
      if (stored) {
        const c = await cartService.getById(stored);
        setCart(c);
      }
    } catch {
      localStorage.removeItem(CART_KEY);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.all([
      loadCart(),
      productService.getAll().then(p => {
        setProducts(p);
        setProductMap(Object.fromEntries(p.map(x => [x.id, x])));
      }),
    ]);
  }, []);

  async function createCart() {
    const c = await cartService.create();
    localStorage.setItem(CART_KEY, String(c.id));
    setCart(c);
  }

  async function addItem(productId: number) {
    let c = cart;
    if (!c) { c = await cartService.create(); localStorage.setItem(CART_KEY, String(c.id)); setCart(c); }
    setAddingProduct(productId);
    try {
      await cartService.addItem(c.id, productId, 1);
      const updated = await cartService.getById(c.id);
      setCart(updated);
      toast('success', 'Added to cart');
    } catch (e: any) {
      toast('error', 'Could not add item', e.message);
    } finally { setAddingProduct(null); }
  }

  async function updateQty(itemId: number, qty: number) {
    if (!cart) return;
    if (qty < 1) return removeItem(itemId);
    try {
      await cartService.updateItem(cart.id, itemId, qty);
      const updated = await cartService.getById(cart.id);
      setCart(updated);
    } catch (e: any) { toast('error', 'Update failed', e.message); }
  }

  async function removeItem(itemId: number) {
    if (!cart) return;
    try {
      await cartService.removeItem(cart.id, itemId);
      const updated = await cartService.getById(cart.id);
      setCart(updated);
      toast('info', 'Item removed');
    } catch (e: any) { toast('error', 'Remove failed', e.message); }
  }

  async function checkout() {
    if (!cart || cart.items.length === 0) return;
    setCheckingOut(true);
    try {
      const key = `checkout-${cart.id}-${crypto.randomUUID()}`;
      const order = await cartService.checkout(cart.id, key);
      localStorage.removeItem(CART_KEY);
      setCart(null);
      toast('success', '🎉 Order placed!', `Order #${order.id} — ${order.status}`);
      navigate(`/orders/${order.id}`);
    } catch (e: any) {
      toast('error', 'Checkout failed', e.message);
    } finally { setCheckingOut(false); }
  }

  const filteredProducts = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) && p.stock > 0
  );

  const total = cart
    ? cart.items.reduce((s, item) => {
        const p = productMap[item.product_id];
        return s + (p ? Number(p.price) * item.quantity : 0);
      }, 0)
    : 0;

  if (loading) return (
    <div className="loading-screen" style={{ minHeight: '60vh' }}>
      <span className="spinner" /><span>Loading cart…</span>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <h1>Cart</h1>
        <p>Add products, adjust quantities, and checkout</p>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ gap: 24, alignItems: 'start' }}>

          {/* Product catalogue */}
          <div>
            <div className="card-header" style={{ background: 'none', padding: '0 0 16px', border: 'none' }}>
              <h3 style={{ fontSize: '0.95rem' }}>📦 Catalogue</h3>
              <input
                className="form-input"
                style={{ maxWidth: 200, padding: '7px 12px', fontSize: '0.8rem' }}
                placeholder="Search…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <div className="card" style={{ maxHeight: 600, overflowY: 'auto' }}>
              {filteredProducts.length === 0 ? (
                <div className="empty-state"><p>No products available.</p></div>
              ) : filteredProducts.map(p => (
                <div key={p.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 18px', borderBottom: '1px solid var(--border)',
                }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.name}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 2 }}>
                      ${Number(p.price).toFixed(2)} · {p.stock} in stock
                    </div>
                  </div>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => addItem(p.id)}
                    disabled={addingProduct === p.id}
                  >
                    {addingProduct === p.id ? <span className="spinner" /> : '+ Add'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Cart */}
          <div>
            <div className="card-header" style={{ background: 'none', padding: '0 0 16px', border: 'none' }}>
              <h3 style={{ fontSize: '0.95rem' }}>🛒 Cart {cart && <span className="td-muted">(#{cart.id})</span>}</h3>
              {cart && (
                <button className="btn btn-ghost btn-sm" onClick={() => {
                  localStorage.removeItem(CART_KEY); setCart(null);
                }}>Clear</button>
              )}
            </div>

            <div className="card">
              {!cart || cart.items.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🛒</div>
                  <p>Your cart is empty.<br />Add products from the catalogue.</p>
                </div>
              ) : (
                <>
                  {cart.items.map(item => {
                    const product = productMap[item.product_id];
                    return (
                      <div key={item.id} style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '14px 18px', borderBottom: '1px solid var(--border)',
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                            {product?.name ?? `Product #${item.product_id}`}
                          </div>
                          {product && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: 2 }}>
                              ${Number(product.price).toFixed(2)} × {item.quantity} = ${(Number(product.price) * item.quantity).toFixed(2)}
                            </div>
                          )}
                        </div>
                        <div className="qty-controls">
                          <button className="qty-btn" onClick={() => updateQty(item.id, item.quantity - 1)}>−</button>
                          <span className="qty-value">{item.quantity}</span>
                          <button className="qty-btn" onClick={() => updateQty(item.id, item.quantity + 1)}>+</button>
                        </div>
                        <button
                          className="btn btn-danger btn-sm btn-icon"
                          onClick={() => removeItem(item.id)}
                          title="Remove"
                        >🗑️</button>
                      </div>
                    );
                  })}

                  <div style={{ padding: '18px', borderTop: '1px solid var(--border)' }}>
                    <div className="flex justify-between" style={{ marginBottom: 16 }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Subtotal</span>
                      <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>${total.toFixed(2)}</span>
                    </div>
                    <button
                      className="btn btn-success btn-lg"
                      style={{ width: '100%' }}
                      onClick={checkout}
                      disabled={checkingOut}
                    >
                      {checkingOut
                        ? <><span className="spinner" /> Processing…</>
                        : '⚡ Checkout'
                      }
                    </button>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
                      Idempotency key is auto-generated
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
