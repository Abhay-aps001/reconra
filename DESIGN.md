# Reconra visual system

The approved `docs/superpowers/specs/2026-08-29-reconra-design.md`, sections
22–24, and Task 17 in the implementation plan remain authoritative. This file
records their implementation; it does not extend their scope. The user's approved
Task 17 visual refinement supersedes the original indigo palette with the
₹500-inspired green and parchment direction below. The subsequent user-approved
target image (ChatGPT Image Sep 5, 2026, 01_09_57 PM.png) governs the entry
composition: broad editorial hero, stronger sidebar, action-card row, and dense
capability panels. Routes, finance behavior, and Task 17 scope remain fixed.

## Direction and composition

Audit Instrument + Rupee Flow: a premium Indian-fintech entry with institutional
typography, a 15.6% navigation rail (204–250px), and an embedded decorative currency image with original flow lines.
Light only, warm ivory/parchment canvas, soft cream surfaces, charcoal ink, deep
muted currency green, sage/olive secondary tones, stone borders, and small radii.
Ochre remains reserved for review semantics. No result metrics appear before a real
run. Avoid SaaS gradients, glass, stock imagery, portraits, and decorative motion.
The patterned green primary action and faint parchment texture use only restrained
repeating print lines; the shared navigation surface stays plain.

The latest user-approved Task 17 direction supersedes the original-artwork-only rule. The supplied 500 note.png is optimized once to apps/web/public/assets/rupee-500-reference.webp (2400 × 1052, 980,522 bytes). CSS reuses this local asset for masked architectural and denomination crops with muted tint, multiply blending, and parchment edge fades. Original SVG contributes 18 flow curves; the former generated pavilion and rosettes are removed. The note is decorative, not a product result or external runtime dependency.

The desktop entry has a dominant sans-serif Reconra wordmark, a Georgia editorial
headline, three action cards plus a statement panel, four compact capability
blocks, and three static capability previews. These replace the reference's
invented metrics, charts, and exceptions; they contain no financial run results.
The artwork remains confined to the entry page, not future operational surfaces.

## Runtime ownership

`apps/web/app/globals.css` is the canonical token source. Its `:root` owns colors,
spacing, type sizes, font roles, radius, and scrollbars. Components consume those
tokens directly through CSS classes; there is no second theme or copied palette.

| Roles | Runtime tokens | Consumers |
| --- | --- | --- |
| Canvas and surfaces | `--canvas`, `--surface`, `--surface-muted` | Shell, entry, SVG fragments |
| Text and separation | `--ink`, `--muted-ink`, `--border` | All components |
| Brand and focus | `--accent`, `--accent-soft`, `--on-accent` | Active navigation, entry action, artwork, focus rings |
| Entry print artwork | `--currency-paper`, `--currency-sage`, `--currency-print`, `--currency-rule`, `--currency-stone` | Rupee Flow only |
| Status semantics | `--verified`, `--review`, `--exception` | Reserved for actual statuses with text labels; no invented statuses on entry |
| Shape and density | `--radius`, `--space-1` through `--space-7` | All layout and controls |
| Typography | `--font-sans`, `--font-serif`, `--font-mono`, `--text-*`, `--leading-body` | Interface, narrative, reference labels, numeric display |
| Scrollbars | `--scroll-thumb*`, `--scroll-track` | Document and future overflow surfaces |

Segoe UI and Georgia with system fallbacks avoid remote font requests. Monospace
is reserved for reference/sequence markers and tabular financial numerals.
`formatINRFromPaise(number)` accepts safe integer paise, rejects imprecise inputs,
and uses BigInt division/remainder with Indian grouping and two decimal places.

## Task 17 behavior and accessibility

`AppShell` owns landmarks and skip navigation; `Sidebar` owns navigation and its
mobile disclosure. Below 900px the rail becomes an in-flow disclosure with a
native button and `aria-expanded`. Below 600px entry content stacks. Document
scrolling remains natural; artwork is bounded by its SVG viewBox and masked image layers.

Tasks 18–20 enable the demo action and `/workspace`, `/ledger`, `/exceptions`, and
`/audit`. Import and Razorpay sync remain disabled with availability explanations.
The current run ID survives session navigation and reloads; no run history is stored.

Currency background layers and original inline SVG are decorative and hidden from assistive technology.
A visible caption identifies it as illustrative, with no reconciliation results.
There is no continuous animation, parallax, or remote banknote asset. The
reduced-motion media query disables animation, transitions, and smooth scrolling.
Enabled controls have visible focus and hover states; status meaning must include
text, and cannot rely on color alone.

## Verification

Unit tests cover exact integer currency display, entry copy/actions, shell, artwork
asset independence, and reduced-motion CSS. Playwright covers 1440px, 768px, 320px,
keyboard disclosure and skip navigation, computed reduced-motion behavior, and
local currency asset loading, real demo request sequencing, and operational screens.
The target-match pass includes two inspected desktop iterations and final
1440px, 768px, and 320px screenshots under `artifacts/task17/`. Existing test files
and the test architecture are retained.

## Tasks 18–20 operational contract

Operational screens use plain cream surfaces, compact tables, fine borders, and
the existing green accents. Currency artwork stays on the entry. The tie-out rail
shows backend total, explained, and residual paise only after exact conservation
validation. Unsupported category splits, confidence, and proposal details are
explicitly unavailable. Ledger filters use only actual source and reference fields.
Evidence uses a keyboard-accessible drawer; audit events retain backend lifecycle
order in pages of 20. Tables scroll locally at narrow widths.

Set `NEXT_PUBLIC_API_BASE_URL` to the backend origin (without `/api`) before
starting development or building, for example `http://127.0.0.1:8100` locally.
Next.js rewrites same-origin `/api/*` requests to that origin, avoiding a separate
browser CORS requirement. Deployments must set this value at build time. No
credentials belong in this public setting. Without an available backend, the UI
shows a safe preparation/error state. Demo completion is driven by the response;
no timer simulates progress. Approve/reject waits for server confirmation and then
refreshes the run; conflicts require a successful refresh before retrying.

Production surfaces consume the public run response and `reconciled_ledger.csv`.
Synthetic response fixtures exist only in tests. Tests cover malformed responses,
conservation, decisions, stale conflicts, navigation, evidence, and narrow screens.

For an opt-in connected smoke, start the credential-free local API and a frontend
built with its origin, then set `FRONTEND_SMOKE_URL` to the local frontend origin
and run `pnpm --dir apps/web exec node scripts/connected-smoke.mjs`. This creates
a real demo run and checks all four operational routes at 1440, 768, and 320px.
