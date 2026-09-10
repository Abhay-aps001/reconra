# Reconra

**AI Finance Controller for Razorpay settlement reconciliation.** Every rupee should have a trail.

Reconra is an evidence-first reconciliation workstation, not a generic finance dashboard or chatbot. It follows a controlled workflow: settlement reconciliation, exception detection, residual reasoning, deterministic verification, controller review, audit trail, and exact tie-out.

## Architecture

- **Frontend:** Next.js and TypeScript.
- **API:** FastAPI and Python.
- **Finance engine:** pure deterministic reconciliation with integer paise.
- **AI boundary:** structured hypotheses for unresolved residual ambiguity only.
- **Verification:** deterministic verifier, risk gates, idempotency, and conservation checks.
- **Storage:** browser-only IndexedDB history, capped at 10 public run snapshots. There is no server database.

See [the architecture guide](docs/architecture/system.md) and [the reconciliation methodology](docs/methodology/reconciliation.md).

## Financial safety

- Every financial value is an integer number of paise.
- The engine enforces bank credit = explained credit + residual.
- Deterministic matching runs before any AI reasoning.
- AI never calculates fees, GST, settlement totals, or accounting values.
- AI cannot mutate reconciliation state directly.
- Proposals pass schema validation, deterministic verification, risk gating, and idempotency checks before a backend decision.
- Reconra abstains, escalates, or requests review when evidence is insufficient.
- Backend responses remain the financial authority; the frontend displays validated results.

## Features

- One-click synthetic demo reconciliation
- Workspace tie-out, ledger evidence, exception review, and audit trail
- Exact backend controller artifacts
- CSV, XLSX, and controlled text/table PDF import inspection and mapping
- Browser-local recent-run history
- Read-only Razorpay **TEST MODE** sync
- Saved benchmark evidence when a fresh benchmark is not intentionally run

Scanned-PDF OCR is not supported.

## Local development

### Prerequisites

- Node.js 22 and pnpm 10.33.0
- Python 3.13

Install the frontend workspace:

    pnpm install --frozen-lockfile

Install backend and developer tooling:

    python -m pip install -r apps/api/requirements.txt
    python -m pip install -e ".[dev]"

Start the API from the repository root:

    python -m uvicorn --app-dir apps/api app.main:app --reload --host 127.0.0.1 --port 8000

Start the frontend in another terminal:

    pnpm --dir apps/web dev

In development, the Next.js rewrite defaults to http://127.0.0.1:8000 when NEXT_PUBLIC_API_BASE_URL is unset. Production never defaults to localhost; configure the backend URL explicitly.

### Windows PowerShell

    & "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m uvicorn --app-dir apps/api app.main:app --reload --host 127.0.0.1 --port 8000
    pnpm --dir apps/web dev

## Environment variables

Core synthetic demo: **none required**.

| Variable | Purpose |
| --- | --- |
| ENVIRONMENT | Backend environment label. |
| NEXT_PUBLIC_API_BASE_URL | Backend base URL for a deployed frontend. |
| GEMINI_API_KEY | Enables the optional Gemini residual reasoner. |
| GEMINI_MODEL | Optional Gemini model override. |
| GROQ_API_KEY | Reserved optional provider configuration. |
| RAZORPAY_ENV | Must be test before Razorpay sync is enabled. |
| RAZORPAY_KEY_ID | Server-side Razorpay Test Mode key identifier. |
| RAZORPAY_KEY_SECRET | Server-side Razorpay Test Mode secret. |

Never commit .env files or place secrets in frontend variables.

## Running checks

Frontend:

    pnpm --dir apps/web test
    pnpm --dir apps/web lint
    pnpm --dir apps/web exec tsc --noEmit
    pnpm --dir apps/web build
    pnpm --dir apps/web exec playwright test --workers=1

Backend:

    ruff check .
    mypy engine apps/api
    pytest -q

## Imports, artifacts, and run history

Imports support CSV, XLSX, and controlled text/table PDF files. The backend inspects files and validates confirmed mappings before reconciliation. Raw uploaded files are not persisted in browser run history.

Live runs can export exact backend artifact bytes for the reconciled ledger, exception worklist, audit log, and summary. A saved browser snapshot is visibly non-live and cannot approve/reject exceptions or export live-only artifacts.

## Razorpay Test Mode

Razorpay is **TEST MODE ONLY** and read-only. Reconra has no production toggle and provides no capture, refund, payout, payment, or settlement mutation controls. Credentials remain server-side.

## Benchmark and evaluation

Generate the deterministic fixtures, then run a deliberate deterministic benchmark:

    python scripts/generate_demo_data.py --dataset all --output data/generated
    python scripts/run_benchmark.py --dataset heldout --mode deterministic

The checked-in [saved benchmark result](docs/evaluation/saved-benchmark.json) is repository-backed fallback evidence, never a live run. Its held-out dataset contains scenario labels and entity IDs but no explicit expected candidate mappings, so scoring_available is false. Reconra therefore makes no accuracy, precision, recall, F1, false-match-rate, or AI-success claims from this artifact.

See [the benchmark guide](docs/evaluation/benchmark.md) for reproducibility and truth isolation.

## Security and limitations

Reconra does not provide authentication, a server database, production Razorpay operations, OCR for scanned PDFs, or general-purpose AI chat. Read [the security model](docs/security.md) for data boundaries and known limitations.

## Deployment

Deployment is intentionally not configured in this repository state. No live frontend or backend URL is claimed here. When a deployment is deliberately configured, set NEXT_PUBLIC_API_BASE_URL and keep integration credentials in the hosting provider secret store.

## Repository structure

    apps/web/        Next.js workstation
    apps/api/        FastAPI boundary
    engine/          deterministic reconciliation engine
    agent/           residual reasoning interfaces and providers
    generator/       isolated synthetic-data generator
    scripts/         benchmark and artifact utilities
    tests/           backend, integration, property, and browser tests
    docs/            architecture, evaluation, methodology, and safety guidance

## Buildathon context

Reconra is an audit-oriented Razorpay settlement reconciliation project: explain the money deterministically, isolate uncertainty, and preserve evidence for every action.

## License

Licensed under the [MIT License](LICENSE).
