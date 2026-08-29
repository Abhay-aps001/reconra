# Reconra — Razorpay Buildathon Track 04 Master Design Specification

**Status:** Approved architecture/design specification pending final user review  
**Date:** 2026-08-29  
**Submission deadline:** 2026-09-04  
**Build mode:** Solo developer, Buildathon-first, portfolio-clean core architecture  
**Budget:** ₹0  
**Development environment:** Windows 11 + PowerShell + Codex + VS Code  

---

## 1. Product Definition

Reconra is an AI-assisted finance controller for Razorpay settlement reconciliation.

Its job is to close one finance-operations loop end to end:

> **Settlement reconciliation → exception resolution → deterministic verification → controller action → final rupee tie-out.**

Reconra takes Razorpay-style settlement/reconciliation data, merchant orders/payments/refunds, and bank credits; reconstructs what each settlement should contain; matches records conservatively; uses AI only for unresolved ambiguity; independently verifies every AI proposal; and produces controller-ready artifacts rather than stopping at a dashboard.

### Core user question

> **Can every rupee in this Razorpay settlement be explained against the merchant's orders, payments, refunds, fees, adjustments, and bank statement — and if not, exactly why not?**

### Product tagline

**Reconra — Settlement reconciliation with evidence for every rupee.**

### Explicit non-goals

Reconra is not:

- an ERP or bookkeeping replacement;
- a generic accounting chatbot;
- a fraud detection platform;
- a Tally/Xero/Zoho Books replacement;
- a generic analytics dashboard;
- a payment-capture/refund/payout tool;
- a production-money operations system;
- a general OCR/document intelligence platform.

---

## 2. Buildathon Success Criteria

The Buildathon submission is considered successful only if the deployed system can:

1. Open without login.
2. Start a curated demo reconciliation in one click.
3. Process a 50+ record batch; the curated demo target is approximately 240–250 reconciliation lines.
4. Show real execution stages rather than a fake spinner.
5. Match clean records deterministically.
6. Route only true residuals to the AI reasoning layer.
7. Verify AI proposals independently before any financial state change.
8. Auto-apply only safe, verified, low-risk resolutions.
9. Require human review for borderline/high-impact cases.
10. Escalate genuinely unresolvable cases instead of forcing matches.
11. Produce a final rupee tie-out.
12. Report record-level, decision-level, and rupee-level metrics.
13. Expose a per-decision audit trail.
14. Export controller-ready reconciliation artifacts.
15. Sync real Razorpay Test Mode data.
16. Support smart import for CSV, XLSX, and controlled text/table PDF statements.
17. Degrade safely when the free AI provider or backend host is temporarily unavailable.
18. Pass automated backend, frontend, and end-to-end tests.
19. Be publicly deployable on free tiers.
20. Ship with a polished repository, README, architecture/evaluation documentation, and 5-minute demo package.

---

## 3. Locked System Architecture

### 3.1 High-level architecture

```text
Judge/User
   ↓
Next.js + TypeScript web app
   ↓ HTTPS
FastAPI API
   ├─ Finance engine (pure Python domain layer)
   ├─ Residual reasoning agent
   ├─ Import/parsing services
   └─ Razorpay Test Mode integration
        ↓
Controller-ready result + artifacts
```

### 3.2 Deployment architecture

```text
GitHub
 ├─ apps/web  → Vercel Hobby
 └─ apps/api  → Render Free Web Service (primary)
                    ├─ Razorpay Test API
                    └─ Free AI provider
```

The frontend and backend deploy independently.

### 3.3 Core runtime flow

```text
Ingest
  ↓
Normalize
  ↓
Deterministic matching
  ↓
Residual evidence packet
  ↓
AI proposal
  ↓
Deterministic verification
  ↓
Risk gate
  ├─ Auto-apply
  ├─ Human review
  └─ Escalate
  ↓
Metrics + audit + artifacts + tie-out
```

### 3.4 Architectural invariants

- The finance engine must be usable without FastAPI.
- The finance engine must be usable without AI.
- The finance engine must not import the synthetic generator.
- Production reconciliation code must not read ground truth.
- The AI layer must not calculate money or mutate the ledger directly.
- Every money value is represented as integer paise.
- Every applied resolution must preserve exact money-conservation invariants.
- Re-running or re-applying a decision must be idempotent.

---

## 4. Final Technology Stack

### Frontend

- Next.js (stable release at project initialization)
- TypeScript with strict mode
- Tailwind CSS
- Radix primitives where needed
- Lucide icons
- TanStack Table for dense financial tables
- Zod for browser-side validation
- React Hook Form for import/mapping forms
- Lightweight motion library only in the final polish phase

