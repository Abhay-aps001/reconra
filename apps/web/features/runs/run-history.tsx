"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../reconciliation/api";
import { useRun } from "../reconciliation/run-controller";
import { deleteRunSnapshot, getRunSnapshot, listRunSnapshots, type RunSnapshotSummary } from "../../lib/storage/runs";
import { formatINRFromPaise } from "../../lib/format/currency";
import { safeError, ApiError } from "../../lib/api/errors";

export function RunHistory() {
  const router = useRouter();
  const { acceptRun, openSavedSnapshot } = useRun();
  const [runs, setRuns] = useState<RunSnapshotSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const reload = () => void listRunSnapshots().then(setRuns);
  useEffect(reload, []);
  async function open(runId: string) {
    setBusy(runId); setError(null);
    try { acceptRun(await api.run(runId)); }
    catch (reason) {
      const snapshot = await getRunSnapshot(runId);
      if (!(reason instanceof ApiError) || reason.code !== "RUN_NOT_FOUND" || !snapshot) { setError(safeError(reason)); setBusy(null); return; }
      openSavedSnapshot(snapshot.run);
    }
    router.push(`/workspace?run_id=${encodeURIComponent(runId)}`); setBusy(null);
  }
  async function remove(runId: string) { setBusy(runId); await deleteRunSnapshot(runId); reload(); setBusy(null); }
  if (!runs.length) return <div className="empty-state"><h2>No saved runs</h2><p>No reconciliation runs saved yet.</p></div>;
  return <section className="data-panel"><header><h2>Recent reconciliation runs</h2><p>Stored in this browser only</p></header>
    {error && <p role="alert" className="notice-error">{error}</p>}
    <div className="table-scroll"><table><thead><tr><th>Run</th><th>Saved</th><th>Status</th><th>Bank credit</th><th>Explained</th><th>Residual</th><th>Exceptions</th><th>Actions</th></tr></thead><tbody>
      {runs.map((run) => <tr key={run.run_id}><td className="run-reference">{run.run_id}</td><td>{new Date(run.saved_at).toLocaleString()}</td><td>{run.status}</td><td className="money">{formatINRFromPaise(run.total_bank_credit_paise)}</td><td className="money">{formatINRFromPaise(run.explained_bank_credit_paise)}</td><td className="money">{formatINRFromPaise(run.unexplained_residual_paise)}</td><td>{run.exception_count}</td><td><button className="text-button" disabled={busy === run.run_id} onClick={() => void open(run.run_id)}>Open</button> <button className="text-button" disabled={busy === run.run_id} onClick={() => void remove(run.run_id)}>Delete</button></td></tr>)}
    </tbody></table></div>
  </section>;
}
