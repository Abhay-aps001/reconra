import type { RunResult } from "./types";
const steps = [
  ["Validated", "VALIDATED"],
  ["Normalized", "NORMALIZED"],
  ["Settlement grouping", "GROUPED_SETTLEMENTS"],
  ["Deterministic matching", "DETERMINISTIC_COMPLETE"],
  ["Residual investigation", "RESIDUAL_INVESTIGATION"],
  ["Verification", "VERIFICATION"],
  ["Tie-out", "TIE_OUT"],
];
export function Progress({ run }: { run: RunResult | null }) {
  return (
    <section className="progress-panel" aria-label="Reconciliation progress">
      <h2>Processing evidence</h2>
      <p>
        {run
          ? "Backend-reported stages. Unreported stages are not marked complete."
          : "Awaiting backend result"}
      </p>
      <ol className="progress-list">
        {steps.map(([label, code]) => (
          <li key={code}>
            <span>{label}</span>
            <small>
              {run?.stages.includes(code)
                ? "Complete"
                : run
                  ? "Not reported separately"
                  : "Pending backend confirmation"}
            </small>
          </li>
        ))}
      </ol>
    </section>
  );
}