### Backend/API

- Python 3.13 if dependency compatibility is clean; Python 3.12 is the allowed fallback
- FastAPI
- Pydantic
- pandas
- RapidFuzz
- httpx
- openpyxl
- pdfplumber

### Testing / quality

- pytest
- pytest-cov
- Hypothesis
- Ruff
- Python type checking
- ESLint
- TypeScript strict checks
- Playwright
- GitHub Actions

### Package management

- pnpm for JavaScript/TypeScript
- Python virtual environment + pip/requirements for Python

### Runtime AI

Provider abstraction is mandatory.

Primary free-tier target at planning time:

- Gemini Developer API, free-tier Flash model (currently Gemini 3.7 Flash)

Optional backup:

- Groq structured-output-capable model

Required fallback:

- deterministic-only / AI-disabled mode

The production engine must call a provider-neutral interface such as `ResidualReasoner.reason(case)` rather than vendor SDK code throughout the codebase.

### Runtime Razorpay integration

- Deployed Reconra uses official Razorpay Test Mode REST APIs.
- Razorpay Official MCP is a Codex development aid, not a deployed runtime dependency.

---

## 5. Repository Structure

```text
reconra/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── styles/
│   │   └── public/
│   │
│   └── api/
│       ├── app/
│       │   ├── routes/
│       │   ├── services/
│       │   ├── schemas/
│       │   ├── middleware/
│       │   └── main.py
│       └── requirements.txt
│
├── engine/
│   └── reconra/
│       ├── models/
│       ├── ingestion/
│       ├── normalization/
│       ├── matching/
│       ├── reconciliation/
│       ├── evidence/
│       ├── verification/
│       ├── policy/
│       ├── metrics/
│       ├── artifacts/
│       └── audit/
│
├── agent/
│   ├── schemas/
│   ├── prompts/
│   ├── providers/
│   └── reasoner.py
│
├── generator/
│   ├── src/
│   ├── scenarios/
│   └── README.md
│
├── data/
│   ├── fixtures/clean/
│   ├── development/messy/
│   ├── demo/
│   ├── heldout/
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
├── docs/
│   ├── architecture/
│   ├── evaluation/
│   ├── methodology/
│   └── superpowers/specs/
│
├── .github/workflows/
├── AGENTS.md
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
└── pnpm-workspace.yaml
```

### Dependency boundary

`engine/` may not import `generator/` or ground-truth modules.

The evaluation harness may access both input and ground truth, but production runtime code may access input only.

---

## 6. Demo Merchant and Data Model

### 6.1 Fictional merchant

**Nivara** — fictional Indian D2C home and lifestyle merchant.

- Country: India
- Settlement currency: INR
- Main payment methods: UPI, credit card, debit card, netbanking, wallet, small EMI subset
- Typical order value: ₹499–₹14,999
- Main benchmark period: approximately two weeks

Nivara is only the demo merchant; it is not the Reconra product brand.

### 6.2 Data-source types

Reconra supports four main data paths:

1. Curated synthetic benchmark/demo dataset
2. Razorpay Test Mode sync
3. Smart file import
4. Controlled text/table PDF bank-statement import

### 6.3 Synthetic datasets

Five distinct synthetic dataset roles are required:

#### A. Clean development fixture

- ~60–80 reconciliation records
- nearly all clean deterministic matches
- expected to reconcile perfectly before messy development begins

#### B. Messy development dataset

- ~150–200 reconciliation records
- broad break taxonomy
- used for debugging and threshold development

#### C. Held-out evaluation dataset

- generated and frozen before final matcher evaluation;
- not used for threshold tuning or debugging;
- broad enough to measure false matches, abstention, break-class accuracy, and rupee coverage;
- used for the official benchmark report and rules-vs-agent ablation.

#### D. Curated judge/demo dataset

- approximately 240–250 reconciliation lines;
- ~220 orders;
- ~210 captured payments;
- ~15–20 refunds;
- several adjustments;
- ~8–10 settlement batches;
- corresponding bank credits;
- deliberate ambiguous and unresolvable breaks;
- optimized only for narrative clarity after core behavior is frozen, never by changing expected answers or weakening difficulty to improve metrics.

#### E. Stress dataset

Generated at multiple scales, e.g. 1k / 5k / 10k records, primarily for deterministic throughput and resource testing.

### 6.4 Ground-truth integrity

Synthetic generation must produce input artifacts and a separate ground-truth artifact.

Production code receives input only.

Ground truth may encode:

