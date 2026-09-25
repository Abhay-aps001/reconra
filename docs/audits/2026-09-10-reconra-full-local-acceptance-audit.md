# Reconra Full Local Acceptance & Security Audit Plan

> **For Codex / agentic execution:** Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to execute this plan task-by-task. Use `superpowers:systematic-debugging` for every failure, `superpowers:test-driven-development` before every fix that changes behavior, and `superpowers:verification-before-completion` before claiming success.
>
> **DO NOT DEPLOY.** Render, Vercel, production domains, production Razorpay, deployment screenshots, and production release operations are explicitly out of scope.

**Goal:** Prove that the local Reconra application is functionally complete, financially safe, secure for its current prototype/Test Mode scope, reproducible from a clean environment, internally consistent, and faithful to the approved implementation plan.

**Architecture under audit:** Next.js + TypeScript frontend; FastAPI backend; isolated pure-Python finance engine; deterministic reconciliation before residual-only AI; deterministic verifier/risk gates after AI; browser IndexedDB recent-run snapshots; backend in-memory RunStore/ImportStore; Razorpay Test Mode read-only integration; CSV/XLSX/text-table PDF import.

**Primary references:**
- `docs/superpowers/specs/2026-08-29-reconra-design.md`
- `docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md`
- root `AGENTS.md`
- `plugins/reconra-finance/skills/finance-controller/SKILL.md`
- current `README.md`
- current docs under `docs/`

---

# 0. Non-Negotiable Execution Rules

## 0.1 Scope
- [ ] Audit only the local product.
- [ ] Do not deploy frontend or backend.
- [ ] Do not create Render/Vercel resources.
- [ ] Do not add production URLs.
- [ ] Do not use production Razorpay credentials.
- [ ] Do not perform production-money operations.
- [ ] Do not add deployment screenshots.
- [ ] Do not run original deployment tasks 26–27.
- [ ] Do not commit or push unless the human explicitly asks later.

## 0.2 Finance safety invariants
- [ ] All money remains integer paise.
- [ ] No floating-point financial arithmetic.
- [ ] Exact conservation remains enforced.
- [ ] Deterministic matching executes before AI.
- [ ] AI only reasons over unresolved residual ambiguity.
- [ ] AI never computes fees, GST, settlement arithmetic, ledger truth, or final tie-out.
- [ ] AI never mutates reconciliation state directly.
- [ ] AI never invents authoritative IDs/evidence.
- [ ] Every AI proposal is strict-schema validated.
- [ ] Every AI proposal is deterministically verified.
- [ ] Risk gates remain authoritative.
- [ ] Unsupported/ambiguous cases abstain, escalate, reject, or require review.
- [ ] False-positive prevention is more important than aggressive auto-resolution.
- [ ] Controller actions are idempotent.
- [ ] Final tie-out is recomputed from authoritative state.
- [ ] Held-out evaluation truth never enters matcher/agent execution.

## 0.3 Product boundary
- [ ] Razorpay remains Test Mode only.
- [ ] Razorpay remains read-only.
- [ ] No capture/refund/payment/settlement mutation controls exist.
- [ ] No production-mode switch exists.
- [ ] No frontend credential fields exist.
- [ ] Do not add a database merely because one does not exist.
- [ ] Do not add authentication merely because one does not exist.
- [ ] Audit current in-memory stores + IndexedDB architecture as designed.
- [ ] If durable DB/auth is a future production need, document it rather than implementing it during this audit unless required to fix a current correctness/security defect.

## 0.4 Locked frontend design
- [ ] Preserve the approved ₹500-inspired design system.
- [ ] Preserve warm ivory/parchment, muted green/sage/olive, charcoal.
- [ ] Preserve the decorative currency-note visual on the landing page.
- [ ] Keep operational screens data-dominant.
- [ ] Do not redesign into generic AI SaaS/glass/purple-gradient/chatbot UI.
- [ ] Fix only real correctness, usability, accessibility, performance, or security defects.

## 0.5 Autonomous behavior
Codex must:
- [ ] Continue through all independent checks automatically.
- [ ] Never stop solely because one external integration lacks credentials.
- [ ] If Razorpay credentials are absent: mark `BLOCKED — EXTERNAL CREDENTIAL REQUIRED`, continue.
- [ ] If AI-provider credentials are absent: mark `BLOCKED — EXTERNAL CREDENTIAL REQUIRED`, continue.
- [ ] Never ask the user to paste secrets.
- [ ] Use already-configured environment variables only.
- [ ] Never print secret values.
- [ ] Never weaken tests to obtain green status.
- [ ] Never change finance semantics merely to satisfy typing/lint.
- [ ] Never fabricate benchmark accuracy/precision/recall/F1.
- [ ] Never claim a pass without fresh evidence.

## 0.6 Mandatory failure workflow
For every failure:
1. Reproduce it.
2. Read exact error/output.
3. Trace root cause.
4. Compare against working repository patterns.
5. Add/strengthen a failing test.
6. Apply the smallest correct fix.
7. Run focused test.
8. Run relevant subsystem regression.
9. Run lint/type checks for touched code.
10. Record evidence in the audit report.

Do not make speculative multi-file fixes.

## 0.7 Severity
Use:
- **CRITICAL** — financial conservation/truth violation, real secret exposure, production-money mutation, arbitrary code/file access, held-out truth leakage, cross-run financial contamination.
- **HIGH** — false-positive reconciliation risk, double-apply, stale mutation, exploitable XSS, credential-leak path, unsafe import collision, serious resource abuse.
- **MEDIUM** — functional failure, persistence inconsistency, CI/portability failure, material docs drift, accessibility blocker, unsafe error leakage without secrets.
- **LOW** — minor UX/polish/nonblocking warnings.

