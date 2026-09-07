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
  if (code.startsWith("RAZORPAY_"))
    return new ApiError(
      code,
      code === "RAZORPAY_TEST_MODE_REQUIRED"
        ? "Razorpay sync is available only in Test Mode."
        : code === "RAZORPAY_CREDENTIALS_UNAVAILABLE"
          ? "Razorpay Test Mode credentials are unavailable on the server."
          : "Razorpay Test Mode sync is unavailable. Demo and import remain available.",
      status,
    );
  if (code.startsWith("IMPORT_") || ["INVALID_MAPPING", "INVALID_MAPPING_VALUE", "REQUIRED_FIELD_MISSING", "AMBIGUOUS_SOURCE_ROLE", "UNSUPPORTED_FILE_TYPE"].includes(code))
    return new ApiError(code, `Import validation failed: ${code.replaceAll("_", " ").toLowerCase()}.`, status);
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