- expected match relationships;
- expected break classes;
- whether a case is resolvable;
- expected financial impact.

Generator and matcher may not share implementation logic or hidden configuration that reveals the answer.

### 6.5 Reproducibility

Dataset generation must use fixed seeds for:

- clean development
- messy development
- held-out evaluation
- curated demo
- stress benchmark

Same generator version + same seed must reproduce the same dataset.

---

## 7. Razorpay Reconciliation Contract

The synthetic raw recon rows should mirror the current Razorpay combined settlement reconciliation response shape.

Required fields to model:

- `entity_id`
- `type`
- `debit`
- `credit`
- `amount`
- `currency`
- `fee`
- `tax`
- `on_hold`
- `settled`
- `created_at`
- `settled_at`
- `settlement_id`
- `description`
- `notes`
- `payment_id`
- `settlement_utr`
- `order_id`
- `order_receipt`
- `method`
- `card_network`
- `card_issuer`
- `card_type`
- `dispute_id`

Allowed transaction types are constrained to:

- `payment`
- `refund`
- `transfer`
- `adjustment`

A chargeback/dispute scenario must be represented using supported recon structures such as `adjustment` plus `dispute_id`; no invented `chargeback` recon transaction type is allowed.

---

## 8. Canonical Internal Models

External source-specific structures must be normalized before matching.

Core canonical entities:

### Order

- `order_id`
- `receipt`
- `created_at`
- `amount_paise`
- `currency`
- `status`

### Payment

- `payment_id`
- `order_id`
- `amount_paise`
- `currency`
- `method`
- `captured_at`
- `status`
- optional card metadata

### Refund

- `refund_id`
- `payment_id`
- `amount_paise`
- `created_at`
- `status`

### SettlementEntry

- source recon identity/type
- debit/credit/amount in paise
- fee/tax in paise
- timestamps
- settlement ID and UTR
- optional payment/order/method/dispute references

### BankTransaction

- `bank_transaction_id`
- `transaction_date`
- optional `value_date`
- `description`
- optional `reference`
- optional `utr`
- `credit_paise`
- `debit_paise`
- source metadata

### Adjustment

- `adjustment_id`
- optional settlement/payment/dispute references
- `amount_paise`
- `reason`
- `created_at`

---

## 9. Financial Invariants and Policy

### 9.1 Paise-only arithmetic

All monetary calculations use integers representing paise.

No financial calculation may use binary floating-point values.

### 9.2 Configurable settlement policy

Settlement timing must be policy-driven rather than hard-coded.

Policy should support concepts such as:

- domestic settlement cycle
- working-day treatment
- holiday handling
- instant-settlement behavior
- amount tolerance
- date windows
- UTR/narration matching thresholds
- auto-apply thresholds
- review thresholds
- financial-impact thresholds

### 9.3 Configurable fee schedule

The engine must not assume a universal Razorpay fee by payment method.

Demo fees are driven by a merchant-specific configuration used for the synthetic benchmark.

### 9.4 Money conservation

At all times:

```text
total_bank_credit_paise
=
explained_bank_credit_paise
+
unexplained_residual_paise
```

Every applied resolution must preserve this invariant exactly.

### 9.5 Idempotency

A resolution cannot be applied twice.

Resolution identity must derive from stable run/exception/action information so repeated requests do not double-count financial impact.

---

## 10. Reconciliation Engine

The deterministic engine runs before AI.

### Pass 1 — exact identity matching

Use strong identifiers first:

- payment ID
- order ID
- settlement ID
- settlement UTR
- refund ID
- entity ID

### Pass 2 — settlement-to-bank matching

Evaluate candidate bank credits using explicit evidence:

- exact/normalized UTR
- compatible amount
- compatible date
- narration evidence

The system must preserve why a candidate scored well instead of only storing one opaque score.

### Pass 3 — settlement decomposition

Recompute expected settlement from:

- captured payments
- fees
- tax
- refunds
- adjustment debits/credits
- other supported settlement movements

Do not simply trust a reported net field.

### Pass 4 — deterministic tolerances

Apply only policy-configured tolerance rules.

### Pass 5 — fuzzy identity matching

Use RapidFuzz/reference normalization for damaged narrations/UTRs, but fuzzy similarity alone may not auto-match financial records.

It must be supported by compatible amount/date/identity evidence.

---

## 11. Break Taxonomy

Allowed break classes must be an enum, not free-form model output.

Initial taxonomy:

