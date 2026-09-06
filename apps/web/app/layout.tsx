import {Suspense} from "react";
import { RunProvider } from "../features/reconciliation/run-controller";
import type { Metadata } from "next";
import { AppShell } from "../components/app-shell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Reconra",
  description: "Settlement reconciliation with evidence for every rupee.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-IN">
      <body><Suspense fallback={<p className="empty-state">Preparing reconciliation engine…</p>}><RunProvider><AppShell>{children}</AppShell></RunProvider></Suspense></body>
    </html>
  );
}
