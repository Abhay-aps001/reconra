import assert from "node:assert/strict";
import test from "node:test";
import { resolveBackendBaseUrl } from "../next.config";

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