- `CLEAN_MATCH`
- `ROUNDING_VARIANCE`
- `FEE_VARIANCE`
- `TAX_VARIANCE`
- `SETTLEMENT_CUTOFF`
- `DELAYED_SETTLEMENT`
- `INSTANT_SETTLEMENT_VARIANCE`
- `REFUND_NETTED_LATER`
- `PARTIAL_REFUND`
- `MANGLED_UTR`
- `MANGLED_NARRATION`
- `DUPLICATE_LEDGER_ROW`
- `DUPLICATE_BANK_CREDIT`
- `DISPUTE_ADJUSTMENT`
- `GENERAL_ADJUSTMENT`
- `MISSING_ORDER`
- `MISSING_PAYMENT`
- `MISSING_SETTLEMENT`
- `MISSING_BANK_CREDIT`
- `AMOUNT_MISMATCH`
- `UNRESOLVABLE`

The benchmark must include intentionally unresolvable cases so abstention can be measured.

---

## 12. Residual Agent Architecture

### 12.1 Role of AI

The AI is an **exception reasoning layer**, not a finance calculator.

AI is allowed to:

- classify residual cause;
- compare ambiguous textual evidence;
- reason about mangled narrations/UTRs;
- rank plausible candidates;
- generate a concise hypothesis;
- recommend an action;
- return insufficient evidence / unresolvable.

AI is prohibited from:

- calculating fees/tax/settlement totals;
- modifying money values;
- writing ledger entries directly;
- inventing record IDs or evidence;
- changing thresholds or policy;
- reading ground truth;
- performing Razorpay mutations;
- bypassing deterministic verification.

### 12.2 Evidence packet

Only unresolved residual cases are sent to the model.

Evidence packets must contain sanitized, bounded facts such as:

- amount/date differences;
- candidate IDs;
- normalized/truncated reference evidence;
- precomputed settlement breakdown;
- related refund/adjustment counts;
- known deterministic facts;
- unresolved reason.

Raw uploaded bank statements and unnecessary personal information are not sent to the free AI provider.

### 12.3 Structured proposal schema

The AI must return a strict schema containing fields conceptually equivalent to:

- `break_class`
- `hypothesis`
- `candidate_resolution`
- `confidence`
- `evidence`
- `recommended_action`

Malformed or unsupported output is rejected safely.

### 12.4 Confidence is not permission

Model confidence never directly authorizes financial changes.

Every proposal must pass deterministic verification and the risk gate.

---

## 13. Deterministic Verifier and Risk Gate

The verifier independently checks:

- candidate existence;
- amount compatibility;
- date-window compatibility;
- candidate uniqueness / unused status;
- one-to-one or allowed relationship constraints;
- claimed evidence actually exists;
- proposed break class is compatible with observed facts;
- money conservation;
- no impossible residual state is introduced.

### Resolution states

#### `AUTO_RESOLVED`

Requires:

- valid schema;
- supported break class;
- deterministic verification pass;
- confidence above the relevant threshold;
- risk policy permits auto-application;
- financial invariants preserved.

#### `REVIEW_REQUIRED`

Used for plausible but insufficiently safe autonomous resolutions or high-impact cases.

#### `ESCALATED`

Used when:

- evidence is insufficient;
- no valid candidate exists;
- verification fails;
- model response is malformed;
- model/API is unavailable;
- timeout/rate limit occurs.

#### `REJECTED`

Used when a human rejects a proposed resolution.

The system does not silently retry random alternatives after explicit rejection.

### Risk policy

Autonomy depends on:

- break class;
- verification outcome;
- model confidence;
- financial impact.

High financial impact can force human review even when confidence is high.

---

## 14. AI Failure Behavior

The application must remain functional if AI is unavailable.

Required behavior:

```text
Deterministic reconciliation completes
   ↓
AI unavailable / timeout / rate limit
   ↓
Residuals safely marked review/escalated
   ↓
Metrics and artifacts still generated
```

The user sees a calm message indicating that deterministic reconciliation completed and unresolved cases were safely escalated.

Retries are bounded; no infinite retry loops are allowed.

---

## 15. Audit Trail

Every material action generates an audit event containing fields conceptually equivalent to:

- event ID
- run ID
- optional exception ID
- timestamp
- actor: rule engine / agent / verifier / user / system
- action
- evidence
- decision
- optional confidence
- verification status
- financial impact in paise
- before/after state where relevant

Audit logs are financial decision logs and are distinct from backend technical logs.

---

## 16. Metrics and Evaluation

### 16.1 Required metrics

Each benchmark run should calculate:

