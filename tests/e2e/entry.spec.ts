// Resolve Playwright from its owning workspace package, without a second root dependency.
import { expect, test } from "../../apps/web/node_modules/@playwright/test";

test.beforeEach(async ({page}) => { await page.route("**/api/health", route => route.fulfill({json:{status:"ok",environment:"test"}})); });
for (const width of [1440, 768, 320]) {
  test(`entry fits ${width}px with usable actions and responsive navigation`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Every rupee should have a trail." })).toBeVisible();
    for (const name of ["Run Demo Reconciliation", "Import Data", "Sync Razorpay Test Mode"]) {
      const action = name === "Run Demo Reconciliation" ? page.getByRole("button", { name, exact: true }) : page.getByRole("link", { name, exact: true });
      await expect(action).toBeVisible();
      await expect(action).toBeEnabled();
      const box = await action.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

    const menu = page.getByRole("button", { name: "Navigation", exact: true });
    if (width < 900) {
      await expect(menu).toHaveAttribute("aria-expanded", "false");
      await expect(page.getByRole("navigation", { name: "Primary" })).toBeHidden();
      await menu.focus();
      await page.keyboard.press("Enter");
      await expect(menu).toHaveAttribute("aria-expanded", "true");
      await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await menu.press("Enter");
      await expect(menu).toHaveAttribute("aria-expanded", "false");
    } else {
      await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
    }
  });
}

test("keyboard skip link moves focus to content with a visible focus indicator", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Skip to content" });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  expect(await skip.evaluate(el => getComputedStyle(el).outlineStyle)).not.toBe("none");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
});

test("reduced motion keeps the full money trail visible and static", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const artwork = page.locator(".rupee-flow svg");
  await expect(artwork).toBeVisible();
  await artwork.hover();
  expect(await artwork.evaluate(el => {
    const nodes = [el, ...el.querySelectorAll("*")];
    return nodes.every(node => {
      const style = getComputedStyle(node);
      return style.animationName === "none" && style.transitionDuration === "0s";
    });
  })).toBe(true);
  await expect(page.getByText("Illustrative money trail", { exact: false })).toBeVisible();
});

test("entry loads its local decorative currency asset without application errors or workflow requests", async ({ page }) => {
  const errors: string[] = [];
  const imageRequests: string[] = [];
  const workflowRequests: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("request", request => {
    if (request.resourceType() === "image" && new URL(request.url()).pathname !== "/icon.svg") {
      imageRequests.push(request.url());
    }
    if (request.url().includes("/api/") && !request.url().endsWith("/api/health")) workflowRequests.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(errors).toEqual([]);
  await expect.poll(() => imageRequests.length).toBeGreaterThan(0);
  expect(imageRequests.every(url => new URL(url).origin === new URL(page.url()).origin && new URL(url).pathname === "/assets/rupee-500-reference.webp")).toBe(true);
  const asset = await page.request.get("/assets/rupee-500-reference.webp");
  expect(asset.status()).toBe(200);
  expect(asset.headers()["content-type"]).toContain("image/webp");
  expect(workflowRequests).toEqual([]);
});

test("shell provides its own browser icon", async ({ request }) => {
  const response = await request.get("/icon.svg");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("image/svg+xml");
});
