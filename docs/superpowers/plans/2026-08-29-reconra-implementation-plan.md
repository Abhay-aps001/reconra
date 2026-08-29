# Reconra Buildathon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with human checkpoints. Use `superpowers:test-driven-development` for each feature or bugfix, `superpowers:systematic-debugging` for unexpected failures, `superpowers:verification-before-completion` before every milestone claim, and `superpowers:requesting-code-review` before merging a major subsystem. Do not execute the whole plan unsupervised in one pass.

**Goal:** Build, test, deploy, and submit Reconra — a zero-cost, evidence-first AI-assisted Razorpay settlement reconciliation workstation that closes the loop from settlement matching through exception resolution, verification, audit, rupee tie-out, and export.

**Architecture:** A Next.js + TypeScript web app talks over HTTPS to a stateless FastAPI service. The API delegates all finance logic to a pure Python reconciliation engine; deterministic matching handles normal records, only residual ambiguity reaches a provider-neutral AI reasoner, and every AI proposal must pass a deterministic verifier and risk gate before it may alter reconciliation state.

**Tech Stack:** Next.js, TypeScript strict mode, Tailwind CSS, Radix primitives, TanStack Table, Zod, React Hook Form, IndexedDB, FastAPI, Python 3.13 with 3.12 fallback, Pydantic, pandas, RapidFuzz, httpx, openpyxl, pdfplumber, Gemini Developer API structured output, pytest, Hypothesis, Ruff, mypy, Playwright, GitHub Actions, Vercel Hobby, Render Free Web Service.

**Spec:** `docs/superpowers/specs/2026-08-29-reconra-design.md`

## Global Constraints

- Submission deadline: **2026-09-04**.
- Solo build; increase working hours rather than silently dropping a required core capability.
- Budget: **₹0**.
- Development environment: **Windows 11 + PowerShell + Codex + VS Code**.
- No authentication, database, subscriptions, or production-money operations.
- Runtime Razorpay integration is **Test Mode only**.
- Razorpay Official MCP is a development aid and is **read-only by default**; no capture, refund, payout, or other mutation unless the human explicitly authorizes it.
- Every financial amount inside the engine is an **integer number of paise**; floats are prohibited for financial arithmetic.
- `engine/` must never import from `generator/`, ground-truth files, or synthetic scenario labels.
- The LLM never computes fees, taxes, settlement totals, or ledger values and never mutates reconciliation state directly.
- A model proposal is admissible only after strict schema validation, deterministic evidence verification, risk gating, idempotency validation, and money-conservation checks.
- False matches are the critical error class. Prefer abstention over an unsupported match.
- Raw bank statements are never sent to the free AI provider; only sanitized residual evidence packets may leave the backend.
- Production CORS must be restricted to the deployed Reconra frontend origin.
- Uploaded files are data only: CSV, `.xlsx`, and controlled text/table PDF. No macros, no `.xlsm`, no scanned-image OCR in v1.
- Single-file upload limit: 10 MB. Combined upload limit: 25 MB. Parsed-row limit: 10,000.
- The frontend is light-first, desktop-first, evidence-driven, dense, and intentionally not a generic AI/SaaS dashboard.
- The Rupee Flow visual is expressive only in the entry/storytelling layer; operational tables stay calm and readable.
- Use Indian numbering for displayed INR amounts and tabular numerals in financial tables.
- No fake performance numbers. Benchmark values must come from the evaluation harness.
- Do not tune the held-out dataset after seeing final results.
- No later implementation task starts while the previous task's required tests are red.
- No secret is pasted into Codex prompts, committed to Git, embedded in screenshots, or stored in frontend code.
- Existing approved design/specification overrides suggestions from generic design skills.
- New dependencies require a clear reason and must be added only in the task that needs them.
- The primary live demo must be usable without login and start the curated reconciliation in one click.
- Deployment must retain an honest saved-benchmark fallback if the free backend is sleeping or temporarily unavailable.

---

# Execution Strategy

## Do not use a mega-prompt

Do **not** tell Codex: “Build Reconra completely.”

The working loop is:

```text
Human selects one task/phase
        ↓
Codex reads spec + this plan + AGENTS.md
        ↓
Codex invokes the required Superpowers/process skill
        ↓
Codex writes failing tests
        ↓
Codex implements the smallest passing change
        ↓
Codex runs the required verification commands
        ↓
Codex fixes failures
        ↓
Codex summarizes exact changes and risks
        ↓
Human reviews the checkpoint
        ↓
Commit
        ↓
Next task
```

Codex edits files directly. The human does **not** copy/paste routine application code into VS Code.

The human manually handles:

- real `.env` values;
- Razorpay key/secret;
- Gemini key;
- GitHub/Vercel/Render authorizations;
- deployment secret entry;
- any sensitive or mutating Razorpay action.

## Recommended Codex execution mode

Use `superpowers:executing-plans` for the main plan because the human wants explicit checkpoints. Allow `superpowers:dispatching-parallel-agents` only for independent read-only review/test work, such as:
- frontend accessibility review while backend unit tests are already green;
- README review while screenshots are being captured;
- architecture-document review independent of code changes.

Do not parallelize two tasks that modify the same subsystem.

---

# Schedule to Submission

The target is to finish feature development **before** September 4. September 4 is for release validation, pitch rehearsal, screenshots, submission, and emergency fixes.

## 29 August — Foundation evening
**Target:** 4–6 focused hours.

- Create public GitHub repo.
- Commit the approved design and implementation plan before code.
- Add project governance (`AGENTS.md`) and repo-local `reconra-finance` plugin with `finance-controller` skill.
- Scaffold Next.js, FastAPI, pure Python engine package, tests, lint/type-check configuration, and GitHub Actions.
- Make `/api/health` work locally.
- Make the Next.js shell call the local health endpoint.
- End with one green CI-quality foundation commit.

## 30 August — Data contracts + generator
**Target:** 10–12 focused hours.

- Implement canonical Pydantic finance models and paise utilities.
- Implement reconciliation policy and break taxonomy.
- Build clean synthetic generator first.
- Build messy generator with fixed seeds and isolated ground truth.
- Generate clean, development-messy, demo, held-out, and stress fixtures.
- Prove generator/engine isolation through tests.
- Do not start AI or UI feature work until the data contracts are green.

## 31 August — Deterministic reconciliation core
**Target:** 10–12 focused hours.

- Implement exact identity matching.
- Implement settlement grouping/decomposition.
- Implement settlement-to-bank matching.
- Implement tolerance policy.
- Implement fuzzy candidate discovery.
- Implement money-conservation and idempotency invariants.
- Implement metrics + benchmark harness.
- Run clean dataset: expected 100% correctness on clean cases.
- Run messy development dataset and debug.
- Freeze thresholds before held-out evaluation.
- Run held-out deterministic-only benchmark and save results.

## 1 September — Agent + verifier + API + Razorpay
**Target:** 10–12 focused hours.

- Implement residual evidence packets.
- Implement provider-neutral reasoner interface.
- Implement Gemini structured-output reasoner.
- Implement disabled/failure fallback.
- Implement deterministic verifier and risk gate.
- Implement audit events.
- Implement auto-resolve/review/escalate state machine.
- Implement in-memory run store and core API endpoints.
- Implement Razorpay Test Mode read/sync integration.
- Run rules-only versus rules+agent ablation benchmark.
- Produce first real controller artifacts.

## 2 September — Import pipeline + core frontend
**Target:** 11–13 focused hours.

- Implement CSV/XLSX/text-table PDF inspection.
- Implement deterministic smart column suggestions.
- Implement mapping confirmation and validation.
- Add optional AI-assisted mapping only for unresolved header mappings if it is reliable; never send raw documents.
- Build design tokens, typography, shell, Rupee Flow entry, workspace, running state.
- Build Run Overview with real backend result.
- Build Tie-Out Rail and metrics.
- Build ledger explorer with real data.
- No mock result numbers.

## 3 September — Exception workflow + deployment + polish
**Target:** 12+ hours if required.

- Build exception workbench.
- Build human approve/reject flow.
- Build audit trail.
- Build exports.
- Build IndexedDB run history.
- Build Import UI, mapping UI, Razorpay sync UI, Methodology page.
- Use installed design skills in the controlled review order.
- Run Playwright critical flows.
- Deploy backend to Render.
- Deploy frontend to Vercel.
- Configure CORS and deployment env vars.
- Verify cold-start state and saved-benchmark fallback.
- Complete README, architecture, benchmark report, and screenshots.
- Target feature/code freeze by end of day.

## 4 September — Release + submission
**Target:** whatever is necessary, but no discretionary redesign.

- Fresh-clone verification.
- Full Python tests, web lint/typecheck/build, Playwright production smoke suite.
- Verify live Demo, Razorpay Test sync, CSV, XLSX, controlled PDF, exports, exception approval, audit trail.
- Warm backend and confirm fallback path.
- Capture final screenshots.
- Re-run benchmark and record exact measured values.
- Finalize 5-minute demo script and rehearse until under 5 minutes.
- Prepare backup demo recording if allowed/appropriate.
- Create release tag.
- Submit early enough to recover from upload/form issues.
- Do not add new features on September 4 unless fixing a release blocker.

---

# File Map

The implementation should converge on the following responsibilities.

