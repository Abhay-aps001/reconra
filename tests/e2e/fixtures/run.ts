// Public API-shaped fixtures for isolated tests only. Never imported by production.
export function runFixture() {
  const event = (
    actor: string,
    action: string,
    order: number,
    decision: string,
  ) => ({
    event_id: `event_${order}`,
    run_id: "run_test",
    timestamp: "2026-09-05T10:00:00Z",
    actor,
    action,
    decision,
    verification_status: "VERIFIED",
    financial_impact_paise: 20000,
    exception_id: "ex_review",
    evidence: ["bank_ref_42", "settlement_ref_7"],
    before_state: {},
    after_state: {},
    lifecycle_order: order,
  });
  return {
    run_id: "run_test",
    status: "COMPLETED",
    stages: [
      "VALIDATED",
      "NORMALIZED",
      "GROUPED_SETTLEMENTS",
      "EXACT_MATCHING_COMPLETE",
      "DETERMINISTIC_COMPLETE",
    ],
    tie_out_summary: {
      total_bank_credit_paise: 100000,
      explained_bank_credit_paise: 70000,
      unexplained_residual_paise: 30000,
    },
    metrics: { resolved_records: 2, escalated: 1, scoring_available: false },
    exceptions: [
      {
        exception_id: "ex_review",
        break_class: "MANGLED_UTR",
        resolution_status: "REVIEW_REQUIRED",
        financial_impact_paise: 20000,
        evidence: ["bank_ref_42", "settlement_ref_7"],
      },
      {
        exception_id: "ex_abstain",
        break_class: "UNRESOLVABLE",
        resolution_status: "ESCALATED",
        financial_impact_paise: 10000,
        evidence: ["unlinked_bank_credit"],
      },
    ],
    audit_events: [
      event("rule_engine", "SETTLEMENT_BANK_MATCH", 1, "MATCHED"),
      event("agent", "AGENT_PROPOSAL", 2, "PROPOSED"),
      event("verifier", "VERIFY_PROPOSAL", 3, "VERIFIED"),
      event("risk_gate", "RISK_DISPOSITION", 4, "REVIEW_REQUIRED"),
    ],
    artifact_names: [
      "audit_log.json",
      "exception_worklist.csv",
      "reconciled_ledger.csv",
      "reconciliation_summary.json",
    ],
  };
}
export const ledgerFixture =
  'record_type,source_id,candidate_id,financial_impact_paise,financial_impact_display,evidence\npayment,pay_1,order_1,0,0.00,order evidence\nsettlement_bank,settlement_ref_7,bank_ref_42,70000,700.00,"bank_ref_42 | quoted ""reference"", verified"\n';
