---
name: finance-controller
description: Apply Reconra deterministic-first finance-control rules to reconciliation, agent, Razorpay, and evaluation work.
---

# Reconra Finance Controller

Use for all Reconra finance engine, reconciliation, residual AI, deterministic verification, Razorpay, audit, generator, and evaluation tasks. The approved design and plan are authoritative; do not alter them without explicit human approval.

## Money and policy invariants

- Store and compute every financial value as integer paise. Never use binary floating point for fees, GST/tax, settlements, ledger values, thresholds, or tie-outs.
- Preserve exact money conservation at all times:

  ```text
  total_bank_credit_paise = explained_bank_credit_paise + unexplained_residual_paise
  ```

- Every applied resolution preserves this equality exactly and is idempotent. Stable run, exception, and action identities prevent duplicate financial impact.
- Fee schedules, GST/tax handling, settlement cycles, working days, holidays, instant-settlement behavior, tolerances, date windows, matching thresholds, and risk thresholds are configurable policy. Do not hard-code universal Razorpay rules.

## Deterministic-first matching

- Run deterministic matching before AI: strong identity matching, settlement-to-bank evidence matching, settlement decomposition, policy-configured tolerances, then supported fuzzy identity matching.
- Fuzzy UTR or narration similarity alone never auto-matches; it needs compatible amount, date, and identity evidence.
- False matches are the critical failure class. Prefer abstention, `REVIEW_REQUIRED`, or `ESCALATED` over unsupported matching.
- The closed enum taxonomy is: `CLEAN_MATCH`, `ROUNDING_VARIANCE`, `FEE_VARIANCE`, `TAX_VARIANCE`, `SETTLEMENT_CUTOFF`, `DELAYED_SETTLEMENT`, `INSTANT_SETTLEMENT_VARIANCE`, `REFUND_NETTED_LATER`, `PARTIAL_REFUND`, `MANGLED_UTR`, `MANGLED_NARRATION`, `DUPLICATE_LEDGER_ROW`, `DUPLICATE_BANK_CREDIT`, `DISPUTE_ADJUSTMENT`, `GENERAL_ADJUSTMENT`, `MISSING_ORDER`, `MISSING_PAYMENT`, `MISSING_SETTLEMENT`, `MISSING_BANK_CREDIT`, `AMOUNT_MISMATCH`, `UNRESOLVABLE`.

## Residual AI, verification, and human review

- AI is residual-only. Send only sanitized, bounded post-deterministic evidence packets: precomputed amount/date differences and settlement breakdowns, candidate IDs, normalized/truncated references, related refund/adjustment counts, known facts, and unresolved reason. Never send raw bank statements or unnecessary personal data.
- AI may classify, compare ambiguous text, rank candidates, state a hypothesis, recommend action, or abstain. It must not calculate money; invent IDs/evidence; change policy; access ground truth; mutate reconciliation/ledger state; or mutate Razorpay.
- Require strict `break_class`, `hypothesis`, `candidate_resolution`, `confidence`, `evidence`, and `recommended_action` proposal schema. Reject malformed/unsupported output safely.
- The deterministic verifier must prove candidate existence, amount/date compatibility, uniqueness/unused status, relationship constraints, evidence existence, break compatibility, money conservation, and no impossible residual state.
- Confidence is never permission. `AUTO_RESOLVED` needs schema validity, verifier pass, supported class, policy-permitted risk, and preserved invariants. Plausible but borderline/high-impact cases are `REVIEW_REQUIRED` for human approval or rejection. Do not retry random alternatives after rejection.
- Insufficient evidence, invalid candidates, failed verification, malformed output, provider failure, timeout, and rate limit are `ESCALATED`. If AI is unavailable, complete deterministic reconciliation, safely escalate residuals, and still generate metrics and artifacts.

## Audit and evaluation integrity

- Every material action creates an audit event with event/run/exception IDs, timestamp, actor, action, evidence, decision, confidence when applicable, verification status, paise impact, and relevant before/after state. Decision audit logs are distinct from technical logs.
- Razorpay is Test Mode only. Official Razorpay MCP is read-only by default. No capture, refund, payout, payment mutation, or other mutation without explicit human authorization for that exact action.
- `engine/` and production runtime must never import `generator/`, ground truth, or synthetic scenario labels. Evaluation harnesses may access truth; production may access input only.
- Freeze held-out data before final matcher evaluation. Do not tune thresholds, policy, generator behavior, or agent behavior against held-out outcomes.
- Run rules-only and rules-plus-agent-plus-verifier evaluation on the identical held-out dataset. Report only actual record-, decision-, and rupee-level results; no fake benchmark or reconciliation numbers.
- Tie out rupees exactly through paise values, with any remaining amount explicit as `unexplained_residual_paise`.