```text
reconra/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── workspace/page.tsx
│   │   │   ├── runs/page.tsx
│   │   │   ├── ledger/page.tsx
│   │   │   ├── exceptions/page.tsx
│   │   │   ├── audit/page.tsx
│   │   │   ├── import/page.tsx
│   │   │   ├── razorpay/page.tsx
│   │   │   └── methodology/page.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── rupee-flow/
│   │   │   ├── tie-out/
│   │   │   ├── tables/
│   │   │   ├── status/
│   │   │   └── ui/
│   │   ├── features/
│   │   │   ├── reconciliation/
│   │   │   ├── ledger/
│   │   │   ├── exceptions/
│   │   │   ├── audit/
│   │   │   ├── imports/
│   │   │   ├── razorpay/
│   │   │   └── runs/
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   ├── format/
│   │   │   ├── storage/
│   │   │   └── validation/
│   │   └── public/
│   │
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── errors.py
│       │   ├── routes/
│       │   │   ├── health.py
│       │   │   ├── reconcile.py
│       │   │   ├── runs.py
│       │   │   ├── imports.py
│       │   │   └── razorpay.py
│       │   ├── services/
│       │   │   ├── reconciliation_service.py
│       │   │   ├── run_store.py
│       │   │   ├── import_store.py
│       │   │   ├── import_service.py
│       │   │   └── razorpay_service.py
│       │   └── schemas/
│       │       ├── api.py
│       │       ├── imports.py
│       │       └── razorpay.py
│       └── requirements.txt
│
├── engine/
│   └── reconra/
│       ├── __init__.py
│       ├── models/
│       │   ├── money.py
│       │   ├── order.py
│       │   ├── payment.py
│       │   ├── refund.py
│       │   ├── settlement.py
│       │   ├── bank.py
│       │   ├── adjustment.py
│       │   ├── exception.py
│       │   └── result.py
│       ├── policy/
│       │   ├── reconciliation.py
│       │   └── fees.py
│       ├── normalization/
│       │   ├── ids.py
│       │   ├── text.py
│       │   └── dates.py
│       ├── matching/
│       │   ├── exact.py
│       │   ├── settlement_bank.py
│       │   ├── tolerance.py
│       │   ├── fuzzy.py
│       │   └── candidates.py
│       ├── reconciliation/
│       │   ├── settlement_math.py
│       │   ├── pipeline.py
│       │   └── state.py
│       ├── evidence/
│       │   └── builder.py
│       ├── verification/
│       │   ├── verifier.py
│       │   ├── risk.py
│       │   └── idempotency.py
│       ├── metrics/
│       │   ├── evaluator.py
│       │   └── throughput.py
│       ├── artifacts/
│       │   ├── ledger.py
│       │   ├── exceptions.py
│       │   ├── audit.py
│       │   └── summary.py
│       └── audit/
│           └── events.py
│
├── agent/
│   ├── schemas/
│   │   └── proposal.py
│   ├── prompts/
│   │   └── residual_reasoning.md
│   ├── providers/
│   │   ├── base.py
│   │   ├── gemini.py
│   │   └── disabled.py
│   └── reasoner.py
│
├── generator/
│   ├── src/
│   │   ├── merchant.py
│   │   ├── clean.py
│   │   ├── messy.py
│   │   ├── bank.py
│   │   ├── razorpay_recon.py
│   │   └── truth.py
│   ├── scenarios/
│   │   └── distribution.py
│   └── README.md
│
├── data/
│   ├── fixtures/clean/
│   ├── development/messy/
│   ├── demo/input/
│   ├── demo/ground_truth/
│   ├── heldout/input/
│   ├── heldout/ground_truth/
│   └── samples/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   ├── evaluation/
│   └── e2e/
│
├── scripts/
│   ├── generate_demo_data.py
│   ├── run_benchmark.py
│   └── export_results.py
│
├── plugins/
│   └── reconra-finance/
│       ├── .codex-plugin/plugin.json
│       └── skills/finance-controller/SKILL.md
├── .agents/plugins/marketplace.json
├── .github/workflows/ci.yml
├── docs/superpowers/specs/2026-08-29-reconra-design.md
├── docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md
├── AGENTS.md
├── pyproject.toml
├── pnpm-workspace.yaml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

---

# Task 1: Create the repository and commit the approved contracts

**Files:**
- Create: `docs/superpowers/specs/2026-08-29-reconra-design.md`
- Create: `docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md`
- Create: `.gitignore`
- Create: `LICENSE`

**Interfaces:**
- Consumes: Approved design and implementation plan downloaded by the human.
- Produces: A public Git repository whose first meaningful commit contains the immutable project contract.

- [ ] **Step 1: Create an empty public GitHub repository named `reconra`**

In GitHub, create a public repository named `reconra`. Do not initialize it with a README, `.gitignore`, or license because the local repo will provide them.

- [ ] **Step 2: Clone it from PowerShell**

```powershell
$repoUrl = Read-Host "Paste the HTTPS URL of the new GitHub repository"
$projectsRoot = Read-Host "Paste the folder where you keep projects"
Set-Location $projectsRoot
git clone $repoUrl
Set-Location .\reconra
```

Expected: `git status` reports an empty repository on `main` or the provider's default branch.

- [ ] **Step 3: Create the documentation directories**

```powershell
New-Item -ItemType Directory -Force -Path `
  "docs\superpowers\specs", `
  "docs\superpowers\plans" | Out-Null
```

- [ ] **Step 4: Copy the downloaded design and plan into the repo**

Use File Explorer or PowerShell to place the two approved files at exactly:

```text
docs/superpowers/specs/2026-08-29-reconra-design.md
docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md
```

- [ ] **Step 5: Create baseline `.gitignore`**

Codex may create it, but it must include at minimum:

```gitignore
# Secrets
.env
.env.*
!.env.example

# Python
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# JavaScript
node_modules/
.next/
out/
dist/
.pnpm-store/

# Local/editor
.vscode/
.idea/
.DS_Store
Thumbs.db

# Generated/private evaluation outputs
data/generated/
artifacts/
playwright-report/
test-results/
```

- [ ] **Step 6: Commit the contracts before implementation**

```powershell
git add docs .gitignore LICENSE
git commit -m "docs: lock reconra design and implementation plan"
git push -u origin HEAD
```

Expected: GitHub displays both approved documents before any application code exists.

---

# Task 2: Add Codex governance and the finance-controller skill

**Files:**
- Create: `AGENTS.md`
- Create: `plugins/reconra-finance/.codex-plugin/plugin.json`
- Create: `plugins/reconra-finance/skills/finance-controller/SKILL.md`
- Create: `.agents/plugins/marketplace.json`

**Interfaces:**
- Consumes: Project constraints from the approved spec.
- Produces: Repository-scoped instructions and a discoverable Codex finance skill that constrain every later task.

- [ ] **Step 1: Ask Codex to create the repo governance**

Use this prompt in Codex from the repository root:

```text
We are beginning implementation of Reconra.

Read these files completely before editing anything:
- docs/superpowers/specs/2026-08-29-reconra-design.md
- docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md

Use Superpowers. This is a governance/setup task; do not implement product features yet.

Create the repository-level AGENTS.md and a repo-local Codex plugin named reconra-finance containing one skill named finance-controller. The plugin must follow current Codex plugin conventions with .codex-plugin/plugin.json, skills/finance-controller/SKILL.md, and the repo marketplace at .agents/plugins/marketplace.json.

AGENTS.md must enforce:
- spec and plan are authoritative;
- no silent architecture changes;
- integer-paise financial arithmetic only;
- engine cannot import generator or ground truth;
- LLM cannot perform financial arithmetic or mutate books;
- AI proposals require deterministic verification;
- conservative abstention and false-match priority;
- Razorpay Test Mode only;
- Razorpay Official MCP read-only by default;
- secrets are never exposed;
- design spec overrides generic design skills;
- no mock result data after real engine results exist;
- no new dependency without a reason;
- no next task while required tests fail;
- use TDD for implementation;
- use systematic-debugging for failures;
- use verification-before-completion before claiming a task complete.

The finance-controller skill must encode the same finance-specific rules plus:
- money conservation;
- fee/policy configuration;
- exact break taxonomy from the spec;
- idempotency;
- audit requirements;
- evaluation integrity;
- held-out dataset freeze.

