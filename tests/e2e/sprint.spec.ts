import { test, expect } from "../../apps/web/node_modules/@playwright/test";
import { runFixture, ledgerFixture } from "./fixtures/run";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok", environment: "test" } }),
  );
  await page.route("**/api/reconcile/demo", (route) =>
    route.fulfill({ json: runFixture() }),
  );
  await page.route("**/api/runs/run_test", (route) =>
    route.fulfill({ json: runFixture() }),
  );
  await page.route(
    "**/api/runs/run_test/artifacts/reconciled_ledger.csv",
    (route) => route.fulfill({ contentType: "text/csv", body: ledgerFixture }),
  );
});
async function start(
  page: import("../../apps/web/node_modules/@playwright/test").Page,
) {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Run Demo Reconciliation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Reconciliation complete", exact: true }),
  ).toBeVisible();
}

test("demo waits truthfully then displays backend tie-out and preserves run on navigation", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((r) => (release = r));
  await page.route("**/api/reconcile/demo", async (route) => {
    await gate;
    await route.fulfill({ json: runFixture() });
  });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Run Demo Reconciliation", exact: true })
    .click();
  await expect(
    page.getByText("Reconciling source evidence…", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Awaiting backend result", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Complete", { exact: true })).toHaveCount(0);
  release();
  await expect(
    page.getByRole("heading", { name: "Reconciliation complete", exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("tie-total")).toHaveText("₹1,000.00");
  await expect(page.getByTestId("tie-explained")).toHaveText("₹700.00");
  await expect(page.getByTestId("tie-residual")).toHaveText("₹300.00");
  await page.getByRole("link", { name: "Ledger", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Ledger explorer" }),
  ).toBeVisible();
  await expect(
    page.locator(".run-reference").filter({ hasText: "run_test" }).first(),
  ).toBeVisible();
});
test("cold health and unavailable backend are safe and retryable", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((r) => (release = r));
  await page.route("**/api/health", async (route) => {
    await gate;
    await route.fulfill({
      status: 503,
      json: { message: "secret stack trace" },
    });
  });
  await page.goto("/");
  await expect(
    page.getByText("Preparing reconciliation engine…", { exact: true }),
  ).toBeVisible();
  release();
  await expect(page.locator("main [role=alert]")).toContainText(
    "Reconciliation engine is unavailable",
  );
  await expect(page.getByText("secret stack trace")).toHaveCount(0);
});
test("invalid money conservation never appears as successful reconciliation", async ({
  page,
}) => {
  const run = runFixture();
  run.tie_out_summary.explained_bank_credit_paise = 80000;
  await page.route("**/api/reconcile/demo", (r) => r.fulfill({ json: run }));
  await page.goto("/");
  await page
    .getByRole("button", { name: "Run Demo Reconciliation", exact: true })
    .click();
  await expect(page.locator("main [role=alert]")).toContainText(
    "Integrity error",
  );
  await expect(
    page.getByRole("heading", { name: "Reconciliation complete", exact: true }),
  ).toHaveCount(0);
});
test("ledger filters source rows, opens keyboard evidence drawer, preserves totals", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("link", { name: "Ledger", exact: true }).click();
  await page.getByLabel("Source type").selectOption("settlement_bank");
  await expect(page.getByRole("button", { name: "Inspect pay_1" })).toHaveCount(
    0,
  );
  await page.getByRole("button", { name: "Inspect settlement_ref_7" }).click();
  await expect(page.getByRole("dialog")).toContainText("bank_ref_42");
  await expect(page.getByRole("dialog")).toContainText(
    'quoted "reference", verified',
  );
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByTestId("tie-total")).toHaveText("₹1,000.00");
});
test("approval uses server response and refreshes run, updates residual and audit", async ({
  page,
}) => {
  let current = runFixture();
  let refreshed = 0;
  await page.route("**/api/runs/run_test", (r) => {
    refreshed++;
    return r.fulfill({ json: current });
  });
  let release!: () => void;
  const gate = new Promise<void>((r) => (release = r));
  await page.route(
    "**/api/runs/run_test/exceptions/ex_review/approve",
    async (r) => {
      expect(r.request().method()).toBe("POST");
      await gate;
      current = runFixture();
      current.exceptions[0].resolution_status = "AUTO_RESOLVED";
      current.tie_out_summary.explained_bank_credit_paise = 90000;
      current.tie_out_summary.unexplained_residual_paise = 10000;
      current.audit_events.push({
        ...current.audit_events[0],
        event_id: "event_5",
        actor: "user",
        action: "HUMAN_APPROVAL",
        decision: "APPROVED",
        lifecycle_order: 5,
      });
      await r.fulfill({ json: current });
    },
  );
  await start(page);
  await page.getByRole("link", { name: "Exceptions", exact: true }).click();
  await page.getByRole("button", { name: "Inspect ex_review" }).click();
  await expect(page.getByRole("dialog")).toContainText("bank_ref_42");
  await page.getByRole("button", { name: "Approve resolution" }).click();
  await expect(
    page.getByRole("button", { name: "Approve resolution" }),
  ).toBeDisabled();
  await expect(page.getByTestId("tie-residual")).toHaveText("₹300.00");
  release();
  await expect(page.getByTestId("tie-residual")).toHaveText("₹100.00");
  expect(refreshed).toBeGreaterThan(0);
  await page.keyboard.press("Escape");
  await page.getByRole("link", { name: "Audit Trail", exact: true }).click();
  await expect(page.getByText("HUMAN_APPROVAL", { exact: true })).toBeVisible();
  await expect(page.getByText("user", { exact: true })).toBeVisible();
});
test("reject submits once and preserves authoritative amounts", async ({
  page,
}) => {
  const rejected = runFixture();
  rejected.exceptions[0].resolution_status = "REJECTED";
  await page.route("**/api/runs/run_test", (r) =>
    r.fulfill({ json: rejected }),
  );
  await page.route("**/api/runs/run_test/exceptions/ex_review/reject", (r) => {
    expect(r.request().method()).toBe("POST");
    const run = runFixture();
    run.exceptions[0].resolution_status = "REJECTED";
    return r.fulfill({ json: run });
  });
  await start(page);
  await page.getByRole("link", { name: "Exceptions", exact: true }).click();
  await page.getByRole("button", { name: "Inspect ex_review" }).click();
  await page.getByRole("button", { name: "Reject proposal" }).click();
  await expect(page.getByRole("status")).toContainText("Decision recorded");
  await expect(page.getByTestId("tie-residual")).toHaveText("₹300.00");
});
test("stale conflict is explicit and escalated cases have no approval action", async ({
  page,
}) => {
  await page.route("**/api/runs/run_test/exceptions/ex_review/approve", (r) =>
    r.fulfill({
      status: 409,
      json: { code: "APPROVAL_REJECTED", message: "stale", recoverable: true },
    }),
  );
  await start(page);
  await page.getByRole("link", { name: "Exceptions", exact: true }).click();
  await page.getByRole("button", { name: "Inspect ex_review" }).click();
  await page.getByRole("button", { name: "Approve resolution" }).click();
  await expect(page.locator("main [role=alert]")).toContainText("changed");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Inspect ex_abstain" }).click();
  await expect(page.getByRole("dialog")).toContainText("refused to guess");
  await expect(
    page.getByRole("button", { name: "Approve resolution" }),
  ).toHaveCount(0);
});
for (const width of [1440, 768, 320])
  test(`operational screens fit ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await start(page);
    for (const route of ["ledger", "exceptions", "audit"]) {
      await page.goto(`/${route}?run_id=run_test`);
      await expect(page.getByTestId("tie-total")).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
  });
test("no run and expired run have useful empty/error states", async ({
  page,
}) => {
  await page.goto("/ledger");
  await expect(page.getByText("No active run", { exact: true })).toBeVisible();
  await page.route("**/api/runs/expired", (r) =>
    r.fulfill({
      status: 404,
      json: { code: "RUN_NOT_FOUND", recoverable: true, message: "expired" },
    }),
  );
  await page.goto("/audit?run_id=expired");
  await expect(page.locator("main [role=alert]")).toContainText("expired");
});
test("artifact unavailable and malformed run are handled safely", async ({
  page,
}) => {
  await page.route(
    "**/api/runs/run_test/artifacts/reconciled_ledger.csv",
    (r) => r.fulfill({ status: 404, json: { code: "ARTIFACT_NOT_FOUND" } }),
  );
  await start(page);
  await page.getByRole("link", { name: "Ledger", exact: true }).click();
  await expect(page.locator("main [role=alert]")).toContainText("artifact");
  await page.route("**/api/runs/bad", (r) =>
    r.fulfill({ json: { run_id: "bad", status: "COMPLETED" } }),
  );
  await page.goto("/workspace?run_id=bad");
  await expect(page.locator("main [role=alert]")).toContainText(
    "invalid response",
  );
});
test("query-only run navigation and back never show another run totals", async ({
  page,
}) => {
  const other = runFixture();
  other.run_id = "run_other";
  other.audit_events = [];
  other.tie_out_summary = {
    total_bank_credit_paise: 50000,
    explained_bank_credit_paise: 40000,
    unexplained_residual_paise: 10000,
  };
  await page.route("**/api/runs/run_other", (r) => r.fulfill({ json: other }));
  await start(page);
  await page.evaluate(() =>
    window.history.pushState(null, "", "/workspace?run_id=run_other"),
  );
  await expect(page.getByTestId("tie-total")).toHaveText("₹500.00");
  await page.goBack();
  await expect(page.getByTestId("tie-total")).toHaveText("₹1,000.00");
});
test("conflict refresh re-enables decisions against refreshed evidence", async ({
  page,
}) => {
  await page.route("**/api/runs/run_test/exceptions/ex_review/approve", (r) =>
    r.fulfill({ status: 409, json: { code: "APPROVAL_REJECTED" } }),
  );
  await start(page);
  await page.getByRole("link", { name: "Exceptions", exact: true }).click();
  await page.getByRole("button", { name: "Inspect ex_review" }).click();
  await page.getByRole("button", { name: "Approve resolution" }).click();
  await expect(
    page.getByRole("button", { name: "Reject proposal" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Refresh current evidence" }).click();
  await expect(
    page.getByRole("button", { name: "Reject proposal" }),
  ).toBeEnabled();
});
