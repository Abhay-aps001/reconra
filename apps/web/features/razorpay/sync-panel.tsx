"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { razorpayApi } from "./api";
import { useRun } from "../reconciliation/run-controller";
import { safeError } from "../../lib/api/errors";

export function RazorpaySyncPanel() {
  const router = useRouter(); const { acceptRun } = useRun(); const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  async function sync() { setBusy(true); setError(null); try { const run = await razorpayApi.sync(); acceptRun(run); router.push(`/workspace?run_id=${encodeURIComponent(run.run_id)}`); } catch (reason) { setError(safeError(reason)); } finally { setBusy(false); } }
  return <section className="data-panel razorpay-panel"><header><p className="mode-label">TEST MODE · READ ONLY</p><h2>Razorpay reconciliation sync</h2><p>Server-configured source retrieval only. No payments, refunds, captures, or settlement changes are available here.</p></header><button className="control-button" disabled={busy} onClick={() => void sync()}>{busy ? "Syncing Test Mode data…" : "Sync Razorpay Test Mode"}</button>{error && <p role="alert" className="notice-error">{error}</p>}<p className="panel-note">If credentials or sandbox data are unavailable, use Demo Reconciliation or Import Data instead. Credentials never leave the server environment.</p></section>;
}