Do not create feature code.
Validate the plugin structure.
Show me the files created and the validation result, then stop.
```

- [ ] **Step 2: Review `AGENTS.md` manually**

Confirm it does **not** contain:
- API secrets;
- instructions to use production Razorpay;
- permission for Razorpay mutations;
- permission for the engine to inspect ground truth;
- permission for design plugins to overwrite the approved visual contract.

- [ ] **Step 3: Verify skill discovery**

Restart/reload Codex if necessary, then ask:

```text
List the project-local Reconra plugin/skills you can see. Do not edit files.
```

Expected: `finance-controller` is discoverable.

- [ ] **Step 4: Commit governance**

```powershell
git add AGENTS.md plugins .agents
git commit -m "chore: add reconra agent governance"
git push
```

---

# Task 3: Scaffold the monorepo and establish green quality gates

**Files:**
- Create: `pnpm-workspace.yaml`
- Create: `package.json`
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `apps/web/**`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/config.py`
- Create: `apps/api/app/routes/health.py`
- Create: `apps/api/requirements.txt`
- Create: `engine/reconra/__init__.py`
- Create: `tests/unit/test_health.py`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: repo governance only.
- Produces:
  - `GET /api/health -> {"status":"ok","environment":"test|development|production"}`
  - importable Python package `reconra`
  - Next.js app reachable at `http://localhost:3000`
  - FastAPI app reachable at `http://localhost:8000`

- [ ] **Step 1: Give Codex the Task 3 boundary**

```text
Execute Task 3 from docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md only.

Use superpowers:test-driven-development.
Read AGENTS.md and the approved spec first.
Do not implement finance logic, AI, imports, Razorpay sync, or visual polish.

Scaffold:
- pnpm workspace with apps/web
- stable Next.js App Router + TypeScript strict + Tailwind + ESLint
- Python package engine/reconra
- FastAPI app in apps/api
- root pyproject.toml configuring pytest, Ruff, and mypy
- root .env.example with empty keys only
- /api/health
- GitHub Actions CI for Python lint/type/test and web lint/type/build

Prefer Python 3.13. If a required dependency fails because of Python version compatibility, stop and report before changing to 3.12.
Finish only when local quality commands are green.
Then summarize and stop.
```

- [ ] **Step 2: Write the failing health test**

The test should assert:

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_returns_ok() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 3: Run the failing test**

From the repo root with the venv active:

```powershell
pytest tests\unit\test_health.py -v
```

Expected: failure before the health route/app exists.

- [ ] **Step 4: Implement the minimal FastAPI app**

Required behavior:

```python
@router.get("/api/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
```

No database connection and no AI/Razorpay call inside health.

- [ ] **Step 5: Verify Python quality**

```powershell
ruff check .
mypy engine apps\api
pytest -q
```

Expected: all pass.

- [ ] **Step 6: Verify frontend quality**

```powershell
pnpm --dir apps/web lint
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web build
```

Expected: all pass.

- [ ] **Step 7: Verify local services**

Terminal 1:

```powershell
uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

Terminal 2:

```powershell
pnpm --dir apps/web dev
```

Open `http://localhost:3000` and `http://localhost:8000/api/health`.

- [ ] **Step 8: Commit**

```powershell
git add .
git commit -m "chore: initialize reconra workspace"
git push
```

---

# Task 4: Implement canonical finance models and paise-only primitives

**Files:**
- Create: `engine/reconra/models/money.py`
- Create: `engine/reconra/models/order.py`
- Create: `engine/reconra/models/payment.py`
- Create: `engine/reconra/models/refund.py`
- Create: `engine/reconra/models/settlement.py`
- Create: `engine/reconra/models/bank.py`
- Create: `engine/reconra/models/adjustment.py`
- Create: `engine/reconra/models/exception.py`
- Create: `engine/reconra/models/result.py`
- Create: `engine/reconra/policy/reconciliation.py`
- Create: `engine/reconra/policy/fees.py`
- Test: `tests/unit/test_money.py`
- Test: `tests/unit/test_models.py`
- Test: `tests/property/test_money_invariants.py`

**Interfaces:**
- Produces:
  - `type Paise = int`
  - `parse_rupees_to_paise(value: str | Decimal | int) -> int`
  - `format_paise_inr(value: int) -> str`
  - Pydantic models `Order`, `Payment`, `Refund`, `SettlementEntry`, `BankTransaction`, `Adjustment`
  - `BreakClass` enum
  - `ResolutionStatus` enum
  - `ReconciliationPolicy`
  - `FeePolicy`

- [ ] **Step 1: Write failing paise tests**

Required examples:

```python
def test_parse_rupees_exactly() -> None:
    assert parse_rupees_to_paise("2749.50") == 274950

def test_no_float_input() -> None:
    with pytest.raises(TypeError):
        parse_rupees_to_paise(2749.50)

def test_indian_formatting() -> None:
    assert format_paise_inr(528419000) == "₹52,84,190.00"
```

- [ ] **Step 2: Run tests and confirm failure**

```powershell
pytest tests\unit\test_money.py -v
```

- [ ] **Step 3: Implement money helpers using `Decimal` only at ingestion boundaries**

Internal financial fields remain `int`. A float input must be rejected rather than silently rounded.

- [ ] **Step 4: Define the exact break enum**

Use these labels only:

```text
CLEAN_MATCH
ROUNDING_VARIANCE
AMOUNT_MISMATCH
FEE_VARIANCE
TAX_VARIANCE
SETTLEMENT_CUTOFF
DELAYED_SETTLEMENT
INSTANT_SETTLEMENT_VARIANCE
REFUND_NETTED_LATER
PARTIAL_REFUND
MANGLED_UTR
MANGLED_NARRATION
DUPLICATE_LEDGER_ROW
DUPLICATE_BANK_CREDIT
DISPUTE_ADJUSTMENT
GENERAL_ADJUSTMENT
MISSING_ORDER
MISSING_PAYMENT
MISSING_SETTLEMENT
MISSING_BANK_CREDIT
UNRESOLVABLE
```

- [ ] **Step 5: Implement Pydantic models**

Every financial field ends in `_paise` and is an `int`. Optional external IDs are explicit `str | None`. Raw source metadata may be kept for audit but may not become a matching shortcut.

- [ ] **Step 6: Add policy models**

`ReconciliationPolicy` must own at least:

```python
class ReconciliationPolicy(BaseModel):
    rounding_tolerance_paise: int
    settlement_date_window_days: int
    utr_similarity_threshold: float
    narration_similarity_threshold: float
    auto_apply_confidence_threshold: float
    review_confidence_threshold: float
    high_impact_review_threshold_paise: int
```

Thresholds are configuration, never buried constants.

- [ ] **Step 7: Add property test for integer money**

Use Hypothesis to generate valid integer amounts and prove serialize/deserialize preserves exact paise and never creates a float-valued financial field.

- [ ] **Step 8: Verify and commit**

```powershell
ruff check engine tests
mypy engine
pytest tests\unit tests\property -q
git add engine tests
git commit -m "feat(engine): add canonical finance models"
git push
```

---

# Task 5: Implement normalization helpers

**Files:**
- Create: `engine/reconra/normalization/ids.py`
- Create: `engine/reconra/normalization/text.py`
- Create: `engine/reconra/normalization/dates.py`
- Test: `tests/unit/test_normalization.py`

**Interfaces:**
- Produces:
  - `normalize_identifier(value: str | None) -> str | None`
  - `normalize_utr(value: str | None) -> str | None`
  - `normalize_narration(value: str | None) -> str`
  - `date_distance_days(a: date, b: date) -> int`

- [ ] **Step 1: Write normalization tests**

Cover:
- whitespace/case normalization;
- UTR punctuation removal without inventing characters;
- clipped narration;
- empty values;
- deterministic date distance.

- [ ] **Step 2: Run failing tests**

```powershell
pytest tests\unit\test_normalization.py -v
```

- [ ] **Step 3: Implement pure deterministic normalization**

Normalization may standardize; it may never infer missing IDs.

- [ ] **Step 4: Verify deterministic behavior**

Run the same input through helpers twice and assert identical output.

- [ ] **Step 5: Commit**

```powershell
git add engine tests
git commit -m "feat(engine): add record normalization"
git push
```

---

# Task 6: Build the synthetic generator with hard ground-truth isolation

**Files:**
- Create: `generator/src/merchant.py`
- Create: `generator/src/razorpay_recon.py`
- Create: `generator/src/bank.py`
- Create: `generator/src/clean.py`
- Create: `generator/src/messy.py`
- Create: `generator/src/truth.py`
- Create: `generator/scenarios/distribution.py`
- Create: `scripts/generate_demo_data.py`
- Create: `generator/README.md`
- Test: `tests/unit/test_generator.py`
- Test: `tests/integration/test_generator_isolation.py`

**Interfaces:**
- Produces:
  - `generate_clean_dataset(seed: int) -> GeneratedDataset`
  - `generate_messy_dataset(seed: int, profile: ScenarioDistribution) -> GeneratedDataset`
  - raw input files separate from `ground_truth.json`
  - fixed seeds for clean, messy, demo, held-out, and stress sets

- [ ] **Step 1: Ask Codex to use the finance-controller skill**

Prompt:

```text
Execute Task 6 only.
Use the project finance-controller skill and superpowers:test-driven-development.

The generator must implement the official Razorpay reconciliation shape from the approved spec and must write inputs separately from ground truth.
The engine is forbidden from importing generator modules.
Do not implement matching logic in the generator.
Do not tune generated data toward a target match rate.
```

- [ ] **Step 2: Write reproducibility test**

```python
def test_same_seed_produces_same_input_hash() -> None:
    first = generate_clean_dataset(seed=1101)
    second = generate_clean_dataset(seed=1101)
    assert first.input_hash == second.input_hash
```

- [ ] **Step 3: Write isolation test**

The test should statically inspect imports under `engine/reconra` and fail if any import path begins with `generator`.

- [ ] **Step 4: Implement the clean generator**

The clean fixture should contain 60–80 records and reconcile exactly by identity/amount/date.

- [ ] **Step 5: Implement messy scenario injectors**

Inject explicit, labeled truth for:
- rounding variance;
- amount mismatch;
- fee variance;
- tax variance;
- settlement cutoff;
- delayed settlement;
- instant settlement variance;
- refund netted later;
- partial refund;
- mangled UTR;
- mangled narration;
- duplicate ledger row;
- duplicate bank credit;
- dispute adjustment;
- general adjustment;
- missing order;
- missing payment;
- missing settlement;
- missing bank credit;
- intentionally unresolvable record.

Scenario injectors may manipulate raw records but must write expected truth separately.

- [ ] **Step 6: Generate the five fixed datasets**

Use fixed seeds committed in the generator config:

```text
clean:      1101
messy-dev:  2202
demo:       3303
heldout:    4404
stress:     5505
```

The exact seed values are not secret.

- [ ] **Step 7: Verify demo scale**

Target about 240–250 reconciliation lines. It must exceed 50 without padding with meaningless duplicates.

- [ ] **Step 8: Commit**

```powershell
pytest tests\unit\test_generator.py tests\integration\test_generator_isolation.py -q
git add generator scripts data tests
git commit -m "feat(data): add reproducible reconciliation datasets"
git push
```

---

# Task 7: Implement deterministic exact matching and settlement arithmetic

**Files:**
- Create: `engine/reconra/matching/exact.py`
- Create: `engine/reconra/matching/settlement_bank.py`
- Create: `engine/reconra/reconciliation/settlement_math.py`
- Create: `engine/reconra/reconciliation/state.py`
- Test: `tests/unit/test_exact_matching.py`
- Test: `tests/unit/test_settlement_math.py`
- Test: `tests/property/test_money_conservation.py`

**Interfaces:**
- Produces:
  - `recompute_settlement_net(entries: Sequence[SettlementEntry]) -> int`
  - `find_exact_payment_match(...) -> MatchCandidate | None`
  - `find_exact_bank_match(...) -> MatchCandidate | None`
  - `ReconciliationState`

- [ ] **Step 1: Write settlement arithmetic tests**

Use explicit paise examples and assert:

```text
gross credits
- debits/refunds
- fees
- taxes
± adjustments
= expected net settlement
```

Do not let the test call the generator's truth helper.

- [ ] **Step 2: Write exact ID matching tests**

Exact IDs + compatible amounts must match; same ID + impossible financial relationship must become an exception candidate, not a forced match.

- [ ] **Step 3: Run failing tests**

```powershell
pytest tests\unit\test_exact_matching.py tests\unit\test_settlement_math.py -v
```

- [ ] **Step 4: Implement minimal exact matching and arithmetic**

No fuzzy text logic in this task.

- [ ] **Step 5: Add money-conservation property test**

For any valid generated settlement composition:

```python
assert total_bank_credit_paise == explained_paise + residual_paise
```

at every committed state.

- [ ] **Step 6: Verify clean fixture**

The clean dataset must reconcile with:
- 100% correct matches;
- 0 false matches;
- 0 unexplained paise.

If not, stop and debug before Task 8.

- [ ] **Step 7: Commit**

```powershell
git add engine tests
git commit -m "feat(engine): add deterministic settlement matching"
git push
```

---

# Task 8: Add tolerance matching and fuzzy candidate discovery

**Files:**
- Create: `engine/reconra/matching/tolerance.py`
- Create: `engine/reconra/matching/fuzzy.py`
- Create: `engine/reconra/matching/candidates.py`
- Test: `tests/unit/test_tolerance.py`
- Test: `tests/unit/test_fuzzy_candidates.py`

**Interfaces:**
- Produces:
  - `within_rounding_tolerance(expected_paise: int, actual_paise: int, policy: ReconciliationPolicy) -> bool`
  - `score_utr_similarity(a: str, b: str) -> float`
  - `score_narration_similarity(a: str, b: str) -> float`
  - `build_bank_candidates(settlement, bank_rows, policy) -> list[MatchCandidate]`
- `MatchCandidate` retains component evidence; it is not a mysterious aggregate score.

- [ ] **Step 1: Write tolerance boundary tests**

Test exactly:
- inside tolerance;
- exactly at tolerance;
- one paise beyond tolerance.

- [ ] **Step 2: Write fuzzy evidence tests**

A clipped UTR plus exact amount plus in-window date should create a candidate. Similar text with a large amount mismatch must not auto-match.

- [ ] **Step 3: Implement RapidFuzz candidate scores**

Return evidence fields such as:
- UTR similarity;
- narration similarity;
- amount delta;
- date delta;
- exact amount flag.

- [ ] **Step 4: Ensure fuzzy matching never mutates state**

Candidate discovery returns candidates only.

- [ ] **Step 5: Verify development messy dataset**

Run rules only and capture:
- deterministic coverage;
- false-match count;
- residual count;
- residual rupee value.

Do not claim these are final benchmark values.

- [ ] **Step 6: Commit**

```powershell
git add engine tests
git commit -m "feat(engine): add conservative fuzzy candidate matching"
git push
```

---

# Task 9: Build the deterministic reconciliation pipeline

**Files:**
- Create: `engine/reconra/reconciliation/pipeline.py`
- Modify: `engine/reconra/reconciliation/state.py`
- Create: `engine/reconra/audit/events.py`
- Test: `tests/integration/test_reconciliation_pipeline.py`
- Test: `tests/property/test_order_invariance.py`

**Interfaces:**
- Produces:
  - `reconcile_deterministic(dataset: CanonicalDataset, policy: ReconciliationPolicy) -> ReconciliationResult`
  - residual exceptions with evidence-ready context
  - audit events for deterministic decisions

- [ ] **Step 1: Write end-to-end deterministic pipeline test**

Given the clean fixture, assert:
- result completed;
- all records reconciled;
- residual is zero;
- audit events exist;
- no agent dependency is imported/called.

- [ ] **Step 2: Write row-order invariance property test**

Shuffle orders, settlement entries, and bank rows; result matches and totals must be invariant.

- [ ] **Step 3: Implement pipeline stages**

Required stage order:

```text
validate canonical inputs
→ exact identity matching
→ settlement decomposition
→ settlement-to-bank matching
→ tolerance rules
→ fuzzy candidate discovery
→ unresolved residual creation
→ deterministic metrics seed
```

- [ ] **Step 4: Add stage progress events**

Produce structured progress labels the API/frontend can later stream or poll:

```text
VALIDATED
NORMALIZED
GROUPED_SETTLEMENTS
EXACT_MATCHING_COMPLETE
DETERMINISTIC_COMPLETE
```

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests\integration\test_reconciliation_pipeline.py tests\property\test_order_invariance.py -q
git add engine tests
git commit -m "feat(engine): add deterministic reconciliation pipeline"
git push
```

---

# Task 10: Implement metrics, evaluation, and controller artifacts

**Files:**
- Create: `engine/reconra/metrics/evaluator.py`
- Create: `engine/reconra/metrics/throughput.py`
- Create: `engine/reconra/artifacts/ledger.py`
- Create: `engine/reconra/artifacts/exceptions.py`
- Create: `engine/reconra/artifacts/audit.py`
- Create: `engine/reconra/artifacts/summary.py`
- Create: `scripts/run_benchmark.py`
- Create: `scripts/export_results.py`
- Test: `tests/evaluation/test_scoring.py`
- Test: `tests/integration/test_artifacts.py`

**Interfaces:**
- Produces metrics:
  - total records;
  - resolved records;
  - deterministic resolved;
  - agent assisted;
  - review required;
  - escalated;
  - coverage;
  - auto-resolution precision;
  - false-match rate;
  - resolvable-record recall;
  - correct-abstention rate;
  - per-break-class accuracy;
  - records/second;
  - AI call count;
  - estimated inference cost;
  - total bank credit paise;
  - explained paise;
  - residual paise.
- Produces artifacts:
  - `reconciled_ledger.csv`
  - `exception_worklist.csv`
  - `audit_log.json`
  - `reconciliation_summary.json`

- [ ] **Step 1: Write evaluator tests with hand-authored truth**

Do not use generator helper logic to score. Create a tiny explicit expected mapping and assert false-match behavior.

- [ ] **Step 2: Implement evaluator**

A wrong match counts as a false match even if it reduces residual.

- [ ] **Step 3: Implement artifact exporters**

CSV output must preserve IDs and paise-derived display amounts without converting internal state to float.

- [ ] **Step 4: Run deterministic-only held-out benchmark exactly once after thresholds freeze**

Command:

```powershell
python scripts\run_benchmark.py --dataset heldout --mode deterministic
```

Persist the measured output under `docs/evaluation/` or a generated benchmark file referenced by docs. Do not edit the held-out dataset based on the score.

- [ ] **Step 5: Commit**

```powershell
git add engine scripts tests docs
git commit -m "feat(engine): add reconciliation metrics and artifacts"
git push
```

---

# Task 11: Implement residual evidence packets and strict agent schemas

**Files:**
- Create: `engine/reconra/evidence/builder.py`
- Create: `agent/schemas/proposal.py`
- Create: `agent/providers/base.py`
- Create: `agent/providers/disabled.py`
- Create: `agent/reasoner.py`
- Create: `agent/prompts/residual_reasoning.md`
- Test: `tests/unit/test_evidence_builder.py`
- Test: `tests/unit/test_agent_schema.py`

**Interfaces:**
- Produces:
  - `EvidencePacket`
  - `AgentProposal`
  - `ResidualReasoner` protocol
  - `DisabledReasoner`
- Required protocol:

```python
class ResidualReasoner(Protocol):
    async def reason(self, cases: list[EvidencePacket]) -> list[AgentProposal]:
        ...
```

- [ ] **Step 1: Write evidence privacy test**

Assert the serialized evidence packet has no fields for:
- customer email;
- phone;
- account number;
- full raw PDF/text document.

- [ ] **Step 2: Write schema rejection tests**

Pydantic must reject:
- unknown break classes;
- confidence outside 0–1;
- malformed recommended actions.

Candidate existence is verified later by the deterministic verifier, not trusted from the schema layer.

- [ ] **Step 3: Implement Evidence Builder**

Only include facts already computed by deterministic code:
- target amount/date/reference fragments;
- candidate IDs;
- amount/date deltas;
- normalized similarity evidence;
- related refund/adjustment counts;
- deterministic unresolved reason.

- [ ] **Step 4: Implement disabled provider**

`DisabledReasoner` returns a typed unavailable state that the caller can safely convert to escalation.

- [ ] **Step 5: Commit**

```powershell
git add engine agent tests
git commit -m "feat(agent): add residual evidence and schemas"
git push
```

---

# Task 12: Implement Gemini structured-output reasoning with safe failure

**Files:**
- Create: `agent/providers/gemini.py`
- Modify: `apps/api/requirements.txt`
- Test: `tests/unit/test_gemini_provider.py`
- Test: `tests/integration/test_agent_fallback.py`

**Interfaces:**
- Produces `GeminiReasoner`.
- Consumes `GEMINI_API_KEY` only from backend environment.
- Uses structured JSON output matching `AgentProposal`.
- Batches compatible residual cases.
- Has a hard timeout and at most one retry for transient failure.

- [ ] **Step 1: Add provider tests with mocked response**

Test:
- valid structured response;
- malformed response;
- timeout;
- rate limit;
- second failure after one retry.

- [ ] **Step 2: Implement provider without exposing secrets**

Never log request headers containing keys.

- [ ] **Step 3: Enforce timeout/retry policy**

On final failure, return a typed unavailable state; do not loop.

- [ ] **Step 4: Run one manual free-tier smoke call only after the human adds the key to `apps/api/.env`**

The human manually creates:

```text
GEMINI_API_KEY=<real local value>
```

Codex never receives the plaintext key in chat.

- [ ] **Step 5: Verify deterministic-only mode still works with no key**

Unset/omit key and run reconciliation. It must complete with residuals safely escalated.

- [ ] **Step 6: Commit**

```powershell
git add agent apps/api tests
git commit -m "feat(agent): add structured residual reasoning"
git push
```

---

# Task 13: Implement deterministic verification, risk gate, idempotency, and audit

**Files:**
- Create: `engine/reconra/verification/verifier.py`
- Create: `engine/reconra/verification/risk.py`
- Create: `engine/reconra/verification/idempotency.py`
- Modify: `engine/reconra/audit/events.py`
- Modify: `engine/reconra/reconciliation/pipeline.py`
- Test: `tests/unit/test_verifier.py`
- Test: `tests/unit/test_risk_gate.py`
- Test: `tests/property/test_idempotency.py`
- Test: `tests/property/test_post_resolution_conservation.py`

**Interfaces:**
- Produces:
  - `verify_proposal(proposal, state, policy) -> VerificationResult`
  - `decide_resolution_action(proposal, verification, policy) -> ResolutionDisposition`
  - dispositions: `AUTO_RESOLVED`, `REVIEW_REQUIRED`, `ESCALATED`, `REJECTED`

- [ ] **Step 1: Write fabricated-evidence test**

If the agent claims evidence that is absent from the case packet, verification fails.

- [ ] **Step 2: Write duplicate-candidate test**

A bank transaction already committed to another settlement cannot be reused.

- [ ] **Step 3: Write high-impact risk test**

Even with high agent confidence, a proposal above `high_impact_review_threshold_paise` must not auto-apply.

- [ ] **Step 4: Write idempotency property test**

Applying the same resolution twice produces the same final state as applying it once.

- [ ] **Step 5: Implement verifier and risk gate**

Confidence is never sufficient by itself.

- [ ] **Step 6: Emit audit events for every step**

Record:
- rule engine;
- candidate discovery;
- agent proposal;
- verifier decision;
- system auto-apply;
- human approval/rejection.

- [ ] **Step 7: Run rules-only vs rules+agent held-out ablation**

```powershell
python scripts\run_benchmark.py --dataset heldout --mode deterministic
python scripts\run_benchmark.py --dataset heldout --mode agent-assisted
```

Record the actual comparison. Do not change the dataset after this.

- [ ] **Step 8: Commit**

```powershell
git add engine agent tests docs
git commit -m "feat(engine): verify and gate agent resolutions"
git push
```

---

# Task 14: Expose the reconciliation API and short-lived run state

**Files:**
- Create: `apps/api/app/errors.py`
- Create: `apps/api/app/services/run_store.py`
- Create: `apps/api/app/services/reconciliation_service.py`
- Create: `apps/api/app/routes/reconcile.py`
- Create: `apps/api/app/routes/runs.py`
- Create: `apps/api/app/schemas/api.py`
- Modify: `apps/api/app/main.py`
- Test: `tests/integration/test_reconcile_api.py`
- Test: `tests/integration/test_resolution_api.py`

**Interfaces:**
- Endpoints:
  - `POST /api/reconcile/demo`
  - `POST /api/reconcile`
  - `GET /api/runs/{run_id}`
  - `POST /api/runs/{run_id}/exceptions/{exception_id}/approve`
  - `POST /api/runs/{run_id}/exceptions/{exception_id}/reject`
  - `GET /api/runs/{run_id}/artifacts/{artifact_name}`
- `RunStore`:
  - TTL: 30 minutes;
  - max entries: 20;
  - no disk/database persistence.

- [ ] **Step 1: Write demo API test**

Assert the demo endpoint returns:
- run ID;
- status;
- progress/stages;
- tie-out summary;
- metrics;
- exceptions;
- artifact names.

- [ ] **Step 2: Implement typed API errors**

Shape:

```json
{
  "code": "AGENT_UNAVAILABLE",
  "message": "Agent reasoning is unavailable; unresolved cases were safely escalated.",
  "recoverable": true
}
```

- [ ] **Step 3: Implement run store**

Do not write uploaded or run data to Render's ephemeral filesystem for durability.

- [ ] **Step 4: Implement approve/reject flow**

Approval must call the deterministic verifier again against the current run state before applying.

- [ ] **Step 5: Verify stale/double approval**

Second approval of the same exception must not apply twice.

- [ ] **Step 6: Commit**

```powershell
git add apps/api tests
git commit -m "feat(api): expose reconciliation workflow"
git push
```

---

# Task 15: Implement Razorpay Test Mode sync

**Files:**
- Create: `apps/api/app/services/razorpay_service.py`
- Create: `apps/api/app/routes/razorpay.py`
- Create: `apps/api/app/schemas/razorpay.py`
- Modify: `apps/api/app/config.py`
- Test: `tests/unit/test_razorpay_service.py`
- Test: `tests/integration/test_razorpay_api.py`

**Interfaces:**
- `RazorpayService` retrieves test-mode orders, payments, refunds, and available reconciliation/settlement records.
- Endpoint: `POST /api/razorpay/sync`
- No runtime mutation method is implemented.

- [ ] **Step 1: Use Razorpay Official MCP in read-only mode to inspect Test Mode entity shapes**

Codex prompt:

```text
Execute Task 15 only.

Use the Razorpay Official MCP for read-only inspection of Test Mode entity shapes if needed. Do not invoke any create, capture, refund, payout, update, revoke, or other mutation tool. Read AGENTS.md first.

The deployed app must use Razorpay REST/Test Mode APIs, not MCP.
Never reveal credentials in logs or output.
```

- [ ] **Step 2: Write mocked retrieval tests**

Test pagination, empty account data, authentication failure, and partial endpoint failure.

- [ ] **Step 3: Implement test-environment fail-closed check**

If config is not `RAZORPAY_ENV=test`, the service refuses to initialize the sync path.

- [ ] **Step 4: Human adds test credentials locally**

Manually add to `apps/api/.env`:

```text
RAZORPAY_ENV=test
RAZORPAY_KEY_ID=<local value>
RAZORPAY_KEY_SECRET=<local value>
```

Do not paste the secret into Codex chat.

- [ ] **Step 5: Perform local Test Mode sync smoke test**

Confirm only test/sandbox data is returned.

- [ ] **Step 6: Commit**

```powershell
git add apps/api tests
git commit -m "feat(razorpay): add test-mode reconciliation sync"
git push
```

---

# Task 16: Implement file inspection and controlled smart mapping

**Files:**
- Create: `engine/reconra/ingestion/csv.py`
- Create: `engine/reconra/ingestion/xlsx.py`
- Create: `engine/reconra/ingestion/pdf.py`
- Create: `engine/reconra/ingestion/mapping.py`
- Create: `engine/reconra/ingestion/validation.py`
- Create: `apps/api/app/services/import_store.py`
- Create: `apps/api/app/services/import_service.py`
- Create: `apps/api/app/routes/imports.py`
- Create: `apps/api/app/schemas/imports.py`
- Test: `tests/unit/test_csv_ingestion.py`
- Test: `tests/unit/test_xlsx_ingestion.py`
- Test: `tests/unit/test_pdf_ingestion.py`
- Test: `tests/unit/test_column_mapping.py`
- Test: `tests/integration/test_import_api.py`

**Interfaces:**
- `inspect_import(files) -> ImportInspection`
- `suggest_column_mappings(columns, target_schema) -> list[ColumnSuggestion]`
- in-memory `import_id` with TTL
- endpoints:
  - `POST /api/import/inspect`
  - `POST /api/import/{import_id}/validate`
  - `POST /api/import/{import_id}/reconcile`

- [ ] **Step 1: Add upload limit tests**

Reject:
- unsupported extensions;
- >10 MB single file;
- >25 MB combined;
- >10,000 parsed rows.

- [ ] **Step 2: Add CSV and XLSX parser tests**

Use fixture files that contain known dates, strings, and decimal amounts. Convert monetary values using the paise parser, never float arithmetic.

- [ ] **Step 3: Add controlled PDF tests**

Support text/table PDF fixture with recognizable rows. Reject scanned/image-only fixture with a clear error:

```text
PDF_TEXT_TABLE_REQUIRED
```

- [ ] **Step 4: Implement deterministic header mapping**

Use:
1. normalized exact aliases;
2. token matching;
3. RapidFuzz fallback;
4. confidence + reason.

Examples:

```text
Txn Date      -> transaction_date
Narration     -> description
Deposit Amt   -> credit_paise
Ref No        -> utr
```

- [ ] **Step 5: Preserve human confirmation**

No mapping is considered final until the frontend sends confirmed mappings.

- [ ] **Step 6: Optional low-confidence AI mapping**

Only after deterministic mapping works. If used, send sanitized column names and target-field descriptions only, never file contents. AI suggestions remain suggestions requiring human confirmation.

- [ ] **Step 7: Verify no macro execution**

Only `.xlsx` is supported. `.xlsm` is rejected.

- [ ] **Step 8: Commit**

```powershell
git add engine apps/api tests
git commit -m "feat(import): add smart CSV Excel and PDF ingestion"
git push
```

---

# Task 17: Build frontend design tokens, shell, and Rupee Flow entry

**Files:**
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/app/layout.tsx`
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/components/layout/app-shell.tsx`
- Create: `apps/web/components/layout/sidebar.tsx`
- Create: `apps/web/components/rupee-flow/rupee-flow.tsx`
- Create: `apps/web/components/rupee-flow/rupee-fragment.tsx`
- Create: `apps/web/lib/format/currency.ts`
- Test: `tests/e2e/entry.spec.ts`

**Interfaces:**
- Produces Reconra's design token system.
- `formatINRFromPaise(value: number) -> string`
- Landing CTAs:
  - Run Demo Reconciliation
  - Import data
  - Sync Razorpay Test Mode

- [ ] **Step 1: Give Codex the design orchestration prompt**

```text
Execute Task 17 only.

Read the approved design spec, especially sections 22–24.
Use frontend-design-premium first to establish composition, but the approved Reconra design spec is authoritative.
Use 21st.dev MCP only to discover a primitive if it genuinely improves the implementation; do not import a generic dashboard.
Do not use apple-design, emil-design-eng, or improve-animations yet; those are later review passes.

Visual rules:
- warm light canvas;
- evidence-driven finance workstation;
- deep restrained indigo accent;
- borders over shadows;
- tight radii;
- tabular numerals;
- Indian currency formatting;
- no purple gradients;
- no glassmorphism;
- no giant KPI-card grid;
- no AI chatbot;
- no stock illustrations;
- no decorative charts.

Implement original banknote-inspired Rupee Flow artwork, not scans/copies of real Indian notes. It must respect prefers-reduced-motion and must stop being visually dominant once the workspace begins.

Do not build later screens.
```

- [ ] **Step 2: Implement design tokens before page-specific CSS**

Define CSS variables for canvas, surfaces, ink, muted ink, borders, accent, verified, review, exception, radius, and spacing.

- [ ] **Step 3: Implement Indian currency formatting**

Verify:

```ts
formatINRFromPaise(528419000) === "₹52,84,190.00"
```

- [ ] **Step 4: Build Rupee Flow with CSS/SVG transforms**

Use abstract:
- note-like cropped rectangles;
- guilloché-inspired line patterns;
- denomination numerals;
- serial/reference strings;
- rupee symbols.

No real note scan or faithful security-feature reproduction.

- [ ] **Step 5: Add reduced-motion static state**

With `prefers-reduced-motion: reduce`, the composition remains attractive but static.

- [ ] **Step 6: Verify at desktop and 320px width**

No page-level horizontal scrolling.

- [ ] **Step 7: Commit**

```powershell
git add apps/web
git commit -m "feat(web): establish reconra visual system"
git push
```

---

# Task 18: Build the workspace and live reconciliation experience

**Files:**
- Create: `apps/web/app/workspace/page.tsx`
- Create: `apps/web/features/reconciliation/api.ts`
- Create: `apps/web/features/reconciliation/types.ts`
- Create: `apps/web/features/reconciliation/run-controller.tsx`
- Create: `apps/web/features/reconciliation/progress.tsx`
- Create: `apps/web/lib/api/client.ts`
- Create: `apps/web/lib/api/errors.ts`
- Test: `tests/e2e/demo-run.spec.ts`

**Interfaces:**
- Frontend calls `POST /api/reconcile/demo`.
- Displays real stage progress and final result.
- Initial page load calls `/api/health`.

- [ ] **Step 1: Write Playwright demo-run test before implementation**

Flow:
1. open app;
2. click `Run Demo Reconciliation`;
3. see processing state;
4. reach `Reconciliation complete`;
5. see total/explained/residual values from the API.

Use API mocking only for the isolated browser path; a production-connected smoke test is added after deployment.

- [ ] **Step 2: Implement health warm-up**

On app entry:
- call backend health;
- show `Preparing reconciliation engine…` during cold start;
- never show a raw fetch error.

- [ ] **Step 3: Implement structured progress list**

Display:
- validated;
- normalized;
- grouped settlements;
- deterministic matching;
- residual investigation;
- final verification;
- tie-out.

- [ ] **Step 4: Never fake time-delayed stages**

If the backend returns stage information only at completion initially, display truthful completed-stage information rather than adding fake timers. Add polling/streaming only if implemented honestly.

- [ ] **Step 5: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add live reconciliation workspace"
git push
```

---

# Task 19: Build Run Overview, Tie-Out Rail, metrics, and ledger explorer

**Files:**
- Create: `apps/web/components/tie-out/tie-out-rail.tsx`
- Create: `apps/web/features/reconciliation/run-overview.tsx`
- Create: `apps/web/features/reconciliation/metrics-strip.tsx`
- Create: `apps/web/app/ledger/page.tsx`
- Create: `apps/web/features/ledger/ledger-table.tsx`
- Create: `apps/web/features/ledger/ledger-detail-drawer.tsx`
- Create: `apps/web/features/ledger/filters.tsx`
- Test: `tests/e2e/ledger.spec.ts`

**Interfaces:**
- Tie-Out always obeys:
  - total bank credit = explained + residual.
- Ledger supports status/source filtering and evidence inspection.

- [ ] **Step 1: Add frontend invariant check**

If API values violate the tie-out equation, render an explicit integrity error rather than displaying inconsistent finance numbers.

- [ ] **Step 2: Build Tie-Out Rail as the dominant result visual**

Order:
- total bank credit;
- rules verified;
- agent verified;
- human-approved;
- unexplained residual.

- [ ] **Step 3: Build metrics strip without generic dashboard cards**

Use compact labeled measures. Display actual benchmark/run metrics only.

- [ ] **Step 4: Build TanStack ledger table**

Requirements:
- sticky header;
- right-aligned tabular amounts;
- compact density;
- horizontal local scroll when necessary;
- filters for settlement, status, method, break class, date, resolution source.

- [ ] **Step 5: Build row evidence drawer**

Show exact identifiers, money reconstruction, bank link evidence, resolution source, and verifier status.

- [ ] **Step 6: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add tie-out and ledger explorer"
git push
```

---

# Task 20: Build exception workbench, human review, and audit trail

**Files:**
- Create: `apps/web/app/exceptions/page.tsx`
- Create: `apps/web/features/exceptions/exception-list.tsx`
- Create: `apps/web/features/exceptions/exception-detail.tsx`
- Create: `apps/web/features/exceptions/resolution-actions.tsx`
- Create: `apps/web/app/audit/page.tsx`
- Create: `apps/web/features/audit/audit-timeline.tsx`
- Test: `tests/e2e/exception-resolution.spec.ts`
- Test: `tests/e2e/audit.spec.ts`

**Interfaces:**
- Calls approve/reject API endpoints.
- Updates run result and tie-out after verified approval.
- Audit trail shows actors `RULE_ENGINE`, `AGENT`, `VERIFIER`, `USER`, `SYSTEM`.

- [ ] **Step 1: Write approval e2e test**

Capture residual before approval, approve a review-required item, assert:
- request succeeds;
- exception status changes;
- residual changes by the exact approved financial impact;
- audit event appears.

- [ ] **Step 2: Build evidence-first detail**

Do not headline “AI”. Show:
- proposed resolution;
- evidence;
- agent confidence;
- deterministic verification;
- financial impact.

- [ ] **Step 3: Build approve/reject controls**

Disable actions while request is in flight. Handle stale-state rejection explicitly.

- [ ] **Step 4: Build audit timeline**

Readable finance-investigation timeline, not server logs.

- [ ] **Step 5: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add exception resolution and audit"
git push
```

---

# Task 21: Build exports and browser-side run history

**Files:**
- Create: `apps/web/app/runs/page.tsx`
- Create: `apps/web/features/runs/run-history.tsx`
- Create: `apps/web/lib/storage/runs.ts`
- Create: `apps/web/features/reconciliation/export-menu.tsx`
- Test: `tests/e2e/history-and-exports.spec.ts`

**Interfaces:**
- IndexedDB retains at most 10 recent run snapshots.
- Export types:
  - reconciled ledger CSV;
  - exception worklist CSV;
  - audit JSON;
  - summary JSON.

- [ ] **Step 1: Implement IndexedDB repository**

Functions:

```ts
saveRunSnapshot(snapshot: RunSnapshot): Promise<void>
listRunSnapshots(): Promise<RunSnapshotSummary[]>
getRunSnapshot(runId: string): Promise<RunSnapshot | undefined>
deleteRunSnapshot(runId: string): Promise<void>
```

Enforce max 10 entries by removing oldest.

- [ ] **Step 2: Build run history table**

Do not show benchmark accuracy for Razorpay Test Mode runs where ground truth is unavailable.

- [ ] **Step 3: Verify downloads**

Playwright asserts downloaded filenames and non-empty content.

- [ ] **Step 4: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add run history and exports"
git push
```

---

# Task 22: Build Import & Mapping UX

**Files:**
- Create: `apps/web/app/import/page.tsx`
- Create: `apps/web/features/imports/upload-zone.tsx`
- Create: `apps/web/features/imports/file-classification.tsx`
- Create: `apps/web/features/imports/mapping-table.tsx`
- Create: `apps/web/features/imports/data-preview.tsx`
- Create: `apps/web/features/imports/validation-summary.tsx`
- Create: `apps/web/features/imports/api.ts`
- Test: `tests/e2e/import-csv.spec.ts`
- Test: `tests/e2e/import-xlsx.spec.ts`
- Test: `tests/e2e/import-pdf.spec.ts`

**Interfaces:**
- Upload → inspect → classify → mapping suggestions → human confirmation → validation → reconcile.

- [ ] **Step 1: Write CSV workflow e2e**

Use a fixture with noncanonical names:
- `Txn Date`;
- `Narration`;
- `Deposit Amt`;
- `Ref No`.

Confirm suggested canonical fields, then start reconciliation.

- [ ] **Step 2: Build upload zone with explicit supported formats**

Do not claim scanned-PDF OCR.

- [ ] **Step 3: Build mapping table**

Every suggestion shows:
- source column;
- canonical target;
- confidence;
- reason;
- editable target select.

- [ ] **Step 4: Build preview and warnings**

Show missing UTR rows as warnings, not fatal if policy permits.

- [ ] **Step 5: Verify XLSX and PDF paths**

The controlled PDF path must visibly label extraction confidence.

- [ ] **Step 6: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add smart data import workflow"
git push
```

---

# Task 23: Build Razorpay Test Mode and Methodology screens

**Files:**
- Create: `apps/web/app/razorpay/page.tsx`
- Create: `apps/web/features/razorpay/sync-panel.tsx`
- Create: `apps/web/features/razorpay/api.ts`
- Create: `apps/web/app/methodology/page.tsx`
- Test: `tests/e2e/razorpay-sync.spec.ts`

**Interfaces:**
- Razorpay page always displays `TEST MODE`.
- Methodology explains rules → residual agent → verifier → risk gate → action.

- [ ] **Step 1: Build Test Mode status panel**

Never display key ID/secret to the user.

- [ ] **Step 2: Handle unavailable/empty sandbox gracefully**

Show counts and clear empty state.

- [ ] **Step 3: Build methodology page**

Include:
- paise-only arithmetic;
- no LLM math;
- agent residual-only role;
- verifier;
- abstention;
- generator/ground-truth isolation;
- auditability.

- [ ] **Step 4: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "feat(web): add razorpay sync and methodology"
git push
```

---

# Task 24: Controlled design review and motion pass

**Files:**
- Modify only existing frontend files that fail the review.
- Test: existing Playwright suites.

**Interfaces:**
- No new product capability.
- Produces final visual polish while preserving the approved design.

- [ ] **Step 1: Run `apple-design` as a review, not a redesign**

Codex prompt:

```text
Review the implemented Reconra frontend using apple-design.

The approved Reconra spec is authoritative. Do not redesign the product, change the brand, add dark mode, or convert it into a marketing/SaaS dashboard.

Focus only on:
- hierarchy;
- control clarity;
- spacing;
- alignment;
- interaction ergonomics;
- accessibility;
- consistency;
- keyboard/focus quality.

Return findings first. Make only approved/high-confidence fixes that preserve the Audit Instrument + Rupee Flow direction.
```

- [ ] **Step 2: Run `emil-design-eng` as design-engineering review**

Focus on implementation quality, responsive behavior, CSS structure, and component discipline.

- [ ] **Step 3: Use `12ui-design` only on problematic interactions**

Allowed targets:
- mapping table;
- exception drawer;
- filtering controls;
- audit timeline.

Do not globally restyle the app.

- [ ] **Step 4: Use `improve-animations` last**

Allowed motion:
- Rupee Flow parallax;
- reconciliation stage transitions;
- tie-out residual change;
- review → resolved row movement;
- drawers/popovers.

Forbidden:
- animated backgrounds inside workspace;
- bouncing buttons;
- confetti;
- particles;
- decorative continuous motion.

- [ ] **Step 5: Run Playwright after every design pass**

No design review may break the demo flow.

- [ ] **Step 6: Commit**

```powershell
git add apps/web tests/e2e
git commit -m "refactor(web): refine reconciliation interactions"
git push
```

---

# Task 25: Strengthen security, errors, accessibility, and performance

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/app/errors.py`
- Modify: frontend error/loading states
- Test: `tests/integration/test_security_boundaries.py`
- Test: `tests/e2e/failure-states.spec.ts`
- Test: `tests/e2e/accessibility.spec.ts`

**Interfaces:**
- CORS restricted by environment.
- Secrets redacted.
- AI outage safe.
- Razorpay outage safe.
- Reduced motion respected.

- [ ] **Step 1: Add security boundary tests**

Assert:
- production wildcard CORS is rejected;
- `RAZORPAY_ENV != test` blocks Razorpay sync;
- API error bodies never include secrets;
- unsupported file types are rejected;
- oversized uploads are rejected.

- [ ] **Step 2: Add failure-state e2e tests**

Simulate:
- backend cold/unavailable;
- agent unavailable;
- Razorpay unavailable;
- malformed import;
- PDF extraction low confidence.

- [ ] **Step 3: Add accessibility smoke checks**

Verify:
- keyboard navigation;
- visible focus;
- buttons use real button elements;
- table actions accessible without hover;
- reduced motion;
- status not conveyed by color alone.

- [ ] **Step 4: Run performance sanity check**

Ensure:
- no huge client-side dependency added for Rupee Flow;
- 250-row demo remains responsive;
- 10,000-row backend stress benchmark does not invoke AI once per row.

- [ ] **Step 5: Commit**

```powershell
git add .
git commit -m "test: harden reconra failure and safety boundaries"
git push
```

---

# Task 26: Deploy FastAPI to Render Free

**Files:**
- Create: `render.yaml` if useful for reproducible config.
- Modify: `apps/api/app/config.py` if deployment settings require it.
- Create: `docs/methodology/deployment.md`

**Interfaces:**
- Public backend HTTPS URL.
- `/api/health` responds.
- Secrets stored only in Render environment variables.

- [ ] **Step 1: Run predeployment backend verification**

```powershell
ruff check .
mypy engine apps\api
pytest -q
```

Expected: green.

- [ ] **Step 2: Create Render Web Service manually**

Connect the GitHub repo.

Use repository root as source.

Recommended commands:

```text
Build:
pip install -r apps/api/requirements.txt && pip install -e .

Start:
uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir apps/api
```

Use the Free instance.

- [ ] **Step 3: Add backend environment variables manually**

At minimum:

```text
ENVIRONMENT=production
RAZORPAY_ENV=test
RAZORPAY_KEY_ID=<entered in Render UI>
RAZORPAY_KEY_SECRET=<entered in Render UI>
GEMINI_API_KEY=<entered in Render UI>
ALLOWED_ORIGINS=<temporary Vercel origin after Task 27, then tighten>
```

Do not commit values.

- [ ] **Step 4: Verify cold and warm health**

Open `/api/health` after the service has slept and measure behavior. Confirm the frontend UX can tolerate the wake-up.

- [ ] **Step 5: Record backend URL locally**

Do not hardcode it throughout source; use frontend env configuration.

---

# Task 27: Deploy Next.js to Vercel and connect production

**Files:**
- Modify: frontend environment/config handling.
- Test: production Playwright smoke specs.

**Interfaces:**
- Public Reconra URL with no login.
- `NEXT_PUBLIC_API_BASE_URL` points to Render.
- Render CORS allows the final Vercel origin.

- [ ] **Step 1: Run production web build locally**

```powershell
pnpm --dir apps/web lint
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web build
```

- [ ] **Step 2: Create Vercel project manually**

Import GitHub repo and set Root Directory to:

```text
apps/web
```

- [ ] **Step 3: Add frontend env var**

```text
NEXT_PUBLIC_API_BASE_URL=<Render HTTPS base URL>
```

- [ ] **Step 4: Tighten Render CORS**

Set allowed production origin to the actual Vercel domain.

- [ ] **Step 5: Verify the live one-click demo**

Open Vercel URL in a private/incognito window and run the demo without being logged into development tooling.

- [ ] **Step 6: Commit any deployment-only config changes**

```powershell
git add .
git commit -m "chore: configure production deployment"
git push
```

---

# Task 28: Implement honest saved-benchmark fallback

**Files:**
- Create: `apps/web/public/demo/verified-benchmark.json` or equivalent static asset generated from the final evaluation.
- Modify: entry/workspace unavailable state.
- Create: `scripts/publish_verified_snapshot.py`
- Test: `tests/e2e/saved-benchmark-fallback.spec.ts`

**Interfaces:**
- Fallback is labeled `Verified saved benchmark`.
- Never presented as a live reconciliation run.

- [ ] **Step 1: Generate snapshot from a real successful benchmark run**

Script must copy only sanitized result/output values, not ground truth.

- [ ] **Step 2: Build fallback UI**

When backend health fails after the configured wait:
- offer retry;
- offer `View verified saved benchmark`;
- clearly label it saved/non-live.

- [ ] **Step 3: Verify fallback still lets judges inspect**

Allow:
- tie-out;
- metrics;
- ledger;
- exception examples;
- audit evidence.

Disable actions that require live backend and explain why.

- [ ] **Step 4: Commit**

```powershell
git add apps/web scripts tests/e2e
git commit -m "feat(web): add verified benchmark fallback"
git push
```

---

# Task 29: Complete GitHub Actions and release verification

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/e2e.yml` only if reliable and useful.
- Create: `docs/evaluation/release-checklist.md`

**Interfaces:**
- Pull/push quality gates.
- Final release command checklist.

- [ ] **Step 1: CI must run Python quality**

Commands equivalent to:

```text
ruff check .
mypy engine apps/api
pytest -q
```

- [ ] **Step 2: CI must run frontend quality**

Commands equivalent to:

```text
pnpm --dir apps/web lint
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web build
```

- [ ] **Step 3: Production Playwright remains a manual/final release gate if free CI reliability is poor**

Do not make submission depend on an unstable free browser CI service.

- [ ] **Step 4: Run `superpowers:verification-before-completion`**

No “done” claim until command outputs are inspected.

- [ ] **Step 5: Commit**

```powershell
git add .github docs
git commit -m "ci: enforce reconra release quality"
git push
```

---

# Task 30: Write the public README and technical documentation

**Files:**
- Modify: `README.md`
- Create: `docs/architecture/system.md`
- Create: `docs/methodology/reconciliation.md`
- Create: `docs/evaluation/benchmark.md`
- Create: `docs/security.md`

**Interfaces:**
- Public repo explains how to understand, run, verify, and demo Reconra without marketing fluff.

- [ ] **Step 1: README structure**

Use this order:

```text
Reconra
one-sentence value proposition
Buildathon / Track 04 context
live demo link
demo screenshot
the problem
what Reconra does
why deterministic-first + residual AI
architecture
key safety invariants
measured benchmark
data sources: synthetic vs Razorpay Test Mode
local setup
environment variables
test commands
deployment
known limitations
roadmap
license
```

- [ ] **Step 2: Architecture document**

Include a Mermaid diagram showing:

```text
Next.js
→ FastAPI
→ deterministic engine
→ residual evidence
→ AI reasoner
→ verifier/risk gate
→ result/artifacts
```

- [ ] **Step 3: Methodology document**

Explain finance arithmetic and matching without claiming unsupported accounting guarantees.

- [ ] **Step 4: Benchmark document**

Only insert measured values generated by `run_benchmark.py`.

Include deterministic-only versus agent-assisted ablation.

- [ ] **Step 5: Security doc**

Explicitly state:
- Test Mode only;
- no production Razorpay mutations;
- raw bank statements not sent to free AI;
- no durable server-side storage;
- synthetic benchmark data.

- [ ] **Step 6: Commit**

```powershell
git add README.md docs
git commit -m "docs: document reconra architecture and evaluation"
git push
```

---

# Task 31: Capture submission screenshots and visual evidence

**Files:**
- Create: `docs/assets/` PNG screenshots.
- Modify: README references to selected screenshots.

**Interfaces:**
- Screenshots are generated from the deployed application with no secrets/personal data.

- [ ] **Step 1: Capture these exact screens**

1. Rupee Flow entry / Reconra hero.
2. Run Overview with Tie-Out Rail.
3. Ledger evidence drawer.
4. Exception workbench with verified proposal.
5. Genuinely unresolved exception.
6. Audit timeline.
7. Smart column mapping.
8. Razorpay Test Mode sync.

- [ ] **Step 2: Check every screenshot manually**

No API keys, account numbers, browser personal bookmarks, or unrelated tabs.

- [ ] **Step 3: Add only high-value screenshots to README**

Do not make README a gallery.

---

# Task 32: Prepare the five-minute winning demo

**Files:**
- Create: `docs/demo/5-minute-script.md`
- Create: `docs/demo/demo-checklist.md`

**Interfaces:**
- 5-minute script fits actual deployed behavior.
- No claim depends on a feature not present.

- [ ] **Step 1: Use this demo narrative**

Target timing:

```text
0:00–0:35  Problem
0:35–0:55  Reconra thesis + Rupee Flow
0:55–1:40  Run live curated batch
1:40–2:20  Tie-Out Rail + measured metrics
2:20–3:05  difficult agent-assisted verified resolution
3:05–3:40  genuinely unresolved exception / abstention
3:40–4:15  audit trail + closed-loop approval
4:15–4:35  exports + Razorpay Test Mode sync
4:35–5:00  architecture + why this wins / closing line
```

- [ ] **Step 2: Core pitch line**

Use:

```text
Reconra does not ask an LLM to do accounting. Deterministic code explains the money; the agent is used only where evidence is ambiguous, and every proposal is independently verified before it can affect the reconciliation.
```

- [ ] **Step 3: Demo closer**

End on the actual measured tie-out:

```text
The bank credited ₹X. Reconra explains ₹Y. The remaining ₹Z is isolated across N exceptions, each with evidence for why the system refused to guess.
```

Replace X/Y/Z/N only with live measured values.

- [ ] **Step 4: Rehearse with a timer**

Three consecutive runs under 5 minutes without skipping the unresolved exception.

---

# Task 33: Pre-demo and submission failure plan

**Files:**
- Modify: `docs/demo/demo-checklist.md`

**Interfaces:**
- A live failure does not destroy the pitch.

- [ ] **Step 1: Five minutes before presentation**

Run:

```text
✓ Vercel URL opens
✓ Render /api/health is warm
✓ Demo reconciliation succeeds
✓ Gemini provider responds
✓ Razorpay Test Mode sync endpoint responds or has a clear fallback
✓ saved benchmark opens
✓ exports work
```

- [ ] **Step 2: If Gemini fails**

Continue live:
- deterministic reconciliation completes;
- residuals safely escalate;
- explain graceful degradation;
- show verified saved benchmark for full agent-assisted result if needed.

- [ ] **Step 3: If Render is cold**

Let the health warm-up run while explaining the Rupee Flow/problem. Do not refresh repeatedly.

- [ ] **Step 4: If Razorpay sync fails**

Show the clearly labeled Test Mode integration screen/error state, then continue the benchmark. The benchmark does not depend on live Razorpay availability.

- [ ] **Step 5: If live backend is unavailable**

Use `Verified saved benchmark`, explicitly identify it as saved, and continue inspection screens. Do not pretend it is live.

---

# Task 34: Final release and submission

**Files:**
- No feature files unless fixing a blocker.
- Create Git tag.

**Interfaces:**
- Public repo and live URLs are stable.

- [ ] **Step 1: Fresh-clone test**

Clone into a new temporary folder and follow README setup. Fix missing setup steps only.

- [ ] **Step 2: Run full local verification**

```powershell
ruff check .
mypy engine apps\api
pytest -q

pnpm --dir apps/web lint
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web build
```

Run the complete Playwright smoke suite against production.

- [ ] **Step 3: Run final benchmark**

```powershell
python scripts\run_benchmark.py --dataset heldout --mode deterministic
python scripts\run_benchmark.py --dataset heldout --mode agent-assisted
```

Verify docs contain the actual final values.

- [ ] **Step 4: Check Git state**

```powershell
git status
git log --oneline -15
```

Expected: clean working tree and readable incremental history.

- [ ] **Step 5: Tag the Buildathon release**

```powershell
git tag -a buildathon-2026 -m "Reconra Razorpay Buildathon submission"
git push origin buildathon-2026
```

- [ ] **Step 6: Submit before the deadline**

Verify every submitted link in an incognito window after submitting.

---

# Exact Codex Prompt Strategy

Use these prompts rather than one mega-prompt.

## Session start prompt

```text
We are implementing Reconra for Razorpay Buildathon Track 04.

Before any work:
1. Read AGENTS.md.
2. Read docs/superpowers/specs/2026-08-29-reconra-design.md.
3. Read docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md.
4. Use the Superpowers process skills required by the current task.
5. Use the project finance-controller skill for finance-engine, evaluation, Razorpay, agent, and reconciliation tasks.
6. Do not start any task other than the one I explicitly name.
7. Do not change approved architecture or scope without stopping and asking me.
8. Never expose or request plaintext secrets in chat.
9. Razorpay MCP is read-only unless I explicitly authorize a mutation.
10. At the end of the task, run the exact verification commands from the plan, summarize files changed, tests run, remaining risks, and STOP for my checkpoint.

Do not implement anything yet. Confirm you understand the execution rules and tell me which spec/plan files you read.
```

## Task execution prompt template

```text
Execute Task <number>: <task title> from
docs/superpowers/plans/2026-08-29-reconra-implementation-plan.md.

Follow its file boundaries, interfaces, tests, and stop condition exactly.
Use TDD.
If a test or runtime behavior is unexpected, invoke systematic-debugging instead of guessing.
Before claiming completion, invoke verification-before-completion.
Do not begin the next task.
```

## Frontend implementation prompt

```text
Execute the named frontend task only.

The Reconra visual specification is authoritative. Use the design skills only in the order defined by the plan and only for the purpose assigned to each:
frontend-design-premium -> page composition,
21st.dev MCP -> selective primitives,
12ui-design -> specific interaction review,
apple-design -> hierarchy/ergonomics review,
emil-design-eng -> design-engineering refinement,
improve-animations -> final purposeful motion,
Playwright -> browser verification.

Do not allow any skill to turn the product into a generic AI SaaS dashboard.
Do not add glassmorphism, purple gradients, giant KPI cards, chatbot UI, decorative charts, floating background elements in the operational workspace, or unnecessary rounded cards.
```

## Razorpay task prompt

```text
Execute the named Razorpay task only.

Use Razorpay Official MCP for read-only development inspection if needed.
Do not invoke mutation tools.
Runtime code must use Test Mode REST APIs.
Never print, store, commit, or request plaintext Razorpay secrets.
If runtime config is not explicitly test mode, fail closed.
```

## Debug prompt

```text
A verification step failed. Do not patch randomly.

Invoke superpowers:systematic-debugging.
Reproduce the failure, identify the first incorrect assumption, inspect the smallest relevant surface, write/adjust a failing regression test, then implement the minimal fix.
Re-run the task's full verification commands.
Do not begin unrelated refactoring.
```

## Review prompt

```text
Review the just-completed task against:
- AGENTS.md,
- the approved design spec,
- the exact task in the implementation plan.

Use superpowers:requesting-code-review.
Prioritize correctness, finance invariants, data leakage, false-match risk, security, and regressions.
List actionable defects first.
Do not rewrite unrelated code.
```

---

# What the Human Should and Should Not Do

## Human does

- create GitHub repo;
- download/place spec and plan;
- review Codex checkpoints;
- enter secrets locally and in deployment dashboards;
- authorize GitHub/Vercel/Render;
- manually inspect UI;
- decide if a scope change is accepted;
- rehearse pitch;
- submit.

## Human does not

- copy/paste normal source files from Codex chat into VS Code;
- paste API secrets into Codex;
- manually “fix” failing tests without understanding them;
- let Codex run Razorpay mutations;
- allow design tools to redesign the approved visual direction;
- tune the held-out dataset to improve metrics;
- wait until September 4 to deploy.

---

# Buildathon Winning Priorities

When there is a conflict between two improvements, use this order:

1. Financial correctness and zero false matches.
2. Honest abstention and exception quality.
3. Rupee tie-out correctness.
4. Live demo reliability.
5. Auditability and evidence.
6. Real Razorpay Test Mode integration.
7. Agent value proven by ablation.
8. Import usefulness.
9. Frontend clarity and distinctive visual identity.
10. Motion and extra polish.

A visually impressive feature never outranks a finance invariant.

---

# Final Definition of Done

Reconra is complete only when all are true:

```text
PRODUCT
✓ no-login public URL
✓ one-click curated demo
✓ 50+ meaningful records; target ~240–250 demo lines
✓ deterministic reconciliation
✓ residual AI reasoning
✓ deterministic verification
✓ auto/review/escalate risk gate
✓ human approval updates tie-out
✓ honest unresolved exceptions
✓ final rupee tie-out
✓ audit trail
✓ controller exports
✓ Razorpay Test Mode sync
✓ smart CSV import
✓ smart XLSX import
✓ controlled text/table PDF import
✓ IndexedDB run history
✓ saved benchmark fallback

QUALITY
✓ paise-only arithmetic
✓ engine cannot import generator/ground truth
✓ held-out dataset frozen
✓ clean dataset exact
✓ property tests pass
✓ false-match metric measured
✓ rules-vs-agent ablation measured
✓ Python lint/type/tests pass
✓ frontend lint/type/build pass
✓ Playwright critical flows pass
✓ reduced-motion works
✓ failure states work

DEPLOYMENT
✓ Render backend live
✓ Vercel frontend live
✓ CORS restricted
✓ production secrets only in host stores
✓ cold start handled
✓ fallback clearly labeled saved/non-live

SUBMISSION
✓ public GitHub repo
✓ README complete
✓ architecture doc/diagram
✓ evaluation report with measured numbers
✓ screenshots
✓ 5-minute script
✓ demo checklist
✓ release tag
✓ final URLs verified incognito
✓ submitted before deadline
```

---

# Plan Self-Review

## Spec coverage

Mapped requirements:
- architecture: Tasks 3, 14, 26–27;
- data/financial model: Tasks 4–10;
- generator and held-out evaluation: Tasks 6, 10, 13;
- agent and verifier: Tasks 11–13;
- imports: Tasks 16, 22;
- Razorpay Test Mode: Tasks 15, 23;
- frontend UX/design: Tasks 17–24;
- run history/exports: Task 21;
- security/privacy/reliability: Tasks 25–29;
- deployment: Tasks 26–28;
- docs/demo/submission: Tasks 30–34.

No approved core requirement is intentionally omitted.

## Type/signature consistency

The plan uses:
- integer paise throughout;
- `ReconciliationPolicy` for thresholds;
- `EvidencePacket` → `AgentProposal` → `VerificationResult` flow;
- `ResidualReasoner.reason(list[EvidencePacket]) -> list[AgentProposal]`;
- `ReconciliationResult` as the engine/API/frontend contract;
- short-lived `run_id` for human resolution;
- IndexedDB `RunSnapshot` for browser history.

## Scope discipline

No authentication, database, production-money operation, Tally/Xero integration, general OCR, chatbot, subscription system, or multi-tenant feature appears in the implementation tasks.

---

# Execution Handoff

When the repo contains this plan and the approved spec, use the controlled implementation path:

**Recommended: Inline/Checkpoint Execution** — open Codex in the repo, give it the Session Start Prompt, then execute **one numbered task at a time** with `superpowers:executing-plans`. Stop at each checkpoint for human review.

A fully subagent-driven path is faster in theory, but for a solo, deadline-critical finance build with real credentials and deliberate design checkpoints, the controlled inline/checkpoint mode is safer.
