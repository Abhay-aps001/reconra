import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import nextConfig, { resolveBackendBaseUrl } from "../next.config";

test("uses the local API only when development has no configured backend", () => {
  assert.equal(resolveBackendBaseUrl(undefined, "development"), "http://127.0.0.1:8000");
  assert.equal(resolveBackendBaseUrl(undefined, "production"), undefined);
});

test("configured backend URL takes precedence and strips its trailing slash", () => {
  assert.equal(
    resolveBackendBaseUrl("https://api.reconra.example/", "production"),
    "https://api.reconra.example",
  );
});

test("uses the current worktree as the tracing root when parent repositories have lockfiles", () => {
  assert.equal(nextConfig.outputFileTracingRoot, path.join(__dirname, "../../.."));
});
