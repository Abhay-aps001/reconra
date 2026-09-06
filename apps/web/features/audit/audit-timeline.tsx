"use client";
import { useState } from "react";
import type { AuditEvent } from "../reconciliation/types";
import { formatINRFromPaise } from "../../lib/format/currency";
export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  const [page, setPage] = useState(0);
  const pages = Math.ceil(events.length / 20);
  const currentPage = Math.min(page, Math.max(0, pages - 1));
  if (!events.length)
    return <p className="empty-state">No audit events for this run.</p>;
  return (
    <>
      <div className="table-controls">
        <p>
          Page {currentPage + 1} of {pages} · {events.length} audit events
        </p>
        <button
          className="control-button"
          disabled={currentPage === 0}
          onClick={() => setPage(currentPage - 1)}
        >
          Previous events
        </button>
        <button
          className="control-button"
          disabled={currentPage + 1 >= pages}
          onClick={() => setPage(currentPage + 1)}
        >
          Next events
        </button>
      </div>
      <ol className="audit-timeline">
        {[...events]
          .sort((a, b) => a.lifecycle_order - b.lifecycle_order)
          .slice(currentPage * 20, (currentPage + 1) * 20)
          .map((e) => (
            <li key={e.event_id}>
              <div className="audit-order">{e.lifecycle_order}</div>
              <article>
                <header>
                  <span className="status-chip">{e.actor}</span>
                  <h2>{e.action}</h2>
                  <time dateTime={e.timestamp}>
                    {new Date(e.timestamp)
                      .toISOString()
                      .replace("T", " ")
                      .replace(".000Z", " UTC")}
                  </time>
                </header>
                <p>
                  <strong>{e.decision}</strong> · {e.verification_status}
                </p>
                {e.exception_id && (
                  <p className="run-reference">Exception: {e.exception_id}</p>
                )}
                <p>
                  Financial impact{" "}
                  <span className="money">
                    {formatINRFromPaise(e.financial_impact_paise)}
                  </span>
                </p>
                {e.evidence.length > 0 && (
                  <ul className="evidence-list">
                    {e.evidence.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                )}
                <details>
                  <summary>Audit metadata</summary>
                  <dl className="facts stacked">
                    <div>
                      <dt>Event reference</dt>
                      <dd>{e.event_id}</dd>
                    </div>
                    <div>
                      <dt>Run reference</dt>
                      <dd>{e.run_id}</dd>
                    </div>
                  </dl>
                  <pre>
                    {JSON.stringify(
                      {
                        before_state: e.before_state,
                        after_state: e.after_state,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </article>
            </li>
          ))}
      </ol>
    </>
  );
}