- total records
- deterministic matches
- agent-assisted matches
- auto-resolved count
- review-required count
- escalated count
- record coverage
- auto-resolution precision
- false-match rate
- resolvable-record recall
- correct-abstention rate
- per-break-class accuracy
- processing time
- records/second
- AI-call count
- estimated inference cost
- rupees explained
- rupee residual

### 16.2 Three evaluation levels

#### Record-level

How many records were resolved?

#### Decision-level

Were the proposed/made matches actually correct?

#### Rupee-level

How much of total bank credit is explained exactly?

### 16.3 Headline metrics

The pitch should emphasize:

1. false-match rate;
2. rupee coverage / residual;
3. correct abstention;
4. rules-vs-agent contribution.

### 16.4 No target-score tuning

Do not tune the synthetic dataset to produce a desired match percentage.

Thresholds are developed on development data and frozen before held-out benchmark evaluation.

### 16.5 Ablation benchmark

Run the same held-out dataset in:

- deterministic-only mode;
- deterministic + residual agent + verifier mode.

Compare actual measured coverage, false-match rate, rupee coverage, and abstention behavior.

---

## 17. Output Artifacts

Every completed reconciliation run should be able to export:

- `reconciled_ledger.csv`
- `exception_worklist.csv`
- `audit_log.json`
- `reconciliation_summary.json`

Optional bonus after core completion:

- `reconciliation_report.pdf`

The exported ledger/worklist must derive from actual engine results, not mocked UI state.

---

## 18. Import Pipeline

### Supported Buildathon input types

- CSV
- XLSX
- controlled text/table PDF

### Explicitly unsupported

- arbitrary scanned/image-only PDF OCR
- macro-enabled Excel workflows
- general document understanding

### Import flow

```text
Upload
  ↓
File classification
  ↓
Column detection
  ↓
Smart mapping suggestions
  ↓
Human confirmation/edit
  ↓
Preview + validation
  ↓
Canonical models
  ↓
Reconciliation
```

### Smart mapping hierarchy

1. deterministic/exact header mapping;
2. normalized/fuzzy header matching;
3. AI-assisted suggestion only as a last resort;
4. user confirmation before reconciliation.

### File safety limits

Planned limits:

- single file up to 10 MB;
- combined upload up to 25 MB;
- parsed rows up to 10,000;
- supported extensions only: `.csv`, `.xlsx`, `.pdf`.

Uploaded files are temporary and are not retained as permanent user storage.

---

## 19. Razorpay Test Mode Integration

### Runtime behavior

The deployed backend may fetch test-mode entities such as orders, payments, refunds, and supported reconciliation/settlement data needed for the demo.

The frontend never receives the Razorpay secret.

A clear `TEST MODE` indicator must be visible.

### Safety rule

Reconra is a read/retrieval/reconciliation demo.

It must not autonomously:

- capture payments;
- initiate payouts;
- create payment links;
- issue refunds;
- mutate production money state.

Repository instructions must treat the Razorpay MCP as read-only unless the human explicitly authorizes a mutation.

The Buildathon deployment must be configured for Razorpay Test Mode only and should fail closed if production-style configuration is detected.

---

## 20. API Surface

Keep the HTTP API small and explicit.

Initial endpoint set, subject only to naming refinement during implementation:

- `GET /api/health`
- `POST /api/reconcile/demo`
- `POST /api/reconcile`
- `POST /api/import/inspect`
- `POST /api/import/map`
- `POST /api/razorpay/sync`
- `POST /api/runs/{run_id}/exceptions/{exception_id}/approve`
- `POST /api/runs/{run_id}/exceptions/{exception_id}/reject`
- `GET /api/runs/{run_id}/export/{artifact}`

API errors must return predictable machine-readable error codes and recoverability information.

---

## 21. Runtime State and Run History

### Backend

No database.

Use a short-lived in-memory run cache for convenience during a live session.

The backend remains logically stateless/durable-state-free; a host restart may clear active runs.

### Frontend

Use IndexedDB for recent run history/results with a hard retention cap, planned around 10 recent runs.

Run IDs should be non-sequential, human-readable identifiers such as:

`RC-20260829-A3F7`

---

## 22. Frontend UX Contract

### 22.1 Primary user journey

```text
Rupee Flow
  ↓
Workspace
  ↓
Reconcile
  ↓
Tie-Out
  ↓
Investigate
  ↓
Verify
  ↓
Act
  ↓
Audit
  ↓
Export
```

### 22.2 First 10 seconds

The opening experience must immediately communicate:

- what Reconra does;
- the demo merchant/data context;
- one dominant CTA: **Run Demo Reconciliation**;
- secondary paths: Import Data and Sync Razorpay Test Data.

No login is required.

