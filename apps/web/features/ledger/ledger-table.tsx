"use client";
import { useEffect, useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import { api } from "../reconciliation/api";
import { useRun } from "../reconciliation/run-controller";
import { parseLedger, type LedgerRow } from "./parse-ledger";
import { safeError, ApiError } from "../../lib/api/errors";
import { formatINRFromPaise } from "../../lib/format/currency";
import { EvidenceDrawer } from "../../components/evidence-drawer";
export function LedgerTable() {
  const { run } = useRun();
  const [rows, setRows] = useState<LedgerRow[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState<string | null>(null),
    [selected, setSelected] = useState<LedgerRow | null>(null),
    [source, setSource] = useState(""),
    [reference, setReference] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    if (!run) return;
    setLoading(true);
    setRows([]);
    setError(null);
    setSelected(null);
    void (async () => {
      try {
        if (!run.artifact_names.includes("reconciled_ledger.csv"))
          throw new ApiError(
            "ARTIFACT_NOT_FOUND",
            "The ledger artifact is not available for this run.",
          );
        const text = await api.artifact(run.run_id, "reconciled_ledger.csv");
        if (typeof text !== "string")
          throw new ApiError(
            "INVALID_ARTIFACT",
            "The ledger artifact is invalid.",
          );
        const parsed = parseLedger(text);
        if (active) setRows(parsed);
      } catch (e) {
        if (active) setError(safeError(e));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [run, attempt]);
  const columns = useMemo<ColumnDef<LedgerRow>[]>(
    () => [
      { accessorKey: "record_type", header: "Source type" },
      {
        accessorKey: "source_id",
        header: "Source reference",
        cell: ({ row }) => (
          <button
            className="text-button"
            aria-label={`Inspect ${row.original.source_id}`}
            onClick={() => setSelected(row.original)}
          >
            {row.original.source_id}
          </button>
        ),
      },
      { accessorKey: "candidate_id", header: "Matched reference" },
      {
        accessorKey: "financial_impact_paise",
        header: "Financial impact",
        cell: ({ row }) => (
          <span className="money">
            {formatINRFromPaise(row.original.financial_impact_paise)}
          </span>
        ),
      },
      {
        accessorKey: "evidence",
        header: "Evidence",
        cell: ({ row }) => (
          <span className="evidence-excerpt">
            {row.original.evidence || "Not available for this run"}
          </span>
        ),
      },
    ],
    [],
  );
  const data = useMemo(
    () =>
      rows.filter(
        (r) =>
          (!source || r.record_type === source) &&
          (!reference ||
            `${r.source_id} ${r.candidate_id}`
              .toLowerCase()
              .includes(reference.toLowerCase())),
      ),
    [rows, source, reference],
  );
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });
  return (
    <section className="data-panel">
      <div className="table-controls">
        <label>
          Source type
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">All sources</option>
            {Array.from(new Set(rows.map((r) => r.record_type))).map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Settlement / reference
          <input
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            placeholder="Search actual references"
          />
        </label>
        <p>
          {loading
            ? "Loading ledger…"
            : `${data.length} of ${rows.length} rows`}
        </p>
      </div>
      {error ? (
        <div role="alert" className="notice-error">
          {error}{" "}
          <button
            className="control-button"
            onClick={() => setAttempt((a) => a + 1)}
          >
            Retry artifact
          </button>
        </div>
      ) : loading ? (
        <p role="status">Loading ledger artifact…</p>
      ) : rows.length === 0 ? (
        <p className="empty-state">No ledger rows for this run.</p>
      ) : (
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Ledger rows"
        >
          <table>
            <thead>
              {table.getHeaderGroups().map((group) => (
                <tr key={group.id}>
                  {group.headers.map((h) => (
                    <th key={h.id} scope="col">
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} onClick={() => setSelected(row.original)}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.length === 0 && (
            <p className="empty-state">No rows match these filters.</p>
          )}
        </div>
      )}
      <p className="panel-note">
        Ledger filters affect rows only. The tie-out above always represents the
        full run. This artifact exposes source references, matched references,
        financial impact, and evidence.
      </p>
      {selected && (
        <EvidenceDrawer
          title="Ledger evidence"
          onClose={() => setSelected(null)}
        >
          <dl className="facts stacked">
            <div>
              <dt>Source type</dt>
              <dd>{selected.record_type}</dd>
            </div>
            <div>
              <dt>Source reference</dt>
              <dd>{selected.source_id}</dd>
            </div>
            <div>
              <dt>Matched reference</dt>
              <dd>{selected.candidate_id}</dd>
            </div>
            <div>
              <dt>Financial impact</dt>
              <dd className="money">
                {formatINRFromPaise(selected.financial_impact_paise)}
              </dd>
            </div>
          </dl>
          <h3>Source evidence</h3>
          <p className="evidence-text">
            {selected.evidence || "Not available for this run"}
          </p>
          <p className="panel-note">
            Amount reconstruction, resolution source, and verifier status are
            not separately exposed by this ledger artifact.
          </p>
        </EvidenceDrawer>
      )}
    </section>
  );
}
