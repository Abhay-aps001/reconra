import Link from "next/link";
import type { RunResult } from "./types";
export function RunOverview({ run }: { run: RunResult }) {
  return (
    <div className="run-overview">
      <dl className="facts">
        <div>
          <dt>Exceptions in result</dt>
          <dd>{run.exceptions.length}</dd>
        </div>
        <div>
          <dt>Resolved records</dt>
          <dd>{run.metrics.resolved_records}</dd>
        </div>
        <div>
          <dt>Escalated</dt>
          <dd>{run.metrics.escalated}</dd>
        </div>
      </dl>
      <nav className="run-links" aria-label="Inspect run">
        {[
          ["ledger", "Inspect ledger"],
          ["exceptions", "Investigate exceptions"],
          ["audit", "Follow audit trail"],
        ].map(([route, label]) => (
          <Link
            key={route}
            href={`/${route}?run_id=${encodeURIComponent(run.run_id)}`}
          >
            {label} <span aria-hidden="true">→</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
