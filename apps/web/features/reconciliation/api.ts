import { request } from "../../lib/api/client";
import { ApiError } from "../../lib/api/errors";
import { object, parseRun } from "./types";
async function runRequest(path: string, method = "GET", expectedId?: string) {
  const run = parseRun(await request(path, method));
  if (expectedId && run.run_id !== expectedId)
    throw new ApiError(
      "INVALID_RESPONSE",
      "The engine returned an invalid response for this run.",
    );
  return run;
}
export const api = {
  async health() {
    const h = object(await request("/health"));
    if (h.status !== "ok" || typeof h.environment !== "string")
      throw new ApiError(
        "API_UNAVAILABLE",
        "Reconciliation engine is unavailable. Please retry shortly.",
      );
  },
  demo: () => runRequest("/reconcile/demo", "POST"),
  run: (id: string) => runRequest(`/runs/${encodeURIComponent(id)}`, "GET", id),
  decide: (id: string, exception: string, action: "approve" | "reject") =>
    runRequest(
      `/runs/${encodeURIComponent(id)}/exceptions/${encodeURIComponent(exception)}/${action}`,
      "POST",
      id,
    ),
  artifact: (
    id: string,
    name:
      | "reconciled_ledger.csv"
      | "audit_log.json"
      | "exception_worklist.csv"
      | "reconciliation_summary.json",
  ) =>
    request(
      `/runs/${encodeURIComponent(id)}/artifacts/${name}`,
      "GET",
      name.endsWith(".csv"),
    ),
};
