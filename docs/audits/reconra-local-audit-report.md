# Reconra Local Acceptance Audit Report

## Audit Metadata

- Date: 2026-09-11
- Branch: `feat/evaluation-ci-docs`
- Commit: `99c051e46a450263850d616370b4d71ad3598c45`
- OS: Windows 11
- Python: 3.13.7
- Node: 22.18.0
- pnpm: 10.33.0

## Executive Summary

- PASS: 19 audit areas
- FIXED: 3 findings
- BLOCKED: 3 external checks
- OPEN CRITICAL: 0
- OPEN HIGH: 0
- OPEN MEDIUM: 0
- OPEN LOW: 0

## Finance Safety

Integer paise boundaries, exact conservation, deterministic-first reconciliation, verifier/risk-gate authority, idempotency, controller approval/rejection, residual provider fallback, and generator/truth isolation passed focused and full regression checks. The connected demo reconciled `185990200 = 185001500 + 988700` paise.

## Backend

The clean temporary virtual environment was created outside the repository with the documented dependency commands. The documented Uvicorn command exposed `/api/health` successfully. RunStore and ImportStore are bounded to 20 entries with a 30-minute monotonic TTL; browser snapshots retain only validated public data and cap at 10 entries.

## AI Boundary

Provider input/output validation, malformed/provider-failure fallback, deterministic verification, risk gates, and no-provider behavior are covered by focused regressions. `GEMINI_API_KEY` was unavailable, so live provider execution was not attempted.

## Razorpay Test Mode

Static and regression review confirms server-configured read-only GET endpoints, Test Mode fail-closed configuration, no production toggle, and no mutation controls. Key variables existed locally but `RAZORPAY_ENV` was not `test`; no external request was made.

## Import Security

CSV/XLSX/text-table PDF handling, scanned-PDF rejection, traversal rejection, typed mapping failures, size/row limits, and deterministic mapping were exercised by regression coverage. Duplicate filename mapping/row namespace collision and CSV formula injection were fixed.

## Persistence

Live backend state is intentionally volatile. Connected browser smoke verified a live run across workspace, ledger, exceptions, and audit; existing browser tests verify saved snapshots are visibly non-live and disable authoritative actions and exports.

## Frontend

Unit validation, runtime paise-safety checks, reduced-motion coverage, semantic table/navigation checks, 320px overflow checks, connected local smoke, and serial Playwright passed. The import workflow continues to display user filenames while using opaque per-file IDs internally.

## Security

Current-tree and Git-history indicator scans found no real credential literals; discovered indicators were configuration names and test fixtures. Static review found no `dangerouslySetInnerHTML`, raw HTML assignment, arbitrary fetch endpoint, shell execution, or artifact route bypass. The checked-in benchmark artifact no longer contains a local absolute path.

## CI / Reproducibility

The workflow has PR and push-to-main triggers, `contents: read`, pinned Python/Node/pnpm setup, backend/frontend checks, Chromium installation, and serial Playwright. Frozen-lockfile installation and all local quality gates passed. GitHub Actions execution was not observed from this local audit.

## Documentation

README startup and environment guidance were executed from a clean venv. Documentation accurately states Test Mode/read-only Razorpay, no scanned-PDF OCR, in-memory server state, local IndexedDB history, and saved benchmark limitations.

## External Credential-Dependent Checks

- Razorpay Test Mode live: BLOCKED — `RAZORPAY_ENV=test` was not configured; the service failed closed and no request was made.
- AI provider live: BLOCKED — `GEMINI_API_KEY` was unavailable.
- GitHub Actions observed: BLOCKED — external GitHub execution was not available to this local audit.

## Findings

### FINDING-001

- Severity: MEDIUM
- Status: FIXED
- Component: benchmark artifact portability
- Reproduction: portability scan found a Windows absolute `output_directory` in the checked-in held-out benchmark JSON.
- Root cause: `run_benchmark.py` serialized `str(output_directory)` directly.
- Fix: emit a repository-relative output label when possible and a basename otherwise; sanitized the checked-in artifact.
- Tests: added `test_benchmark_payload_redacts_an_absolute_output_directory`.
- Verification: 14 focused benchmark/saved-benchmark tests, Ruff, and full mypy passed.
- Remaining risk: output labels intentionally do not disclose arbitrary local paths.

### FINDING-002

- Severity: HIGH
- Status: FIXED
- Component: import mapping and generated bank-row IDs
- Reproduction: two uploads named `bank.csv` shared the mapping key and generated row-ID namespace.
- Root cause: display filename served as a stable internal identity.
- Fix: inspection assigns ordered opaque `file_id` values; validation, reconciliation, generated row IDs, and the frontend mapping state use them while retaining the filename for display.
- Tests: added `test_import_keeps_duplicate_filenames_in_separate_mapping_and_row_namespaces`.
- Verification: 15 focused import tests, frontend unit tests, TypeScript, lint, and full mypy passed.
- Remaining risk: user-provided source IDs remain subject to existing canonical duplicate-ID validation.

### FINDING-003

- Severity: MEDIUM
- Status: FIXED
- Component: CSV artifact exports
- Reproduction: identifiers and evidence beginning with `=`, `+`, `-`, or `@` were emitted as active spreadsheet cells.
- Root cause: `csv.DictWriter` quotes CSV syntax but does not neutralize spreadsheet formulas.
- Fix: prefix only formula-like untrusted text cells with an apostrophe. Integer paise fields remain native integer values.
- Tests: added `test_csv_exports_escape_untrusted_formula_like_text_cells`.
- Verification: 18 focused artifact/controller tests, Ruff, and full mypy passed.
- Remaining risk: JSON artifacts remain structured data and do not use spreadsheet formula interpretation.

## Final Acceptance Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Finance engine | PASS | 36 focused finance/verifier/isolation tests; exact connected-demo tie-out |
| Backend/API | PASS | 234 full tests; clean-vm import and health startup |
| AI boundary | PASS | provider schema/fallback/verifier regressions; live check blocked safely |
| Razorpay Test Mode | PASS | read-only/Test Mode regression and fail-closed local configuration |
| Imports and exports | PASS | 15 import and 18 artifact/controller focused tests; collision and formula regressions |
| Persistence | PASS | bounded server stores and browser snapshot regression coverage |
| Frontend | PASS | 38 unit tests; connected local smoke; 30 serial Playwright tests |
| Security | PASS | secret/path/static-boundary scans and targeted regression coverage |
| CI and docs | PASS | workflow tests, clean installs, documented startup proof |
| External integrations | BLOCKED | no AI credential, no Test Mode environment, no GitHub run observation |

## Final Verdict

READY FOR LOCAL ACCEPTANCE

## Blocking Items

No local acceptance blockers. External live checks remain blocked without credentials/configuration and fail closed.
