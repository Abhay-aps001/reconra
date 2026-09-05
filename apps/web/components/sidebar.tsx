"use client";

import { useState } from "react";
import Link from "next/link";

const navigation = [
  { label: "Workspace", path: "M3 3h6v6H3zM13 3h6v6h-6zM3 13h6v6H3zM13 13h6v6h-6z" },
  { label: "Ledger", path: "M4 3h14v16H4zM8 3v16M8 8h10M8 13h10" },
  { label: "Exceptions", path: "m11 3 9 16H2L11 3ZM11 8v5M11 15v1" },
  { label: "Audit Trail", path: "m11 2 7 3v5c0 5-7 9-7 9s-7-4-7-9V5l7-3ZM7 10l3 3 5-6" },
  { label: "Imports", path: "M3 13v6h16v-6M11 3v11M7 10l4 4 4-4" },
  { label: "Razorpay", path: "M7 3h11l-5 6h4L5 20l4-9H5l2-8Z" },
];

export function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <aside className="sidebar" data-open={open}>
      <div>
        <div className="sidebar-brand-row">
          <Link className="brand" href="/" aria-label="Reconra home">
            <svg className="brand-mark" viewBox="0 0 36 42" aria-hidden="true"><path d="M3 17 9 13v25H3ZM14 7l6-4v27l-6-4ZM25 0h3v22l7 3-10 8Z" fill="currentColor" /></svg>Reconra
          </Link>
          <button className="menu-toggle" type="button" aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen(!open)}>
            Navigation <span aria-hidden="true">{open ? "−" : "+"}</span>
          </button>
        </div>
        <p className="sidebar-caption">Reconcile. Verify. Explain.</p>
      </div>
      <nav id="primary-navigation" aria-label="Primary">
        <ul className="nav-list">
          <li><Link href="/" className="nav-item" aria-current="page">
            <svg className="nav-symbol" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><path d="m3 10 8-7 8 7M5 9v10h12V9M9 19v-6h4v6" /></svg>
            Overview
          </Link></li>
          {navigation.slice(0, 4).map(item => <li key={item.label}>
            <button type="button" className="nav-item" disabled aria-describedby="navigation-availability">
              <svg className="nav-symbol" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" aria-hidden="true"><path d={item.path} /></svg>
              {item.label}
            </button>
          </li>)}
        </ul>
        <hr className="nav-divider" />
        <ul className="nav-list">
          {navigation.slice(4).map(item => <li key={item.label}>
            <button type="button" className="nav-item" disabled aria-describedby="navigation-availability">
              <svg className="nav-symbol" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" aria-hidden="true"><path d={item.path} /></svg>
              {item.label}
            </button>
          </li>)}
        </ul>
        <p className="nav-note" id="navigation-availability">Planned sections are not available yet.</p>
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-mode"><span className="mode-dot" aria-hidden="true" /><div><strong>Test Mode only</strong><span>Entry preview</span></div></div>
        <div className="workspace-identity"><span className="workspace-avatar" aria-hidden="true">N</span><div><strong>Nivara demo</strong><span>Synthetic merchant</span></div></div>
      </div>
    </aside>
  );
}
