import axios from "axios";

export class ApiError extends Error {
  readonly status: number | null;
  constructor(message: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function describeDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI/Pydantic validation errors: [{ loc, msg, type }]
    const msgs = detail
      .map((d) => {
        if (d && typeof d === "object" && "msg" in d) {
          const loc = Array.isArray((d as { loc?: unknown }).loc)
            ? ((d as { loc: unknown[] }).loc.filter((p) => p !== "body").join("."))
            : "";
          return loc ? `${loc}: ${String((d as { msg: unknown }).msg)}` : String((d as { msg: unknown }).msg);
        }
        return null;
      })
      .filter(Boolean);
    return msgs.length ? msgs.join("; ") : null;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    // GitHub errors: { message, retry_after?, rate_limit_reset_at? }
    const d = detail as { message: unknown; retry_after?: unknown };
    const base = String(d.message);
    return d.retry_after ? `${base} Retry after ${String(d.retry_after)}s.` : base;
  }
  return null;
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (axios.isAxiosError(error)) {
    if (error.response) {
      const { status, data } = error.response;
      const detail = describeDetail((data as { detail?: unknown } | undefined)?.detail);
      const fallback: Record<number, string> = {
        401: "Authentication failed. Check the dashboard proxy API key.",
        403: "This action is not permitted.",
        404: "Not found.",
        409: "This item has already been reviewed.",
        502: "Unable to reach the DocuMind backend.",
        503: "The backend or proxy is not configured.",
        504: "The backend took too long to respond.",
      };
      return new ApiError(detail ?? fallback[status] ?? `Request failed (HTTP ${status}).`, status);
    }
    if (error.code === "ECONNABORTED") {
      return new ApiError("The request timed out.", null);
    }
    return new ApiError("Network error. Is the dashboard server running?", null);
  }

  return new ApiError(error instanceof Error ? error.message : "Unexpected error.", null);
}

export function errorMessage(error: unknown): string {
  return toApiError(error).message;
}
