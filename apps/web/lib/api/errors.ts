export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function safeError(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The request could not be completed. Please try again.";
}
export function responseError(status: number, code: string): ApiError {
  if (status === 409)
    return new ApiError(
      code,
      "This exception changed or its proposal is no longer valid. Refresh the run and review the current evidence before deciding again.",
      status,
    );
  if (code === "RUN_NOT_FOUND")
    return new ApiError(
      code,
      "This run is unavailable or expired. Start a new demo reconciliation.",
      status,
    );
  if (code === "ARTIFACT_NOT_FOUND")
    return new ApiError(
      code,
      "The requested artifact is not available for this run.",
      status,
    );
  if (status === 404)
    return new ApiError(
      code,
      "The requested record is not available for this run.",
      status,
    );
  return new ApiError(
    code,
    "Reconciliation engine is unavailable. Please retry shortly.",
    status,
  );
}