### 22.3 Primary application surfaces

1. Reconciliation Workspace
2. Runs
3. Ledger
4. Exceptions
5. Audit
6. Import
7. Razorpay
8. Methodology

Do not add irrelevant SaaS pages such as Pricing, Blog, Testimonials, or generic AI chat.

### 22.4 Run Overview

The dominant result should be the **Tie-Out Rail** rather than generic KPI cards.

Above the fold after completion, the judge should be able to see:

- total bank credit;
- explained amount;
- unexplained residual;
- coverage;
- false-match result;
- unresolved-exception count;
- direct path to inspect exceptions.

### 22.5 Ledger

The ledger is a first-class dense data surface with:

- sticky headers;
- right-aligned money;
- tabular numerals;
- compact row density;
- filters;
- search;
- row inspection drawer;
- status/resolution source;
- horizontal scrolling only when necessary.

### 22.6 Exception Workbench

Each exception should show:

- break class;
- financial impact;
- evidence;
- proposal;
- agent confidence where applicable;
- deterministic verification result;
- approve/reject actions only where human review is actually required.

### 22.7 Audit

The audit surface should read like an investigator/controller timeline, not a raw server log.

### 22.8 Smart Import

Users can:

- upload supported files;
- review detected file type;
- review/edit column mapping;
- inspect parsed preview rows;
- see validation warnings/errors;
- proceed only after confirmation.

### 22.9 Razorpay Test Mode

The Razorpay surface must clearly communicate:

- connection status;
- Test Mode status;
- available/synced record counts;
- sync action;
- safe error/retry state.

### 22.10 Saved benchmark fallback

If the free backend is unavailable, the frontend may offer a clearly labeled **View saved benchmark** path using a bundled verified result snapshot.

It must never label a saved snapshot as a live reconciliation run.

---

## 23. Visual Design Specification

### 23.1 Design direction

**Audit Instrument + Rupee Flow**

Operational UX should feel like:

> payment operations console + audit workpaper + modern fintech product.

Design keywords:

- evidence-driven
- calm
- dense
- precise
- operational
- trustworthy
- Indian-fintech aware
- human-designed

Avoid:

- generic dashboard grids;
- glassmorphism;
- neon/cyberpunk styling;
- purple/blue startup gradients;
- giant KPI cards;
- excessive rounded cards;
- stock illustrations;
- AI sparkles/stars;
- chat panels;
- decorative charts;
- excessive shadows or badges.

### 23.2 Light-first audit workstation

Use:

- warm off-white/cool-neutral canvas;
- white/localized surfaces where needed;
- near-black primary text;
- restrained neutral borders;
- deep indigo/ink-blue brand accent;
- semantic status colors only when status has meaning.

### 23.3 Typography

Use a high-quality sans-serif for interface/narrative text and tabular-numeric/monospace treatment for financial data, IDs, UTRs, and technical evidence.

Indian currency formatting is mandatory:

`₹52,84,190`, not `₹5,284,190`.

### 23.4 Shape and elevation rules

- low radius for tables/data surfaces;
- moderate radius for controls/dialogs;
- avoid universal large rounded cards;
- hierarchy should come primarily from borders, spacing, typography, and surface tone;
- shadows only for genuinely floating UI such as dialogs/dropdowns/drawers.

### 23.5 Signature visual: Tie-Out Rail

The recurring visual motif shows how total bank credit is decomposed into:

- rules-verified amount;
- agent-verified amount;
- review amount;
- unexplained residual.

The visual identity should communicate **the path of every rupee** rather than a generic color gradient.

### 23.6 Interactive Rupee Flow opening

The entry experience uses stylized, abstract Indian-currency-inspired motifs rather than high-resolution literal banknote scans. It must not reproduce a real Indian banknote faithfully or use recognizable portraits, RBI emblems, security marks, signatures, serial layouts, or other protected note artwork as a near-copy. The visual system should evoke rupee-denominated money through original abstract geometry, denomination typography, transaction fragments, and guilloché-inspired patterns.

Possible ingredients:

- cropped note-like fragments;
- denomination numerals;
- serial/reference-like strings;
- subtle guilloché/security-line patterns;
- rupee symbols;
- abstract note silhouettes;
- transaction-reference fragments.

The interaction tells a financial story:

```text
scattered money
  ↓
transactions organize
  ↓
many payments collapse into settlement
  ↓
fees/tax/refunds separate
  ↓
bank credit emerges
  ↓
Tie-Out Rail / reconciled truth
```

This is Reconra's equivalent of an environmental scroll transformation.

### 23.7 Interaction boundaries

