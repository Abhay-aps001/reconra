import type { TieOut } from "../../features/reconciliation/types";
import { assertTieOut } from "../../features/reconciliation/types";
import { formatINRFromPaise } from "../../lib/format/currency";
export function TieOutRail({ value }: { value: TieOut }) {
  try {
    assertTieOut(value);
  } catch {
    return (
      <p role="alert" className="notice-error">
        Integrity error: bank credit must equal explained plus residual.
      </p>
    );
  }
  return (
    <section className="tie-out" aria-label="Exact tie-out">
      <div>
        <h2>Total bank credit</h2>
        <strong data-testid="tie-total">
          {formatINRFromPaise(value.total_bank_credit_paise)}
        </strong>
      </div>
      <span aria-hidden="true">=</span>
      <div>
        <h2>Explained</h2>
        <strong data-testid="tie-explained">
          {formatINRFromPaise(value.explained_bank_credit_paise)}
        </strong>
      </div>
      <span aria-hidden="true">+</span>
      <div>
        <h2>Unexplained residual</h2>
        <strong data-testid="tie-residual">
          {formatINRFromPaise(value.unexplained_residual_paise)}
        </strong>
      </div>
      <p>
        Exact paise conservation verified. Explained credit is reported as an
        aggregate by the backend.
      </p>
    </section>
  );
}
