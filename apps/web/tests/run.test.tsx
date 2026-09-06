import assert from "node:assert/strict";
import { test } from "node:test";
import { parseRun, assertTieOut } from "../features/reconciliation/types";
import { parseLedger } from "../features/ledger/parse-ledger";
import { runFixture, ledgerFixture } from "../../../tests/e2e/fixtures/run";
test("validates public run and exact paise conservation", () => {
  assert.equal(parseRun(runFixture()).run_id, "run_test");
  assert.doesNotThrow(() => assertTieOut(runFixture().tie_out_summary));
});
test("rejects inconsistent, unsafe and malformed finance responses", () => {
  const run = runFixture();
  run.tie_out_summary.explained_bank_credit_paise = 80000;
  assert.throws(() => parseRun(run), /Integrity/);
  assert.throws(() => parseRun({ ...runFixture(), exceptions: null }));
  assert.throws(() =>
    parseRun({
      ...runFixture(),
      tie_out_summary: {
        ...runFixture().tie_out_summary,
        total_bank_credit_paise: Number.MAX_SAFE_INTEGER + 1,
      },
    }),
  );
});
test("parses CSV quoting without using display amounts as financial input", () => {
  const rows = parseLedger(ledgerFixture);
  assert.equal(rows.length, 2);
  assert.equal(rows[1].financial_impact_paise, 70000);
  assert.match(rows[1].evidence, /quoted "reference", verified/);
  assert.throws(() => parseLedger(ledgerFixture.replace("70000,", "70000.5,")));
  assert.throws(() => parseLedger("invalid,header\n1,2"));
});

test("audit renders a bounded first page without discarding event order", async () => {
  const { AuditTimeline } = await import("../features/audit/audit-timeline");
  const { renderToStaticMarkup } = await import("react-dom/server");
  const base = runFixture().audit_events[0];
  const events = Array.from({ length: 45 }, (_, i) => ({
    ...base,
    event_id: `event_${i}`,
    lifecycle_order: i + 1,
  }));
  const html = renderToStaticMarkup(<AuditTimeline events={events} />);
  assert.equal((html.match(/class="audit-order"/g) || []).length, 20);
  assert.match(html, /Next events/);
});
