"use client";
import { useState } from "react";
import { useRun } from "../reconciliation/run-controller";
import { EvidenceDrawer } from "../../components/evidence-drawer";
import { ResolutionActions } from "./resolution-actions";
import { formatINRFromPaise } from "../../lib/format/currency";
export function ExceptionList() {
  const { run } = useRun();
  const [selected, setSelected] = useState<string | null>(null),
    [status, setStatus] = useState("active");
  if (!run) return null;
  const rows = run.exceptions.filter(
    (e) =>
      status === "all" ||
      (status === "active"
        ? ["REVIEW_REQUIRED", "ESCALATED"].includes(e.resolution_status)
        : e.resolution_status === status),
  );
  const item = run.exceptions.find((e) => e.exception_id === selected);
  const events = item
    ? run.audit_events
        .filter((e) => e.exception_id === item.exception_id)
        .sort((a, b) => a.lifecycle_order - b.lifecycle_order)
    : [];
  const proposal = events.findLast((e) => e.action === "AGENT_PROPOSAL"),
    verifier = events.findLast((e) => e.action === "VERIFY_PROPOSAL");
  return (
    <section className="data-panel">
      <div className="table-controls">
        <label>
          Exception status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="active">Unresolved / review required</option>
            <option value="all">All exceptions</option>
            {Array.from(
              new Set(run.exceptions.map((e) => e.resolution_status)),
            ).map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <p>{rows.length} exceptions shown</p>
      </div>
      {rows.length === 0 ? (
        <p className="empty-state">No exceptions match this view.</p>
      ) : (
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Exception worklist"
        >
          <table>
            <thead>
              <tr>
                <th>Exception</th>
                <th>Break class</th>
                <th>Amount impact</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr
                  key={e.exception_id}
                  onClick={() => setSelected(e.exception_id)}
                >
                  <td>
                    <button
                      className="text-button"
                      aria-label={`Inspect ${e.exception_id}`}
                      onClick={() => setSelected(e.exception_id)}
                    >
                      {e.exception_id}
                    </button>
                  </td>
                  <td>{e.break_class}</td>
                  <td className="money">
                    {formatINRFromPaise(e.financial_impact_paise)}
                  </td>
                  <td>
                    <span className="status-chip">{e.resolution_status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="panel-note">
        Confidence and resolution source are not separately available in the
        public run response.
      </p>
      {item && (
        <EvidenceDrawer
          title={`Exception ${item.exception_id}`}
          onClose={() => setSelected(null)}
        >
          <span className="status-chip">{item.resolution_status}</span>
          {item.resolution_status === "ESCALATED" && (
            <p className="abstention">
              Reconra refused to guess. This exception remains unresolved and
              requires further evidence.
            </p>
          )}
          <h3>Proposed resolution</h3>
          <p>
            {proposal
              ? `Recorded decision: ${proposal.decision}. Proposal text and candidate details are not available for this run.`
              : "Not available for this run"}
          </p>
          <h3>Evidence</h3>
          {item.evidence.length ? (
            <ul className="evidence-list">
              {item.evidence.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          ) : (
            <p>Not available for this run</p>
          )}
          <h3>Agent confidence</h3>
          <p>Not available for this run</p>
          <h3>Deterministic verifier result</h3>
          <p>{verifier?.verification_status ?? "Not available for this run"}</p>
          {verifier && (
            <p className="run-reference">
              Audit reference: {verifier.event_id}
            </p>
          )}
          <h3>Risk / status</h3>
          <p>
            {item.break_class} · {item.resolution_status}
          </p>
          <h3>Financial impact</h3>
          <p className="impact-amount money">
            {formatINRFromPaise(item.financial_impact_paise)}
          </p>
          <p className="panel-note">
            Exception impact reported by the engine. Current tie-out changes
            only after the backend confirms a decision.
          </p>
          {item.resolution_status === "REVIEW_REQUIRED" ? (
            <ResolutionActions key={item.exception_id} id={item.exception_id} />
          ) : (
            <p role="status">
              {item.resolution_status === "AUTO_RESOLVED" ||
              item.resolution_status === "REJECTED"
                ? "Decision recorded."
                : ""}
            </p>
          )}
          <h3>Decision audit references</h3>
          <ul className="evidence-list">
            {events.map((e) => (
              <li key={e.event_id}>
                {e.actor} · {e.action} · {e.decision}
                <small>{e.event_id}</small>
              </li>
            ))}
          </ul>
        </EvidenceDrawer>
      )}
    </section>
  );
}
