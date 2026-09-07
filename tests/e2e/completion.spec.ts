import { expect, test } from "../../apps/web/node_modules/@playwright/test";
import { runFixture } from "./fixtures/run";
import { readFile } from "node:fs/promises";

const artifactBodies = {
  "reconciled_ledger.csv": "record_type,source_id\npayment,pay_1\n",
  "exception_worklist.csv": "exception_id\nex_review\n",
  "audit_log.json": "[{\"event_id\":\"event_1\"}]\n",
  "reconciliation_summary.json": "{\"run_id\":\"run_test\"}\n",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ json: { status: "ok", environment: "test" } }));
});

test("history saves a valid demo, opens saved-only fallback, and exports exact backend artifacts", async ({ page }) => {
  let live = true;
  await page.route("**/api/reconcile/demo", (route) => route.fulfill({ json: runFixture() }));
  await page.route("**/api/runs/run_test", (route) => live ? route.fulfill({ json: runFixture() }) : route.fulfill({ status: 404, json: { code: "RUN_NOT_FOUND" } }));
  for (const [name, body] of Object.entries(artifactBodies)) await page.route(`**/api/runs/run_test/artifacts/${name}`, (route) => route.fulfill({ body }));
  await page.goto("/");
  await page.getByRole("button", { name: "Run Demo Reconciliation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Reconciliation complete" })).toBeVisible();
  for (const [name, body] of Object.entries(artifactBodies)) {
    const label = name === "reconciled_ledger.csv" ? "Reconciled ledger CSV" : name === "exception_worklist.csv" ? "Exception worklist CSV" : name === "audit_log.json" ? "Audit JSON" : "Summary JSON";
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: label }).click();
    const file = await download;
    expect(file.suggestedFilename()).toMatch(/^reconra-run_test-(ledger\.csv|exceptions\.csv|audit\.json|summary\.json)$/);
    const location = await file.path();
    expect(location).toBeTruthy();
    expect(await readFile(location!, "utf8")).toBe(body);
  }
  await page.getByRole("link", { name: "Runs", exact: true }).click();
  await expect(page.getByText("run_test", { exact: true })).toBeVisible();
  live = false;
  await page.getByRole("button", { name: "Open", exact: true }).click();
  await expect(page.getByText("SAVED RUN SNAPSHOT", { exact: false })).toBeVisible();
  await expect(page.getByText("Exports require a live backend run.")).toBeVisible();
  await page.getByRole("link", { name: "Exceptions", exact: true }).click();
  await page.getByRole("button", { name: "Inspect ex_review" }).click();
  await expect(page.getByRole("dialog")).toContainText("Saved snapshots cannot change");
  await page.keyboard.press("Escape");
  await page.getByRole("link", { name: "Runs", exact: true }).click();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByText("No reconciliation runs saved yet.")).toBeVisible();
});

test("import confirms mappings, validates, reconciles, and supports CSV/XLSX/text-table PDF selection", async ({ page }) => {
  const inspection = {
    import_id: "import_123", warnings: [], files: [{ filename: "bank.csv", source_type: "csv", columns: ["Txn Date", "Narration", "Deposit Amt", "Ref No"], row_count: 1, sample_rows: [{ "Txn Date": "2026-01-01", Narration: "credit", "Deposit Amt": "1000", "Ref No": "utr_1" }], candidate_role: "bank_transactions", suggestions: [
      { source_column: "Txn Date", target_field: "transaction_date", confidence: 1, reason: "exact_alias" }, { source_column: "Narration", target_field: "description", confidence: 1, reason: "exact_alias" }, { source_column: "Deposit Amt", target_field: "credit_paise", confidence: 1, reason: "exact_alias" }, { source_column: "Ref No", target_field: "utr", confidence: 1, reason: "exact_alias" },
    ] }],
  };
  await page.route("**/api/import/inspect", (route) => route.fulfill({ json: inspection }));
  await page.route("**/api/import/import_123/validate", (route) => route.fulfill({ json: { import_id: "import_123", validated: true } }));
  await page.route("**/api/import/import_123/reconcile", (route) => route.fulfill({ json: runFixture() }));
  await page.route("**/api/runs/run_test", (route) => route.fulfill({ json: runFixture() }));
  await page.goto("/import");
  const input = page.getByLabel("Import source files");
  await expect(input).toHaveAttribute("accept", /\.xlsx.*\.pdf/);
  await input.setInputFiles({ name: "bank.csv", mimeType: "text/csv", buffer: Buffer.from("Txn Date,Narration,Deposit Amt,Ref No\n2026-01-01,credit,1000,utr_1\n") });
  await expect(page.getByText("Backend classification:")).toBeVisible();
  await expect(page.getByText("Scanned PDF OCR is not supported.")).toBeVisible();
  await page.getByRole("button", { name: "Confirm mappings and validate" }).click();
  await expect(page.getByText("Validation complete.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Reconcile imported data" }).click();
  await expect(page).toHaveURL(/workspace\?run_id=run_test/);
});

test("Razorpay remains Test Mode only and methodology explains governance", async ({ page }) => {
  await page.route("**/api/razorpay/sync", (route) => route.fulfill({ json: runFixture() }));
  await page.route("**/api/runs/run_test", (route) => route.fulfill({ json: runFixture() }));
  await page.goto("/razorpay");
  await expect(page.getByText("TEST MODE · READ ONLY")).toBeVisible();
  await expect(page.getByText(/payments, refunds, captures, or settlement changes/)).toBeVisible();
  await expect(page.getByText(/API secret|Authorization/)).toHaveCount(0);
  await page.getByRole("button", { name: "Sync Razorpay Test Mode" }).click();
  await expect(page).toHaveURL(/workspace\?run_id=run_test/);
  await page.goto("/methodology");
  for (const text of ["Integer paise only", "Deterministic reconciliation first", "Abstention is a result", "Truth isolation and auditability", "Razorpay sync is Test Mode only", "scanned-PDF OCR is not supported"]) await expect(page.getByText(text, { exact: false })).toBeVisible();
});

test("Razorpay credentials unavailable remains safe and keeps the Test Mode boundary visible", async ({ page }) => {
  await page.route("**/api/razorpay/sync", (route) => route.fulfill({ status: 503, json: { code: "RAZORPAY_CREDENTIALS_UNAVAILABLE" } }));
  await page.goto("/razorpay");
  await page.getByRole("button", { name: "Sync Razorpay Test Mode" }).click();
  await expect(page.locator("main [role=alert]")).toContainText("credentials are unavailable on the server");
  await expect(page.getByText(/secret|Authorization|key_id/i)).toHaveCount(0);
  await expect(page.getByText("TEST MODE · READ ONLY")).toBeVisible();
});
