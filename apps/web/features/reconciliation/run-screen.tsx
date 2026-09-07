"use client";
import type { ReactNode } from "react";
import { useRun } from "./run-controller";
export function RunScreen({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  const { run, phase, error, startDemo, refresh, busy, savedOnly } = useRun();
  return (
    <section className="operational">
      <header className="screen-heading">
        <div>
          <p className="screen-eyebrow">RECONCILIATION CONTROL</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <button
          className="control-button"
          onClick={() => void (run ? refresh() : startDemo())}
          disabled={busy || savedOnly}
        >
          {run ? "Refresh run" : "Run Demo Reconciliation"}
        </button>
      </header>
      {error && (
        <p role="alert" className="notice-error">
          {error}
        </p>
      )}
      {phase !== "idle" ? (
        <p role="status">
          {phase === "preparing"
            ? "Preparing reconciliation engine…"
            : phase === "processing"
              ? "Reconciling source evidence…"
              : "Loading run…"}
        </p>
      ) : run ? (
        <>
          <p className="run-reference">
            {run.run_id} <span className="status-chip">{run.status}</span>
          </p>
          {savedOnly && <p className="snapshot-label" role="status">SAVED RUN SNAPSHOT · Live actions and exports are unavailable.</p>}
          {children}
        </>
      ) : !error ? (
        <div className="empty-state">
          <h2>No active run</h2>
          <p>
            Run Demo Reconciliation to inspect source evidence, exceptions, and
            the audit trail.
          </p>
        </div>
      ) : null}
    </section>
  );
}
