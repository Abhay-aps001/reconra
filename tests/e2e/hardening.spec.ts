import { expect, test } from "../../apps/web/node_modules/@playwright/test";

const routes = ["/", "/workspace", "/ledger", "/exceptions", "/audit", "/runs", "/import", "/razorpay", "/methodology"];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok", environment: "test" } }),
  );
});

for (const width of [1440, 1024, 768, 390, 320]) {
  test(`all routes avoid page overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    for (const route of routes) {
      await page.goto(route);
      await expect(page.getByRole("main")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    }
  });
}