Every finding must include severity, component, reproduction, root cause, fix, tests, verification, remaining risk.

---

# 1. Repository & Git Integrity

## 1.1 State
- [ ] Run `git status --short`.
- [ ] Record current branch.
- [ ] Record current commit SHA.
- [ ] Run `git worktree list`.
- [ ] Identify unmerged local branches/worktrees.
- [ ] Compare current audit branch against `main`.
- [ ] Confirm Tasks 28–30 changes are present.
- [ ] Do not delete any worktree/branch during the audit.

## 1.2 Repository hygiene
Inspect:
- `.gitignore`
- `.github/workflows/`
- `pyproject.toml`
- all package manifests
- `pnpm-lock.yaml`
- `.env.example` if present
- `.next`, Playwright reports, caches, venvs, temp/download paths

Verify:
- [ ] `.env*` secrets are ignored appropriately.
- [ ] `.worktrees/` is ignored.
- [ ] local venvs are ignored.
- [ ] `.next/` is ignored.
- [ ] Python caches are ignored.
- [ ] generated test reports/temp files are ignored.
- [ ] no local-machine absolute path is accidentally committed in runtime source.

## 1.3 Current-tree and Git-history secret scan
Search current files and Git history for likely secret indicators:
- [ ] `rzp_test_`
- [ ] `rzp_live_`
- [ ] `GEMINI_API_KEY`
- [ ] `AIza`
- [ ] `Authorization:`
- [ ] `Basic `
- [ ] `Bearer `
- [ ] `api_key`
- [ ] `secret`
- [ ] `.env`
- [ ] webhook secret patterns
- [ ] high-entropy credential-like literals

Rules:
- redact values in reports;
- never print a full discovered secret;
- do not rotate keys automatically;
- do not rewrite Git history automatically;
- if a real secret was committed, mark HIGH/CRITICAL and state that rotation/remediation is required.

---

# 2. Clean Environment / Reproducibility

## 2.1 Python dependency audit
Verify runtime and dev dependencies are declared:
- [ ] FastAPI/server runtime.
- [ ] pytest.
- [ ] Hypothesis.
- [ ] Ruff.
- [ ] mypy.
- [ ] CSV/XLSX/PDF libraries.
- [ ] Razorpay/client dependency if used.
- [ ] AI-provider dependency if used.
- [ ] no required globally installed package.

## 2.2 Clean Python install
Create a temporary clean venv outside tracked source.
- [ ] Install project with documented runtime/dev method.
- [ ] Do not reuse `artifacts/frontend-sprint/venv313` for this proof.
- [ ] Import API app.
- [ ] Run full backend tests.
- [ ] Run Ruff.
- [ ] Run mypy.
- [ ] Verify startup command from README.

If startup only works through undocumented `PYTHONPATH`, investigate and fix/document the packaging/startup path rather than relying on hidden local state.

## 2.3 Clean frontend install
- [ ] `pnpm install --frozen-lockfile`.
- [ ] frontend unit tests.
- [ ] lint.
- [ ] TypeScript.
- [ ] production build.
- [ ] Playwright serial.

## 2.4 Windows/Linux portability
Because primary development is Windows:
- [ ] inspect path separators.
- [ ] inspect filename/import casing.
- [ ] inspect drive-letter assumptions.
- [ ] inspect absolute local paths.
- [ ] ensure CI commands are Linux-compatible where intended.
- [ ] treat GitHub/Linux CI failures as potential case/path defects, not “CI-only” noise.

---

# 3. Full Baseline Verification

Run and record fresh results:
- [ ] full backend `pytest`.
- [ ] Ruff.
- [ ] mypy over `apps/api engine agent scripts`.
- [ ] saved benchmark tests.
- [ ] CI workflow tests.
- [ ] frontend unit tests.
- [ ] frontend lint.
- [ ] frontend TypeScript.
- [ ] frontend production build.
- [ ] Playwright with `--workers=1`.
- [ ] `git diff --check`.

Record warnings separately. Do not turn deprecation warnings into unrelated refactoring unless they are materially risky.

---

# 4. Finance Engine Deep Audit

## 4.1 Money representation
Search finance engine, API models, import normalization, agent schemas, exports, and frontend parsing.
- [ ] integer paise only.
- [ ] no float fields representing money.
- [ ] no implicit float-producing finance arithmetic.
- [ ] unsafe JS integer values rejected at frontend boundary.
- [ ] money parsing deterministic.

Add/verify tests:
- [ ] 0 paise.
- [ ] 1 paise.
- [ ] large safe integer.
- [ ] maximum supported value.
- [ ] float input.
- [ ] decimal-string edge cases.
- [ ] unsupported negative.
- [ ] explicitly supported refund-like negative behavior if applicable.

## 4.2 Conservation
Verify exact conservation at:
- [ ] normalization output.
- [ ] deterministic match output.
- [ ] residual construction.
- [ ] post-AI verification.
- [ ] post-controller approval.
- [ ] post-controller rejection.
- [ ] imported runs.
- [ ] Razorpay-synced runs.
- [ ] public RunResult.
- [ ] reconciliation summary export.

Any uncovered transition must receive a regression test.

## 4.3 Deterministic matching
Test:
- [ ] exact identifier match.
- [ ] amount/date match.
- [ ] duplicate UTR.
- [ ] duplicate payment ID.
- [ ] duplicate settlement ID.
- [ ] malformed UTR.
- [ ] whitespace/case normalization.
- [ ] same amount/date with different entities.
- [ ] multiple plausible candidates.
- [ ] exact match beats fuzzy candidate.
- [ ] unsupported ambiguity abstains.
- [ ] permutation/order invariance.

