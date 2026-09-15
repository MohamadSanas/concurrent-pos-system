import React, { useEffect, useState } from 'react';
import { productService } from '../services/productService';
import { useToast } from '../hooks/useToast';
import type { Product, ProductCreate } from '../types';

function ProductModal({
  initial,
  onSave,
  onClose,
}: {
  initial?: Product;
  onSave: (data: ProductCreate) => Promise<void>;
  onClose: () => void;
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    price: initial ? String(initial.price) : '',
    stock: initial?.stock ?? 0,
  });
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({ name: form.name, price: form.price, stock: Number(form.stock) });
      onClose();
    } finally { setSaving(false); }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>{initial ? 'Edit Product' : 'Add Product'}</h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={submit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Name</label>
              <input
                className="form-input"
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                placeholder="Product name"
                required
              />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Price ($)</label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.price}
                  onChange={e => setForm({ ...form, price: e.target.value })}
                  placeholder="0.00"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Stock</label>
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  value={form.stock}
                  onChange={e => setForm({ ...form, stock: +e.target.value })}
                  required
                />
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <><span className="spinner" /> Saving…</> : (initial ? 'Save Changes' : 'Add Product')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ProductsPage() {
  const { toast } = useToast();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Product | undefined>();
  const [deleting, setDeleting] = useState<number | null>(null);

  async function load() {
    try { setProducts(await productService.getAll()); }
    catch (e: any) { toast('error', 'Failed to load products', e.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleSave(data: ProductCreate) {
    if (editing) {
      const updated = await productService.update(editing.id, data);
      setProducts(prev => prev.map(p => p.id === updated.id ? updated : p));
      toast('success', 'Product updated');
    } else {
      const created = await productService.create(data);
      setProducts(prev => [...prev, created]);
      toast('success', 'Product created');
    }
  }

  async function handleDelete(id: number) {
    setDeleting(id);
    try {
      await productService.delete(id);
      setProducts(prev => prev.filter(p => p.id !== id));
      toast('success', 'Product deleted');
    } catch (e: any) {
      toast('error', 'Delete failed', e.message);
    } finally { setDeleting(null); }
  }

  function stockClass(stock: number) {
    if (stock === 0) return 'text-danger';
    if (stock <= 5) return 'text-warning';
    return 'text-success';
  }

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="page-header">
        <h1>Products</h1>
        <p>Manage your product catalogue and inventory</p>
      </div>
      <div className="page-body">
        <div className="flex justify-between items-center mb-4">
          <input
            className="form-input"
            style={{ maxWidth: 300 }}
            placeholder="🔍  Search products…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <button
            className="btn btn-primary"
            onClick={() => { setEditing(undefined); setModalOpen(true); }}
          >
            + Add Product
          </button>
        </div>

        {loading ? (
          <div className="loading-screen"><span className="spinner" /><span>Loading…</span></div>
        ) : (
          <div className="table-wrap card">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Updated</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
                    No products found.
                  </td></tr>
                ) : filtered.map(p => (
                  <tr key={p.id}>
                    <td className="td-muted font-mono">#{p.id}</td>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td>${Number(p.price).toFixed(2)}</td>
                    <td>
                      <span className={`font-mono ${stockClass(p.stock)}`} style={{ fontWeight: 700 }}>
                        {p.stock}
                      </span>
                      {p.stock === 0 && (
                        <span className="badge badge-EXPIRED" style={{ marginLeft: 8 }}>Out of stock</span>
                      )}
                      {p.stock > 0 && p.stock <= 5 && (
                        <span className="badge badge-EXPIRED" style={{ marginLeft: 8 }}>Low</span>
                      )}
                    </td>
                    <td className="td-muted">{new Date(p.updated_at).toLocaleDateString()}</td>
                    <td>
                      <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => { setEditing(p); setModalOpen(true); }}
                        >
                          ✏️ Edit
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(p.id)}
                          disabled={deleting === p.id}
                        >
                          {deleting === p.id ? <span className="spinner" /> : '🗑️'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {modalOpen && (
          <ProductModal
            initial={editing}
            onSave={handleSave}
            onClose={() => setModalOpen(false)}
          />
        )}
      </div>
    </>
  );
}
