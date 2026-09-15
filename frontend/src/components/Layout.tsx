import React from 'react';
import { NavLink } from 'react-router-dom';

const NAV = [
  { to: '/',        icon: '⚡', label: 'Dashboard' },
  { to: '/products',icon: '📦', label: 'Products'  },
  { to: '/cart',    icon: '🛒', label: 'Cart'      },
  { to: '/orders',  icon: '📋', label: 'Orders'    },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>⚡ POS System</h2>
          <p>Concurrent & Safe</p>
        </div>
        <nav className="sidebar-nav">
          {NAV.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            SELECT FOR UPDATE<br />concurrency safety
          </p>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