## 4.4 False-positive prevention
Create an explicit ambiguity matrix.
For each ambiguous case, expected status must be unresolved/review/escalation/rejection unless deterministic evidence is sufficient.
- [ ] Never raise auto-resolution rate by weakening safety thresholds.
- [ ] Document evidence that Reconra prefers abstention over wrong match.

---

# 5. AI Residual Reasoning Boundary

## 5.1 Provider input
Trace data sent to AI.
Must not contain:
- [ ] Razorpay key/secret.
- [ ] Authorization headers.
- [ ] environment dump.
- [ ] held-out expected mappings.
- [ ] hidden truth labels.
- [ ] raw uploaded file bytes.
- [ ] unnecessary full-account data.

## 5.2 Provider output
Verify strict parsing rejects:
- [ ] malformed JSON.
- [ ] missing required fields.
- [ ] wrong types.
- [ ] invented candidate IDs.
- [ ] invented evidence IDs.
- [ ] invalid status/action.
- [ ] unsupported extra authority.
- [ ] direct state mutation attempt.

## 5.3 Deterministic verifier adversarial tests
Feed proposals containing:
- [ ] right prose + wrong candidate ID.
- [ ] invented evidence ID.
- [ ] amount mismatch.
- [ ] date mismatch.
- [ ] absent candidate.
- [ ] false certainty among multiple candidates.
- [ ] invalid confidence/status.
- [ ] model arithmetic conflicting with engine.
- [ ] stale proposal.
- [ ] duplicate proposal.

Unsafe proposal must be rejected/gated.

## 5.4 Provider failure tests
Simulate:
- [ ] timeout.
- [ ] invalid credentials.
- [ ] 401/403.
- [ ] 429.
- [ ] 5xx.
- [ ] empty response.
- [ ] malformed response.
- [ ] schema mismatch.
- [ ] network exception.

Expected:
- deterministic result remains valid;
- run is not corrupted;
- no invented resolution;
- safe fallback/status.

## 5.5 Real provider smoke
If valid credentials are already configured:
- [ ] run one controlled live residual reasoning case.
- [ ] verify provider result passes deterministic verifier.
- [ ] verify finance invariants after result.
- [ ] verify no key is logged.

Otherwise mark:
`BLOCKED — EXTERNAL CREDENTIAL REQUIRED`

---

# 6. End-to-End Pipeline Trace

Trace at least one deterministic and one ambiguous case through:
1. raw input
2. normalization
3. deterministic matching
4. residual
5. evidence
6. AI proposal if applicable
7. verifier
8. risk gate
9. status
10. audit
11. controller action if applicable
12. recomputed tie-out
13. public RunResult
14. frontend rendering
15. exports

- [ ] IDs remain consistent.
- [ ] paise values remain consistent.
- [ ] no hidden state mutation bypasses verifier.
- [ ] audit reflects actual transitions.

---

# 7. RunStore / ImportStore Lifecycle & Isolation

This is a priority audit because the backend intentionally has no traditional DB.

## 7.1 Inspect implementation
Document for both stores:
- data structure;
- entry lifecycle;
- max entries;
- TTL;
- eviction;
- cleanup;
- concurrency assumptions;
- restart behavior.

## 7.2 Boundedness
If unbounded:
- [ ] create a failing test showing uncontrolled growth.
- [ ] define a small prototype-safe limit/TTL consistent with existing behavior.
- [ ] implement minimal eviction/cleanup.
- [ ] preserve active run/import functionality.
- [ ] document policy.

Do not add Postgres/MySQL/Mongo as an automatic fix.

## 7.3 Isolation
Test:
- [ ] wrong run ID cannot access another run.
- [ ] wrong import ID cannot access another import.
- [ ] IDs are unique enough.
- [ ] expired IDs fail safely.
- [ ] one import cannot alter another.
- [ ] one run decision cannot mutate another.
- [ ] run/import namespaces cannot cross-contaminate data.

## 7.4 Backend restart
- [ ] create run.
- [ ] persist browser snapshot.
- [ ] restart backend.
- [ ] live backend run disappears as designed.
- [ ] browser saved snapshot survives.
- [ ] UI says `SAVED RUN SNAPSHOT`.
- [ ] authoritative actions disabled.
- [ ] stale snapshot never masquerades as live.

Document in-memory persistence limitation clearly.

---

# 8. IndexedDB / Session Storage

## 8.1 IndexedDB behavior
Verify:
- [ ] schema v1.
- [ ] newest first.
- [ ] max 10.
- [ ] duplicate ID replacement.
- [ ] 11th evicts oldest.
- [ ] corrupt records ignored.
- [ ] unsupported schema ignored.
- [ ] storage failure nonfatal.

## 8.2 Sensitive data
Inspect stored object. Must not contain:
- [ ] Razorpay credentials.
- [ ] AI credentials.
- [ ] Authorization headers.
- [ ] environment variables.
- [ ] raw CSV/XLSX/PDF bytes.
- [ ] raw uploaded documents.
- [ ] held-out truth.
- [ ] unsafe private model internals.

## 8.3 Manual persistence
Test:
- [ ] refresh.
- [ ] browser close/reopen.
- [ ] saved run open.
- [ ] delete.
- [ ] >10 runs.
- [ ] corrupted record.
- [ ] blocked/unavailable storage.
- [ ] backend offline saved snapshot.

## 8.4 Session storage
Verify only safe current-run pointer/reference is stored.
Test:
- [ ] clear storage.
- [ ] stale run ID.
- [ ] invalid run ID.
- [ ] URL run ID versus stale pointer.
- [ ] no wrong-run totals flash/render.

