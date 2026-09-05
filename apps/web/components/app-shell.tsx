import type { ReactNode } from "react";
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Sidebar />
      <div className="app-body">
        <header className="topbar">
          <div className="topbar-context">Settlement reconciliation platform</div>
          <div className="topbar-trust">
            <span className="mode-label"><span className="mode-dot" aria-hidden="true" />Test Mode</span>
            <span className="trust-labels">Secure <i aria-hidden="true">•</i> Private <i aria-hidden="true">•</i> You stay in control</span>
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