The expressive Rupee Flow is for entry/storytelling moments only.

Once the operational workspace opens, currency-background motion stops so tables, exceptions, and audit content remain calm and readable.

Mouse/parallax interaction must be subtle and bounded.

No falling money, aggressive cursor-following notes, constant background movement, or gambling/crypto aesthetics.

### 23.8 Motion

Motion explains state changes only.

Good examples:

- reconciliation stage progression;
- residual amount updating after approval;
- rows moving from review to resolved;
- Tie-Out Rail updating.

No confetti, particle systems, constantly bouncing controls, gradient blobs, or decorative motion.

`prefers-reduced-motion` must provide a useful static experience.

### 23.9 Design-tool orchestration

Design tooling should be applied in sequence, not simultaneously:

1. `frontend-design-premium` — page composition
2. `21st.dev MCP` — discover only useful primitives
3. `12ui-design` — targeted component review
4. `apple-design` — hierarchy/interaction review
5. `emil-design-eng` — design-engineering refinement
6. `improve-animations` — final motion pass only
7. Playwright — real browser verification

The Reconra design specification overrides generic suggestions from any design skill.

---

## 24. Loading, Empty, Error, and Accessibility States

### Loading

Show real reconciliation phases rather than a generic spinner.

### Empty

Use concise finance-oriented copy with no giant decorative illustrations.

### Error

Errors must be calm and actionable.

Example behavior:

- Razorpay sync failure must not modify reconciliation state.
- AI failure must not prevent deterministic completion.
- PDF parsing failure should suggest CSV/XLSX or a supported text/table PDF.

### Accessibility

- keyboard/focus support for all primary controls;
- visible focus states;
- proper labels;
- sufficient contrast;
- desktop-first layout with non-breaking tablet/mobile fallback;
- reduced-motion support.

---

## 25. Security and Privacy

### Secrets

Secrets exist only in ignored local env files and deployment secret stores.

Required examples:

- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `GEMINI_API_KEY`
- optional `GROQ_API_KEY`

Never commit or expose secrets in:

- Git;
- frontend code;
- README;
- screenshots;
- prompt examples;
- fixtures;
- `AGENTS.md`.

### CORS

Production must allow only the actual Reconra frontend origin(s), not wildcard CORS.

### Logging

Technical logs must redact:

- API keys;
- account numbers;
- full uploaded documents;
- unnecessary personal information.

### Free AI privacy

Only sanitized residual evidence packets may be sent to the external free-tier AI provider.

Raw bank statements are not sent to the AI provider.

---

## 26. CI/CD and Deployment Reliability

### CI on push to main

Python side:

- Ruff
- type checks
- pytest

Web side:

- lint
- TypeScript checks
- build

Final release also requires Playwright smoke/e2e tests against deployment.

### Backend cold-start mitigation

Render free services may sleep after inactivity, so Reconra should:

1. call `/api/health` on initial page load;
2. show an explicit engine-preparing state instead of a fetch error;
3. include a pre-demo warm-up checklist;
4. maintain the honest saved-benchmark fallback.

---

## 27. Codex Development Contract

Codex works directly in the repository under human-controlled phases.

The human manually handles:

- real API secrets;
- `.env` values;
- GitHub/Vercel/backend-host authorization;
- deployment secret configuration;
- any sensitive Razorpay action.

Codex handles:

- repository files;
- package installation;
- implementation;
- tests;
- refactors;
- routine fixes;
- documentation drafts.

### Development method

Do not use one giant “build everything” prompt.

For each implementation phase:

```text
Define phase
  ↓
Codex implements that subsystem
  ↓
Codex runs required tests
  ↓
Fix failures
  ↓
Human checkpoint/review
  ↓
Commit
  ↓
Next phase
```

### Project `AGENTS.md` must encode

- read spec before implementation;
- architecture may not change silently;
- paise-only finance arithmetic;
- ground-truth isolation;
- generator/matcher isolation;
- no LLM financial arithmetic;
- no unverified AI mutation;
- false matches are prioritized as the critical error class;
- conservative abstention;
- Razorpay Test Mode only;
- Razorpay MCP read-only by default;
- design spec overrides generic design-skill output;
- no mocked result data after real engine output exists;
- no new dependencies without reason;
- no later phase while current tests fail.

### Custom `finance-controller` skill

Create before core finance implementation.

It must encode:

- paise-only math;
- money conservation;
- fee/policy configuration;
- generator/ground-truth isolation;
- break taxonomy;
- false-match priority;
- agent boundaries;
- verification requirements;
- abstention policy;
- idempotency;
- Razorpay test-mode constraints;
- audit requirements;
- evaluation integrity.

