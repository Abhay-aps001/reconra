import { ApiError, responseError } from "./errors";
// NEXT_PUBLIC_API_BASE_URL is consumed by next.config.ts. Same-origin rewrites
// avoid requiring cross-origin access from the backend and work in production.
function errorCode(body: unknown): string {
  const value = body as { code?: unknown; detail?: { code?: unknown } };
  return typeof value?.code === "string"
    ? value.code
    : typeof value?.detail?.code === "string"
      ? value.detail.code
      : "API_UNAVAILABLE";
}

function timeoutFor(path: string): number {
  return path === "/health" ? 15000 : 90000;
}

export async function request(
  path: string,
  method = "GET",
  text = false,
): Promise<unknown> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutFor(path));
  try {
    const response = await fetch(`/api${path}`, {
      method,
      signal: controller.signal,
      cache: "no-store",
      headers: { Accept: text ? "text/csv" : "application/json" },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw responseError(response.status, errorCode(body));
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

async function checkedFetch(path: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutFor(path));
  try {
    const response = await fetch(`/api${path}`, {
      ...init,
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw responseError(response.status, errorCode(body));
    }
    return response;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("API_UNAVAILABLE", "Reconciliation engine is unavailable. Please retry shortly.");
  } finally {
    clearTimeout(timeout);
  }
}

export async function requestForm(path: string, form: FormData): Promise<unknown> {
  const response = await checkedFetch(path, { method: "POST", body: form, headers: { Accept: "application/json" } });
  try { return await response.json(); } catch { throw new ApiError("INVALID_RESPONSE", "The engine returned an invalid response. Please retry."); }
}

export async function requestJson(path: string, body?: unknown): Promise<unknown> {
  const response = await checkedFetch(path, { method: "POST", headers: { Accept: "application/json", "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  try { return await response.json(); } catch { throw new ApiError("INVALID_RESPONSE", "The engine returned an invalid response. Please retry."); }
}

export async function requestBlob(path: string): Promise<Blob> {
  return (await checkedFetch(path, { headers: { Accept: "application/octet-stream" } })).blob();
}
