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
      <body><AppShell>{children}</AppShell></body>
    </html>
  );
}
