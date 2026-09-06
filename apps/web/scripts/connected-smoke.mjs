// Opt-in smoke against an already running frontend and local, credential-free API.
// FRONTEND_SMOKE_URL=http://127.0.0.1:3101 node apps/web/scripts/connected-smoke.mjs
import assert from "node:assert/strict";
import { chromium } from "@playwright/test";

const origin = process.env.FRONTEND_SMOKE_URL;
if (!origin) throw new Error("Set FRONTEND_SMOKE_URL to the local frontend origin.");
const url = new URL(origin);
if (!["localhost", "127.0.0.1"].includes(url.hostname)) {
  throw new Error("Connected smoke is restricted to a local frontend.");
}
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(origin);
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/reconcile/demo") && r.request().method() === "POST",
    { timeout: 120_000 },
  );
  await page.getByRole("button", { name: /Run Demo Reconciliation/ }).click();
  const demo = await response;
  assert.equal(demo.status(), 200);
  const run = await demo.json();
  assert.equal(run.status, "COMPLETED");
  const tie = run.tie_out_summary;
  assert.equal(BigInt(tie.total_bank_credit_paise),
    BigInt(tie.explained_bank_credit_paise) + BigInt(tie.unexplained_residual_paise));
  await page.waitForURL("**/workspace?run_id=*", { timeout: 30_000 });
  const totals = await page.locator(".tie-out").innerText();
  for (const [path, name] of [["workspace", "Workspace"], ["ledger", "Ledger"], ["exceptions", "Exceptions"], ["audit", "Audit Trail"]]) {
    await page.goto(`${origin}/${path}?run_id=${encodeURIComponent(run.run_id)}`);
    await page.getByTestId("tie-total").waitFor();
    assert.equal(await page.locator(".tie-out").innerText(), totals);
    if (path === "ledger") {
      await page.locator("tbody tr").first().waitFor();
      await page.locator("tbody tr").first().click();
      await page.getByRole("dialog").waitFor();
      await page.keyboard.press("Escape");
    }
    if (path === "audit") {
      assert.equal(await page.locator(".audit-timeline > li").count(), Math.min(20, run.audit_events.length));
    }
    for (const width of [1440, 768, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name} overflows at ${width}px`);
    }
  }
  console.log(JSON.stringify({ result: "PASS", run_id: run.run_id, tie_out_summary: tie,
    exceptions: run.exceptions.length, audit_events: run.audit_events.length,
    routes: ["workspace", "ledger", "exceptions", "audit"], widths: [1440, 768, 320] }, null, 2));
} finally {
  await browser.close();
}