---

# 9. Multi-Tab / Race Conditions

Test:
- [ ] two tabs with different runs.
- [ ] sessionStorage tab isolation.
- [ ] shared IndexedDB consistency.
- [ ] simultaneous history writes.
- [ ] rapid demo double-click.
- [ ] route change during fetch.
- [ ] route change during import.
- [ ] slow old response followed by newer response.
- [ ] old response cannot overwrite new run.
- [ ] double approve.
- [ ] double reject.
- [ ] approve then reject rapidly.
- [ ] retry after timeout.
- [ ] stale proposal conflict.

Any double-application or wrong-run overwrite is HIGH/CRITICAL.

---

# 10. CSV Import

## 10.1 Happy path
Verify upload → inspect → classify → mapping → human confirm → validate → reconcile → history.

## 10.2 Edge cases
Test:
- [ ] UTF-8.
- [ ] BOM.
- [ ] quoted commas.
- [ ] embedded quotes.
- [ ] blank rows.
- [ ] duplicate headers.
- [ ] unknown headers.
- [ ] missing required fields.
- [ ] malformed date.
- [ ] malformed amount.
- [ ] zero.
- [ ] negative.
- [ ] Unicode.
- [ ] long description.
- [ ] duplicate transaction.
- [ ] row-limit boundary.
- [ ] file-size boundary.

## 10.3 Spreadsheet formula injection
Test user-controlled strings beginning:
- `=`
- `+`
- `-`
- `@`

Inspect exported CSV too.
If spreadsheet software could execute a formula from an untrusted text cell, add safe escaping with regression tests while preserving authoritative numeric values.

---

# 11. XLSX Import

Automated + real manual local smoke.

Test:
- [ ] valid workbook.
- [ ] multiple worksheets.
- [ ] empty workbook.
- [ ] formatted currency cells.
- [ ] native date cells.
- [ ] formula cells.
- [ ] computed values.
- [ ] hidden rows/columns behavior.
- [ ] duplicate columns.
- [ ] Unicode.
- [ ] oversized workbook.
- [ ] corrupt workbook.
- [ ] macro-enabled file.

No macro/code execution is permitted.
If `.xlsm` unsupported, reject honestly.

---

# 12. PDF Import

Scope: text/table PDFs only; no OCR.

Test:
- [ ] valid text PDF.
- [ ] valid table PDF.
- [ ] multi-page table.
- [ ] split table.
- [ ] blank PDF.
- [ ] malformed PDF.
- [ ] encrypted/password PDF.
- [ ] image-only scanned PDF.
- [ ] oversized PDF.
- [ ] Unicode.

Expected for scanned/image-only PDF:
- clear unsupported OCR response;
- no fake parsed data.

Inspect parser implementation:
- [ ] no unsafe shell execution.
- [ ] no arbitrary external command.
- [ ] no unintended persistent temp-file leakage.

---

# 13. Import Filename / Path Security

Test:
- [ ] `../file.csv`
- [ ] `..\file.csv`
- [ ] `/tmp/file.csv`
- [ ] `C:\temp\file.csv`
- [ ] UNC-style path
- [ ] encoded traversal
- [ ] Unicode filename
- [ ] trailing dots/spaces
- [ ] extremely long filename

Only safe basename-like behavior should be accepted.

## 13.1 Duplicate filename collision — priority
Upload two different files with exactly the same filename in one import.

Check whether:
- metadata collide;
- mapping keyed by filename overwrites one;
- classification merges incorrectly;
- wrong data reaches reconciliation.

If collision exists:
- write failing regression test;
- fix using stable per-file identity/index;
- preserve user-visible filename;
- verify deterministic mapping.

Cross-file contamination is at least HIGH.

---

# 14. Import Limits / Resource Abuse

Verify current limits and exact boundaries:
- [ ] individual size.
- [ ] combined size.
- [ ] row count.
- [ ] file count if any.

Test:
- [ ] exactly limit.
- [ ] limit + 1.
- [ ] many tiny files.
- [ ] many empty files.
- [ ] repeated near-limit imports.
- [ ] compressed XLSX expansion risk.

Reject before expensive parsing where possible.
If no file-count bound and arbitrary tiny-file fanout is possible, evaluate and add a reasonable prototype-safe cap with tests.

---

# 15. Razorpay Test Mode Integration

## 15.1 Code safety
Search all integration code.
Verify:
- [ ] Test Mode only.
- [ ] read-only only.
- [ ] credentials server-side only.
- [ ] no frontend credential field.
- [ ] no production toggle.
- [ ] no capture.
- [ ] no refund.
- [ ] no payment mutation.
- [ ] no settlement mutation.
- [ ] no hidden generic mutation path.

Any production-money mutation capability is CRITICAL.

## 15.2 Data correctness
Verify:
- [ ] amounts treated as paise.
- [ ] IDs normalized.
- [ ] pagination if needed.
- [ ] empty account.
- [ ] duplicate sync.
- [ ] missing fields.
- [ ] malformed upstream response.
- [ ] deterministic ordering.

## 15.3 Failure handling
Simulate:
- [ ] missing credentials.
- [ ] invalid credentials.
- [ ] 401/403.
- [ ] 429.
- [ ] timeout.
- [ ] 5xx.
- [ ] network failure.
- [ ] partial/malformed response.

No run corruption, no duplicate application, no secret leakage.

## 15.4 Real Test Mode smoke
If valid Test Mode credentials already exist:
- [ ] perform one read-only sync.
- [ ] verify Test Mode data.
- [ ] create authoritative run.
- [ ] verify history.
- [ ] verify exports.
- [ ] inspect browser network/storage for no secret exposure.

