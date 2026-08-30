# Reconra Repository Governance

## Authority and delivery

- `docs/superpowers/specs/2026-08-29-reconra-design.md` and `docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md` are authoritative.
- Do not silently change approved architecture, scope, interfaces, finance policy, evaluation method, or visual contract. Obtain explicit human approval first.
- Execute only the named task. Do not start a later task while required tests are failing.
- The approved Reconra design overrides generic design-skill suggestions.
- Add no dependency without a clear task-specific reason.

## Finance safety

- All financial arithmetic and values use integer paise only; never binary floating point.
- Preserve exact money conservation for every applied resolution and final tie-out.
- `engine/` must never import `generator/`, ground truth, or synthetic scenario labels. Production reconciliation consumes input artifacts only.
- The LLM must never calculate fee, GST/tax, settlement, ledger, or accounting arithmetic.
- The LLM must never directly mutate reconciliation state, ledger state, policy, thresholds, or money values.
- AI proposals require strict schema validation, deterministic verification, and risk gating before any state change.
- False matches are the critical failure class. Prefer abstention, review, or escalation over unsupported matching.
- Resolutions must be idempotent and must create the required audit event.

## Razorpay and secrets

- Razorpay integration is Test Mode only and must fail closed for production configuration.
- Razorpay Official MCP is read-only by default.
- Never capture, refund, pay out, mutate a payment, or perform another Razorpay mutation without explicit human authorization for that exact action.
- Secrets must never appear in prompts, Git, logs, screenshots, frontend code, or committed files.

## Evaluation integrity

- Do not fabricate benchmark, reconciliation, metric, or tie-out numbers.
- Once real engine results exist, do not use mock result data in product surfaces or artifacts.
- Freeze held-out data; do not tune thresholds, policies, generators, or implementation against held-out results.
- Preserve generator/engine and ground-truth isolation. Evaluate deterministic-only and rules-plus-agent modes on the same held-out data.

## Required workflow

- Use `superpowers:test-driven-development` for implementation.
- Use `superpowers:systematic-debugging` for unexpected failures before fixing them.
- Use `superpowers:verification-before-completion` and fresh evidence before claiming a task complete.
- Use the repository-local `finance-controller` skill for finance-engine, reconciliation, agent, Razorpay, generator, and evaluation work.