"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { importApi } from "./api";
import { supportedImportFile, type ImportInspection } from "./types";
import { useRun } from "../reconciliation/run-controller";
import { safeError } from "../../lib/api/errors";

const fields: Record<string, string[]> = {
  bank_transactions: ["transaction_date", "description", "credit_paise", "utr"],
  orders: ["order_id", "created_at", "amount_paise", "status"],
  payments: ["payment_id", "order_id", "amount_paise", "status"],
  reconciliation_rows: ["entity_id", "entry_type", "credit_paise", "debit_paise", "amount_paise", "created_at"],
};
type Mappings = Record<string, Record<string, string>>;

function initialMappings(inspection: ImportInspection): Mappings {
  return Object.fromEntries(inspection.files.map((file) => {
    const used = new Set<string>();
    const mapping: Record<string, string> = {};
    file.suggestions.forEach((suggestion) => { if (!used.has(suggestion.target_field)) { mapping[suggestion.source_column] = suggestion.target_field; used.add(suggestion.target_field); } });
    return [file.filename, mapping];
  }));
}

export function ImportWorkflow() {
  const router = useRouter(); const { acceptRun } = useRun();
  const [inspection, setInspection] = useState<ImportInspection | null>(null);
  const [mappings, setMappings] = useState<Mappings>({});
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<"upload" | "inspect" | "validated">("upload");
  const [busy, setBusy] = useState(false);
  async function inspect(files: FileList | null) {
    const selected = files ? [...files] : [];
    if (!selected.length) return;
    if (selected.some((file) => !supportedImportFile(file))) { setError("Only CSV, XLSX, and text/table PDF files are supported."); return; }
    setBusy(true); setError(null);
    try { const next = await importApi.inspect(selected); setInspection(next); setMappings(initialMappings(next)); setStage("inspect"); }
    catch (reason) { setError(safeError(reason)); } finally { setBusy(false); }
  }
  async function validate() {
    if (!inspection) return; setBusy(true); setError(null);
    try { await importApi.validate(inspection.import_id, mappings); setStage("validated"); }
    catch (reason) { setError(safeError(reason)); } finally { setBusy(false); }
  }
  async function reconcile() {
    if (!inspection) return; setBusy(true); setError(null);
    try { const run = await importApi.reconcile(inspection.import_id); acceptRun(run); router.push(`/workspace?run_id=${encodeURIComponent(run.run_id)}`); }
    catch (reason) { setError(safeError(reason)); } finally { setBusy(false); }
  }
  return <section className="data-panel import-workflow">
    <header><h2>Import source files</h2><p>Inspect before reconciliation</p></header>
    <label className="file-input"><span>CSV, XLSX, or text/table PDF</span><input aria-label="Import source files" type="file" multiple accept=".csv,.xlsx,.pdf,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/pdf" disabled={busy || stage !== "upload"} onChange={(event) => void inspect(event.target.files)} /></label>
    <p className="panel-note">Scanned PDF OCR is not supported. Files are inspected by the backend and are not saved in browser history.</p>
    {error && <p role="alert" className="notice-error">{error}</p>}
    {inspection && <div className="inspection-results"><p className="status-chip">INSPECTED · {inspection.import_id}</p>{inspection.files.map((file) => <article key={file.filename} className="mapping-panel"><h3>{file.filename}</h3><p>{file.source_type} · {file.row_count} rows · Backend classification: <strong>{file.candidate_role}</strong></p><div className="table-scroll"><table><thead><tr>{file.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{file.sample_rows.map((row, index) => <tr key={index}>{file.columns.map((column) => <td key={column}>{row[column]}</td>)}</tr>)}</tbody></table></div><h4>Confirm column mapping</h4><div className="mapping-grid">{file.columns.map((column) => { const suggestion = file.suggestions.find((item) => item.source_column === column); return <label key={column}><span>{column} {suggestion && <small>{Math.round(suggestion.confidence * 100)}% · {suggestion.reason}</small>}</span><select aria-label={`${file.filename} ${column} mapping`} value={mappings[file.filename]?.[column] ?? ""} disabled={busy || stage === "validated"} onChange={(event) => setMappings((current) => { const next = { ...current[file.filename] }; if (event.target.value) next[column] = event.target.value; else delete next[column]; return { ...current, [file.filename]: next }; })}><option value="">Do not map</option>{(fields[file.candidate_role] ?? []).map((field) => <option key={field} value={field}>{field}</option>)}</select></label>; })}</div></article>)}</div>}
    {stage === "inspect" && <button className="control-button" disabled={busy} onClick={() => void validate()}>Confirm mappings and validate</button>}
    {stage === "validated" && <p role="status" className="notice-success">Validation complete. The backend accepted the confirmed mappings.</p>}
    {stage === "validated" && <button className="control-button" disabled={busy} onClick={() => void reconcile()}>Reconcile imported data</button>}
  </section>;
}