Otherwise:
`BLOCKED — EXTERNAL CREDENTIAL REQUIRED`

Never request production credentials.

---

# 16. API Contract

Enumerate FastAPI/OpenAPI routes and compare every frontend request.

Audit at least:
- health;
- demo reconcile;
- run fetch;
- approve/reject;
- artifacts;
- import inspect;
- import validate;
- import reconcile;
- Razorpay sync.

Verify:
- [ ] path.
- [ ] method.
- [ ] content type.
- [ ] request schema.
- [ ] response schema.
- [ ] typed error code.
- [ ] timeout expectations.

Test:
- [ ] invalid method.
- [ ] malformed JSON.
- [ ] 404.
- [ ] 409.
- [ ] 422.
- [ ] 500.
- [ ] unexpected HTML.
- [ ] empty response.
- [ ] malformed JSON response.

Frontend must never interpret malformed response as success.

---

# 17. API Input / Identifier Validation

Test:
- [ ] empty run ID.
- [ ] huge run ID.
- [ ] Unicode.
- [ ] slash/path-like ID.
- [ ] invalid exception ID.
- [ ] missing exception ID.
- [ ] invalid action.
- [ ] oversized JSON.
- [ ] duplicate request.

Identifiers must never become filesystem paths.

---

# 18. Artifact Route Security

Only:
- `reconciled_ledger.csv`
- `exception_worklist.csv`
- `audit_log.json`
- `reconciliation_summary.json`

Test:
- [ ] unknown artifact.
- [ ] `../`.
- [ ] encoded traversal.
- [ ] absolute path.
- [ ] alternate extension.
- [ ] case tricks.

Artifact lookup must be allowlist-driven, never arbitrary file read.
Arbitrary file access is CRITICAL.

---

# 19. Controller Approve/Reject & Idempotency

For eligible proposal:
- [ ] approve once.
- [ ] inspect tie-out.
- [ ] inspect audit.
- [ ] reload.
- [ ] approve same request again.
- [ ] reject after approval.
- [ ] simultaneous approvals.
- [ ] stale proposal.
- [ ] decision against wrong run.
- [ ] decision against saved snapshot.
- [ ] decision after backend restart.

Repeat relevant flow for reject.

Expected:
- no double application;
- stale conflict;
- backend authoritative;
- frontend does not optimistically invent finance state.

---

# 20. Audit Trail

Verify transitions:
- [ ] run creation.
- [ ] deterministic resolution.
- [ ] AI proposal where applicable.
- [ ] verification.
- [ ] escalation/review.
- [ ] approval.
- [ ] rejection.
- [ ] final state relevant to exports.

Audit must have:
- [ ] unique/stable event IDs.
- [ ] deterministic ordering.
- [ ] no frontend mutation.
- [ ] no secret content.
- [ ] no hidden evaluation truth.
- [ ] no raw credential/provider secret.

---

# 21. Export Content & Security

## 21.1 CSV exports
Verify:
- [ ] headers.
- [ ] row counts.
- [ ] identifiers.
- [ ] integer paise/money presentation according to contract.
- [ ] post-decision state updated.
- [ ] no stale artifact.
- [ ] UTF-8.
- [ ] formula-injection safety.

## 21.2 JSON exports
Verify:
- [ ] valid JSON.
- [ ] schema.
- [ ] audit ordering.
- [ ] tie-out.
- [ ] statuses.
- [ ] no NaN/Infinity.
- [ ] no secrets.
- [ ] no hidden truth.

## 21.3 Response metadata
Verify content type, filename/disposition, invalid artifact behavior, path safety.

---

# 22. Frontend RunResult Runtime Validation

Test malformed payloads:
- [ ] missing required field.
- [ ] wrong type.
- [ ] float money.
- [ ] unsafe integer.
- [ ] conservation mismatch.
- [ ] unknown status.
- [ ] malformed ID.
- [ ] malformed exception.
- [ ] malformed audit.

Expected:
- safe error state;
- no stale previous totals;
- never display “reconciled” from invalid finance data.

---

# 23. Frontend Navigation / State

For every actual route:
- [ ] direct open.
- [ ] refresh.
- [ ] back/forward.
- [ ] missing run.
- [ ] invalid run.
- [ ] expired run.
- [ ] saved-only run.
- [ ] backend offline.

Routes include home, workspace, ledger, exceptions, audit, runs, import, Razorpay, methodology.

Verify no stale state bleed and no console errors.

---

# 24. Homepage

Preserve locked design.
Check:
- [ ] demo CTA.
- [ ] import CTA.
- [ ] Razorpay CTA.
- [ ] decorative note asset.
- [ ] reduced motion.
- [ ] no dead buttons.
- [ ] no placeholder/debug copy.
- [ ] no horizontal page overflow.

No redesign.

---

# 25. Workspace

Check:
- [ ] tie-out rail.
- [ ] run overview.
- [ ] progress.
- [ ] residual.
- [ ] complete state.
- [ ] loading.
- [ ] error.
- [ ] saved snapshot.
- [ ] long IDs.
- [ ] large values.
- [ ] zero residual.
- [ ] full residual.

Cross-check every financial display against backend payload.

---

# 26. Ledger

Check:
- [ ] rows.
- [ ] filtering.
- [ ] source labels.
- [ ] evidence drawer.
- [ ] keyboard access.
- [ ] long descriptions.
- [ ] empty state.
- [ ] large table.
- [ ] responsive local scrolling.

Filtering must be display-only and must never alter totals or reconciliation truth.

---

# 27. Exceptions

Verify statuses:
- `AUTO_RESOLVED`
- `REVIEW_REQUIRED`
- `ESCALATED`
- `REJECTED`

