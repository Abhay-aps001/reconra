# Reconciliation methodology

Reconra uses integer paise for financial values. It does not derive finance values from formatted currency strings or use binary floating point for financial arithmetic.

The deterministic engine first normalizes and validates canonical source records, then attempts supported identity and settlement-to-bank evidence matching. It records the resulting matches, exceptions, and audit events. The final result must conserve money exactly:

    total bank credit = explained bank credit + unexplained residual

Ambiguous residuals are not treated as matches. An optional AI provider may propose structured next steps from sanitized evidence packets, but it cannot calculate fees, taxes, settlement amounts, or ledger values. It also cannot mutate a run.

The backend verifies any proposal deterministically, applies risk gates, preserves idempotency, and records the decision lifecycle. If evidence is insufficient, Reconra escalates or requests review rather than guessing.

This methodology explains product behavior. It is not accounting, legal, or tax advice.
