import { ApiError, responseError } from "./errors";
// NEXT_PUBLIC_API_BASE_URL is consumed by next.config.ts. Same-origin rewrites
// avoid requiring cross-origin access from the backend and work in production.
export async function request(
  path: string,
  method = "GET",
  text = false,
): Promise<unknown> {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    path === "/health" ? 15000 : 90000,
  );
  try {
    const response = await fetch(`/api${path}`, {
      method,
      signal: controller.signal,
      cache: "no-store",
      headers: { Accept: text ? "text/csv" : "application/json" },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw responseError(
        response.status,
        typeof body?.code === "string"
          ? body.code
          : typeof body?.detail?.code === "string"
            ? body.detail.code
            : "API_UNAVAILABLE",
      );
    }
    if (text) return await response.text();
    try {
      return await response.json();
    } catch {
      throw new ApiError(
        "INVALID_RESPONSE",
        "The engine returned an invalid response. Please refresh the run.",
      );
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "API_UNAVAILABLE",
      "Reconciliation engine is unavailable. Please retry shortly.",
    );
  } finally {
    clearTimeout(timeout);
  }
}