Check:
- [ ] allowed actions only.
- [ ] buttons disabled during request.
- [ ] no double-submit.
- [ ] stale conflict.
- [ ] no optimistic finance mutation.
- [ ] saved-snapshot actions disabled.

---

# 28. Runs / History

Check:
- [ ] newest first.
- [ ] max 10.
- [ ] open.
- [ ] delete.
- [ ] duplicate replacement.
- [ ] saved-only label.
- [ ] backend restart.
- [ ] corrupted storage.
- [ ] multiple tabs.

Saved snapshot must never be silently treated as backend authority.

---

# 29. Razorpay Page

Check:
- [ ] `TEST MODE` visible.
- [ ] `READ ONLY` visible.
- [ ] no production control.
- [ ] no secret field.
- [ ] unavailable state.
- [ ] pending state.
- [ ] failure state.
- [ ] success state.
- [ ] no false claim if live smoke blocked.

---

# 30. Methodology Claims

Compare UI/docs claims to source.

Must accurately describe:
- paise-only arithmetic;
- deterministic-first matching;
- residual AI;
- strict proposals;
- deterministic verifier;
- risk gates;
- abstention;
- auditability;
- Test Mode/read-only Razorpay;
- no scanned OCR;
- evaluation truth isolation.

Remove/fix any unsupported claim of guaranteed accuracy, production readiness, OCR support, or persistent server DB.

---

# 31. XSS / UI Injection

Search for:
- `dangerouslySetInnerHTML`;
- raw DOM HTML assignment;
- unsafe URL construction.

Inject adversarial strings into descriptions, UTR/reference, filenames, model text:
- `<script>alert(1)</script>`
- `<img src=x onerror=alert(1)>`
- `javascript:...`

Expected: rendered as inert text or properly sanitized.
Any exploitable XSS is HIGH/CRITICAL.

---

# 32. Error Information Leakage

Trigger representative failures.

Ensure browser/API responses do not expose:
- [ ] absolute filesystem paths.
- [ ] stack traces.
- [ ] environment variables.
- [ ] Razorpay credentials.
- [ ] AI credentials.
- [ ] Authorization headers.
- [ ] sensitive raw third-party errors.

Keep useful typed error codes.

---

# 33. Logging

Search `print`, logging calls, middleware, provider/Razorpay logging.

Ensure logs do not contain:
- credentials;
- Authorization;
- whole env;
- raw uploads;
- unnecessary full financial/customer datasets;
- hidden truth;
- raw provider secrets.

---

# 34. SSRF / Network Boundary

Verify:
- [ ] users cannot provide arbitrary backend-fetch URLs.
- [ ] Razorpay endpoint is server-configured.
- [ ] AI endpoint is server-configured.
- [ ] imports do not fetch remote URLs.
- [ ] artifacts do not proxy arbitrary URLs.

If unexpected arbitrary-fetch support exists, assess SSRF and fix.

---

# 35. Local CORS / API Rewrite

Inspect FastAPI CORS and Next config.

Verify:
- [ ] dev fallback targets `127.0.0.1:8000`.
- [ ] explicit env base URL wins.
- [ ] production build does not silently use localhost.
- [ ] no dangerous credentialed wildcard CORS setup.
- [ ] local `/api` behavior is correct.

Do not add production-domain configuration.

---

# 36. No-Auth / No-Database Boundary

Current design intentionally has no auth and no traditional DB.

Verify documentation states:
- prototype/Test Mode scope;
- server state is in-memory;
- recent run snapshots are local IndexedDB;
- production merchant use would require auth, tenant isolation, durable persistence, encryption/operational controls.

Do not implement auth/database unless required to resolve a current local correctness/security defect.

---

# 37. Resource / Memory Behavior

Exercise:
- many demo runs;
- repeated imports;
- near-limit CSV;
- near-limit XLSX;
- many exceptions;
- large audit.

Observe:
- RunStore growth;
- ImportStore growth;
- browser cap;
- stale references.

If backend stores are unbounded, implement tested bounded lifecycle policy rather than a database.

---

# 38. Timeouts / Retries

Verify timeout/failure behavior for:
- health;
- demo;
- run fetch;
- controller action;
- export;
- import;
- Razorpay;
- AI provider.

Test delayed backend, aborted request, retry.
Retry must never double-apply controller action.

---

# 39. Accessibility

Manual keyboard audit all routes:
- [ ] landmarks.
- [ ] skip link.
- [ ] logical tab order.
- [ ] visible focus.
- [ ] form labels.
- [ ] table column headers.
- [ ] keyboard-reachable scroll containers.
- [ ] drawer/modal behavior.
- [ ] Escape where appropriate.
- [ ] textual statuses.
- [ ] Test Mode not color-only.
- [ ] Saved Snapshot not color-only.
- [ ] reduced motion.
- [ ] 200% zoom without essential clipping.

Fix blockers while preserving design.

---

# 40. Responsive Layout

Inspect:
- 1440px
- 1024px
- 768px
- 390px
- 320px
- landscape phone
- 125% zoom
- 150% zoom
- 200% zoom

All routes:
home, workspace, ledger, exceptions, audit, runs, import, Razorpay, methodology.

Verify no page-level horizontal overflow; tables may use intentional local scrolling.

---

# 41. Browser Compatibility

Required local:
- Chromium/Chrome.
- Edge if available.

Optional:
- Firefox if practical.

Check IndexedDB, downloads, layout, table scroll, uploads.

---

# 42. Performance

