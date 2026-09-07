"use client";
import { useState } from "react";
import { api } from "./api";
import { safeError } from "../../lib/api/errors";
import { useRun } from "./run-controller";

const exports = [
  ["reconciled_ledger.csv", "Reconciled ledger CSV", "ledger.csv"],
  ["exception_worklist.csv", "Exception worklist CSV", "exceptions.csv"],
  ["audit_log.json", "Audit JSON", "audit.json"],
  ["reconciliation_summary.json", "Summary JSON", "summary.json"],
] as const;

export function ExportMenu() {
  const { run, savedOnly } = useRun();
  const [error, setError] = useState<string | null>(null);
  if (!run) return null;
  const activeRun = run;
  async function download(name: (typeof exports)[number][0], suffix: string) {
    try {
      setError(null);
      const blob = await api.artifactBlob(activeRun.run_id, name);
      if (!blob.size) throw new Error("empty artifact");
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `reconra-${activeRun.run_id.replace(/[^a-z0-9_-]/gi, "_")}-${suffix}`;
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (reason) { setError(safeError(reason)); }
  }
  return <section className="data-panel export-menu" aria-label="Run exports">
    <header><h2>Controller artifacts</h2><p>Original backend files</p></header>
    {savedOnly ? <p className="panel-note">Exports require a live backend run.</p> : <div className="action-row">
      {exports.map(([name, label, suffix]) => <button key={name} className="control-button" disabled={!activeRun.artifact_names.includes(name)} onClick={() => void download(name, suffix)}>{label}</button>)}
    </div>}
    {error && <p role="alert" className="notice-error">{error}</p>}
  </section>;
}
