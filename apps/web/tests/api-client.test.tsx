import assert from "node:assert/strict";
import test from "node:test";

import { requestForm, requestJson } from "../lib/api/client";
import { ApiError } from "../lib/api/errors";

test("form and JSON requests preserve nested backend error codes", async () => {
  const originalFetch = globalThis.fetch;
  const requests: RequestInit[] = [];
  globalThis.fetch = (async (_input, init) => {
    requests.push(init ?? {});
    return (
    new Response(JSON.stringify({ detail: { code: "IMPORT_VALIDATION_FAILED" } }), {
      status: 422,
      headers: { "content-type": "application/json" },
    })
    );
  }) as typeof fetch;

  try {
    await assert.rejects(
      () => requestForm("/import/inspect", new FormData()),
      (error: unknown) => error instanceof ApiError && error.code === "IMPORT_VALIDATION_FAILED",
    );
    await assert.rejects(
      () => requestJson("/import/example/validate", {}),
      (error: unknown) => error instanceof ApiError && error.code === "IMPORT_VALIDATION_FAILED",
    );
    assert.ok(requests.every((request) => request.signal instanceof AbortSignal));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