Local only.
Check:
- [ ] homepage load.
- [ ] duplicate requests.
- [ ] fetch loops.
- [ ] route transitions.
- [ ] large ledger.
- [ ] large audit.
- [ ] near-limit imports.
- [ ] IndexedDB writes.
- [ ] console warnings/errors.
- [ ] network behavior.

Do not optimize without measured/visible problem.

---

# 43. Benchmark / Evaluation Truthfulness

## 43.1 Truth isolation
Trace held-out truth access.
- [ ] matcher cannot read it.
- [ ] AI cannot read it.
- [ ] evidence builder cannot read it.
- [ ] only evaluator/scorer may read expected mappings.

## 43.2 Saved benchmark
Verify:
- [ ] schema version.
- [ ] `scoring_available=false`.
- [ ] explicit reason.
- [ ] paise conservation.
- [ ] real saved counts only.
- [ ] no timing/machine paths.
- [ ] no fabricated metrics.

Run/regenerate using documented command and compare structure.

## 43.3 Claims
Search docs/UI for unsupported accuracy/precision/recall/F1.
Remove unsupported numerical claims.

A future manually labeled evaluation set may be documented as future work, not fabricated during this audit.

---

# 44. CI

Inspect `.github/workflows/ci.yml`.

Verify:
- [ ] PR trigger.
- [ ] push-to-main trigger.
- [ ] `contents: read`.
- [ ] no unnecessary write permissions.
- [ ] no secrets required.
- [ ] Python install.
- [ ] dev dependencies.
- [ ] pytest.
- [ ] Ruff.
- [ ] mypy.
- [ ] pnpm install.
- [ ] frontend tests.
- [ ] lint.
- [ ] TypeScript.
- [ ] build.
- [ ] Playwright Chromium.
- [ ] Playwright serial `--workers=1`.

Run local workflow structure test.

If current branch is pushed and GitHub Actions can be inspected through available tooling, record the real run. Otherwise:
`BLOCKED — EXTERNAL GITHUB EXECUTION NOT OBSERVED`

Do not modify repository settings.

---

# 45. README / Documentation Reproduction

Read every project document and execute documented local commands exactly.

Verify:
- [ ] install commands.
- [ ] backend startup.
- [ ] frontend startup.
- [ ] tests.
- [ ] env variable names.
- [ ] Test Mode language.
- [ ] AI boundary.
- [ ] import formats.
- [ ] no OCR.
- [ ] no fake URLs.
- [ ] no production-ready claims.
- [ ] no fake metrics.
- [ ] in-memory persistence limitation.
- [ ] IndexedDB history description if documented.

Fix drift.

---

# 46. Manual Local E2E Acceptance

Start backend/frontend using documented commands and complete this flow without code changes mid-run:

1. [ ] homepage.
2. [ ] run curated demo.
3. [ ] workspace.
4. [ ] tie-out.
5. [ ] ledger.
6. [ ] evidence.
7. [ ] exceptions.
8. [ ] approve an eligible item if available.
9. [ ] reject an eligible item in an appropriate scenario.
10. [ ] audit.
11. [ ] final tie-out.
12. [ ] runs/history.
13. [ ] refresh.
14. [ ] reopen saved snapshot.
15. [ ] download all four exports.
16. [ ] inspect export contents.
17. [ ] CSV import.
18. [ ] XLSX import.
19. [ ] text/table PDF import.
20. [ ] scanned PDF rejection.
21. [ ] invalid import.
22. [ ] Razorpay unavailable state or live Test Mode smoke.
23. [ ] methodology.
24. [ ] browser console.
25. [ ] network errors.
26. [ ] IndexedDB/sessionStorage.
27. [ ] backend restart + saved snapshot behavior.

Record evidence.

---

# 47. Full Regression Gate After Fixes

Required final green checks:
- [ ] full backend pytest.
- [ ] Ruff.
- [ ] mypy.
- [ ] saved benchmark tests.
- [ ] CI workflow tests.
- [ ] frontend unit tests.
- [ ] lint.
- [ ] TypeScript.
- [ ] production build.
- [ ] Playwright serial.
- [ ] every new focused audit/security/import/store/race test.
- [ ] `git diff --check`.

No area is complete if only focused tests pass while its regression suite fails.

---

# 48. Final Source/Diff Review

Search final diff for accidental:
- [ ] redesign.
- [ ] finance threshold changes.
- [ ] weakened validation.
- [ ] deleted/disabled tests.
- [ ] unjustified `type: ignore`.
- [ ] `Any` introduced to silence mypy.
- [ ] swallowed exceptions.
- [ ] hard-coded secrets.
- [ ] production Razorpay code.
- [ ] deployment config.
- [ ] fake benchmark metrics.
- [ ] debug prints.
- [ ] local absolute paths.

Run `git diff --check` again.

---

# 49. Audit Report

Create/update:

`docs/audits/reconra-local-audit-report.md`

Use:

```markdown
# Reconra Local Acceptance Audit Report

## Audit Metadata
- Date:
- Branch:
- Commit:
- OS:
- Python:
- Node:
- pnpm:

## Executive Summary
- PASS:
- FIXED:
- BLOCKED:
- OPEN CRITICAL:
- OPEN HIGH:
- OPEN MEDIUM:
- OPEN LOW:

## Finance Safety
...

## Backend
...

## AI Boundary
...

## Razorpay Test Mode
...

## Import Security
...

## Persistence
...

## Frontend
...

## Security
...

## CI / Reproducibility
...

## Documentation
...

## External Credential-Dependent Checks
...

## Findings

### FINDING-001
- Severity:
- Status:
- Component:
- Reproduction:
- Root cause:
- Fix:
- Tests:
- Verification:
- Remaining risk:

## Final Acceptance Matrix
| Area | Status | Evidence |
|---|---|---|
| Finance engine | PASS/FAIL/BLOCKED | ... |

## Final Verdict
READY FOR LOCAL ACCEPTANCE
or
NOT READY FOR LOCAL ACCEPTANCE

## Blocking Items
...
```

