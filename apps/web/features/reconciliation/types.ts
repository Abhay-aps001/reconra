import { ApiError } from "../../lib/api/errors";
export interface TieOut {
  total_bank_credit_paise: number;
  explained_bank_credit_paise: number;
  unexplained_residual_paise: number;
}
export type ResolutionStatus =
  | "AUTO_RESOLVED"
  | "REVIEW_REQUIRED"
  | "ESCALATED"
  | "REJECTED";
export interface RunException {
  exception_id: string;
  break_class: string;
  resolution_status: ResolutionStatus;
  financial_impact_paise: number;
  evidence: string[];
}
export interface AuditEvent {
  event_id: string;
  run_id: string;
  timestamp: string;
  actor: string;
  action: string;
  decision: string;
  verification_status: string;
  financial_impact_paise: number;
  exception_id: string | null;
  evidence: string[];
  before_state: Record<string, number>;
  after_state: Record<string, number>;
  lifecycle_order: number;
}
export interface RunResult {
  run_id: string;
  status: "COMPLETED" | "FAILED";
  stages: string[];
  tie_out_summary: TieOut;
  metrics: {
    resolved_records: number;
    escalated: number;
    scoring_available: boolean;
  };
  exceptions: RunException[];
  audit_events: AuditEvent[];
  artifact_names: string[];
}
function invalid(): never {
  throw new ApiError(
    "INVALID_RESPONSE",
    "The engine returned an invalid response. Please refresh the run.",
  );
}
export function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return invalid();
  return value as Record<string, unknown>;
}
export function string(value: unknown): string {
  return typeof value === "string" ? value : invalid();
}
export function paise(value: unknown): number {
  return typeof value === "number" && Number.isSafeInteger(value)
    ? value
    : invalid();
}
function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.map(string) : invalid();
}
function count(value: unknown): number {
  const n = paise(value);
  return n >= 0 ? n : invalid();
}
function states(value: unknown): Record<string, number> {
  return Object.fromEntries(
    Object.entries(object(value)).map(([k, v]) => [k, paise(v)]),
  );
}
export function assertTieOut(t: TieOut) {
  const total = BigInt(paise(t.total_bank_credit_paise)),
    explained = BigInt(paise(t.explained_bank_credit_paise)),
    residual = BigInt(paise(t.unexplained_residual_paise));
  if (
    total < BigInt(0) ||
    explained < BigInt(0) ||
    residual < BigInt(0) ||
    total !== explained + residual
  )
    throw new ApiError(
      "INTEGRITY_ERROR",
      "Integrity error: total bank credit does not equal explained plus residual. This result cannot be displayed as successful.",
    );
}
export function parseRun(value: unknown): RunResult {
  const r = object(value),
    t = object(r.tie_out_summary),
    m = object(r.metrics);
  const tie_out_summary = {
    total_bank_credit_paise: paise(t.total_bank_credit_paise),
    explained_bank_credit_paise: paise(t.explained_bank_credit_paise),
    unexplained_residual_paise: paise(t.unexplained_residual_paise),
  };
  assertTieOut(tie_out_summary);
  if (
    (r.status !== "COMPLETED" && r.status !== "FAILED") ||
    !Array.isArray(r.exceptions) ||
    !Array.isArray(r.audit_events) ||
    typeof m.scoring_available !== "boolean"
  )
    return invalid();
  const run_id = string(r.run_id);
  if (!run_id) return invalid();
  const exceptions = r.exceptions.map((v) => {
    const e = object(v);
    if (
      !["AUTO_RESOLVED", "REVIEW_REQUIRED", "ESCALATED", "REJECTED"].includes(
        string(e.resolution_status),
      )
    )
      return invalid();
    return {
      exception_id: string(e.exception_id),
      break_class: string(e.break_class),
      resolution_status: e.resolution_status as ResolutionStatus,
      financial_impact_paise: paise(e.financial_impact_paise),
      evidence: strings(e.evidence),
    };
  });
  const audit_events = r.audit_events.map((v) => {
    const e = object(v);
    if (
      e.run_id !== run_id ||
      !Number.isFinite(Date.parse(string(e.timestamp)))
    )
      return invalid();
    return {
      event_id: string(e.event_id),
      run_id,
      timestamp: string(e.timestamp),
      actor: string(e.actor),
      action: string(e.action),
      decision: string(e.decision),
      verification_status: string(e.verification_status),
      financial_impact_paise: paise(e.financial_impact_paise),
      exception_id: e.exception_id === null ? null : string(e.exception_id),
      evidence: strings(e.evidence),
      before_state: states(e.before_state),
      after_state: states(e.after_state),
      lifecycle_order: count(e.lifecycle_order),
    };
  });
  if (
    new Set(exceptions.map((e) => e.exception_id)).size !== exceptions.length ||
    new Set(audit_events.map((e) => e.event_id)).size !== audit_events.length
  )
    return invalid();
  return {
    run_id,
    status: r.status,
    stages: strings(r.stages),
    tie_out_summary,
    metrics: {
      resolved_records: count(m.resolved_records),
      escalated: count(m.escalated),
      scoring_available: m.scoring_available,
    },
    exceptions,
    audit_events,
    artifact_names: strings(r.artifact_names),
  };
}
