import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/e2e",
  testMatch: ["entry.spec.ts", "sprint.spec.ts", "completion.spec.ts"],
  workers: 4,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "pnpm exec next dev --hostname 127.0.0.1 --port 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