Do not claim ready with unresolved CRITICAL/HIGH findings.

External credential checks may remain BLOCKED without failing local acceptance only when unavailable behavior is safe and no false claim is made that live integration was tested.

---

# 50. Machine-Readable Summary

Create:

`docs/audits/reconra-local-audit-summary.json`

Use this shape:

```json
{
  "audit": "reconra-full-local-acceptance",
  "deployment_in_scope": false,
  "overall_status": "PASS",
  "counts": {
    "passed": 0,
    "fixed": 0,
    "blocked": 0,
    "critical_open": 0,
    "high_open": 0,
    "medium_open": 0,
    "low_open": 0
  },
  "external_checks": {
    "razorpay_test_mode_live": "PASS_OR_BLOCKED",
    "ai_provider_live": "PASS_OR_BLOCKED",
    "github_actions_observed": "PASS_OR_BLOCKED"
  },
  "finance_invariants": {
    "integer_paise_only": true,
    "exact_conservation": true,
    "ai_cannot_mutate_truth": true,
    "deterministic_verifier_authoritative": true,
    "false_positive_prevention_verified": true
  }
}
```

Never set `overall_status` to `PASS` if CRITICAL/HIGH remains open.

---

# 51. Stop Conditions

Stop autonomous fixing and report immediately if:
- production Razorpay mutation capability is found;
- real production credential is committed;
- finance conservation violation has unclear root cause;
- reconciliation can be double-applied;
- arbitrary file read/write exists;
- exploitable XSS exists;
- held-out truth reaches matcher/AI;
- cross-run/import financial contamination exists;
- fixing requires changing core finance architecture;
- three attempted fixes for same issue fail;
- required fix contradicts approved design spec.

Report evidence, severity, root cause as far as known, safest next action.
Do not improvise major architecture changes.

---

# 52. Explicitly Out of Scope

Do not perform:
- Render deployment;
- Vercel deployment;
- production domains;
- production environment rollout;
- production Razorpay;
- real-money operations;
- production auth rollout;
- production database rollout;
- multi-tenant architecture;
- deployment screenshots;
- release tagging;
- final public submission;
- marketing/public launch;
- production monitoring infrastructure.

---

# 53. Definition of Local Completion

Reconra is `READY FOR LOCAL ACCEPTANCE` only if:
- [ ] no unresolved CRITICAL.
- [ ] no unresolved HIGH.
- [ ] backend regression green.
- [ ] frontend regression green.
- [ ] Ruff green.
- [ ] mypy green.
- [ ] TypeScript green.
- [ ] production frontend build green.
- [ ] Playwright serial green.
- [ ] benchmark validation green.
- [ ] finance conservation verified across transitions.
- [ ] ambiguity tests demonstrate safe abstention.
- [ ] controller actions idempotent.
- [ ] stale actions rejected.
- [ ] AI boundary verified.
- [ ] AI-provider failure fallback verified.
- [ ] Razorpay remains Test Mode/read-only only.
- [ ] import security passes.
- [ ] duplicate filename behavior safe.
- [ ] RunStore/ImportStore bounded or explicitly proven acceptable.
- [ ] IndexedDB contains no secrets/raw uploads.
- [ ] backend restart/saved snapshot behavior correct.
- [ ] artifact routes allowlisted.
- [ ] exports safe.
- [ ] XSS checks pass.
- [ ] current-tree + Git-history secret scan complete.
- [ ] clean environment installation works.
- [ ] documented startup works.
- [ ] local manual E2E succeeds.
- [ ] no blocking accessibility/responsive defect.
- [ ] docs match implementation.
- [ ] no fabricated benchmark claims.
- [ ] `git diff --check` passes.
- [ ] audit report complete.
- [ ] machine-readable summary complete.

---

# 54. Required Execution Order

1. Repository state + secret baseline.
2. Clean dependency/reproducibility proof.
3. Full baseline test suites.
4. Finance engine invariants.
5. AI/verifier boundary.
6. RunStore/ImportStore lifecycle.
7. CSV/XLSX/PDF imports + import security.
8. Razorpay Test Mode code audit.
9. API/controller/audit/export security.
10. IndexedDB/session/multi-tab/races.
11. Frontend routes and all product functionality.
12. XSS/error/logging/network security.
13. Accessibility/responsive/performance.
14. Benchmark truth isolation.
15. CI/docs reproducibility.
16. Manual local E2E.
17. Full regression gate.
18. Final diff review.
19. Audit report + JSON summary.

Do not skip a phase because previous historical test results were green.

---

# 55. Required Final Codex Response

When the audit is complete, respond with:

`# RECONRA FULL LOCAL AUDIT COMPLETE`

Then provide:
- overall verdict;
- total checks passed;
- defects found;
- defects fixed;
- unresolved CRITICAL/HIGH/MEDIUM/LOW;
- blocked external checks;
- exact final test results;
- finance safety conclusion;
- Razorpay safety conclusion;
- import/security conclusion;
- persistence conclusion;
- frontend conclusion;
- CI/docs conclusion;
- files changed;
- tests added;
- exact paths to:
  - `docs/audits/reconra-local-audit-report.md`
  - `docs/audits/reconra-local-audit-summary.json`

Finish with exactly one of:

`READY FOR LOCAL ACCEPTANCE`

or

`NOT READY FOR LOCAL ACCEPTANCE`

Do not commit, push, deploy, or create external resources unless the human explicitly asks in a later step.