---

## 28. Git Strategy

Because the project is solo and time-bounded:

- use `main` as the primary branch;
- use short-lived feature branches only for risky/large work;
- merge quickly after tests pass;
- do not use GitFlow.

Commit history should reflect deliberate subsystem completion, for example:

- initialize workspace
- synthetic generator
- canonical finance models
- deterministic matcher
- invariant tests
- residual agent
- API layer
- workspace UI
- exception workbench
- smart import
- Razorpay Test sync
- e2e demo flows
- benchmark/methodology docs
- Buildathon release preparation

---

## 29. Complete Product Definition of Done

Reconra is not considered finished until all of the following are true:

### Core engine

- official/current Razorpay-style recon schema represented;
- paise-only arithmetic enforced;
- clean fixture reconciles correctly;
- messy development data supported;
- held-out benchmark exists;
- stress-data generation exists;
- generator cannot leak ground truth into production matcher;
- deterministic matcher works without AI;
- money conservation property passes;
- idempotency property passes.

### Agent

- residual evidence packets work;
- structured proposal validation works;
- AI cannot mutate state directly;
- verifier independently validates evidence;
- risk gate works;
- auto/review/escalate/rejected states work;
- timeout/rate-limit/provider failure degrades safely;
- deterministic-only fallback works;
- ablation benchmark exists.

### Product

- one-click curated demo works;
- real processing stages visible;
- Tie-Out Rail works;
- ledger explorer works;
- exception workbench works;
- human approval changes the financial state correctly;
- audit trail works;
- CSV smart import works;
- XLSX smart import works;
- controlled PDF import works;
- Razorpay Test Mode sync works;
- exports work;
- IndexedDB run history works;
- no login required.

### Design

- Rupee Flow entry experience works without hurting performance;
- operational workspace is calm and dense;
- no generic AI-dashboard aesthetic;
- responsive fallback does not break;
- keyboard/focus flow works;
- reduced-motion mode works.

### Deployment / quality

- Vercel frontend deployment works;
- free FastAPI host deployment works;
- backend health/cold-start experience works;
- saved benchmark fallback works honestly;
- CI passes;
- Playwright critical flows pass against deployment;
- secrets are correctly configured and never committed.

### Submission package

- public GitHub repository polished;
- README complete;
- architecture diagram complete;
- methodology documentation complete;
- benchmark/evaluation report complete;
- screenshots prepared;
- 5-minute demo path scripted and rehearsed;
- final pitch/story prepared;
- backup demo flow tested;
- final submission checklist completed.

---

## 30. Scope Freeze

No new core feature may enter the Buildathon implementation unless it directly improves Track 04 judging or removes a reliability blocker.

Explicitly out of Buildathon scope:

- authentication;
- multi-tenancy;
- database persistence;
- billing/subscriptions;
- production Razorpay operations;
- payment capture/refund/payout mutation;
- Tally/Xero/Zoho Books integrations;
- direct accounting-software journal posting;
- fraud detection;
- generic financial chatbot;
- general scanned-document OCR;
- native mobile app;
- marketplace/split-settlement accounting as a primary demo;
- international/FX accounting as a primary demo.

The Buildathon implementation must favor correctness, auditability, evidence, deployment reliability, and demo clarity over feature count.

---

## 31. Five-Minute Demo Narrative Contract

The final UI and implementation must support this sequence:

1. Open Reconra.
2. Explain the many-transactions-to-one-settlement problem through the Rupee Flow visual.
3. Start the curated demo with one click.
4. Show real processing stages.
5. Land on the final rupee tie-out.
6. Show measured rules-vs-agent contribution.
7. Inspect one difficult agent-assisted resolution with evidence and verifier checks.
8. Inspect one intentionally unresolvable exception and show why Reconra refuses to guess.
9. Show audit trail.
10. Show/export controller-ready artifacts.
11. Briefly prove Razorpay Test Mode integration.
12. End on the thesis: **Reconra does not generate finance answers faster; it verifies which answers are safe to trust and exposes exactly what remains unexplained.**

---

## 32. Final Design Thesis

Reconra's defining idea is:

> **Scattered money becomes structured evidence, and structured evidence becomes reconciled truth.**

The product should visually and technically reinforce the same principle:

- many payments become one settlement;
- one settlement is decomposed into explainable components;
- ambiguous residuals are reasoned about, not guessed;
- every accepted resolution is independently verified;
- every decision is auditable;
- every remaining rupee residual is visible.

That is the Buildathon product contract.
