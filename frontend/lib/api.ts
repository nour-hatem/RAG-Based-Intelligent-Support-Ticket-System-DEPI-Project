// ---------------------------------------------------------------------------
// API client
//
// Architecture note: the browser never calls the FastAPI backend directly.
// All requests go through the Next.js route handler at /api/tickets/respond,
// which injects the server-side BACKEND_API_KEY before forwarding to FastAPI.
// This keeps the API key out of the client bundle entirely.
//
// The only thing the client needs in its env is NEXT_PUBLIC_API_URL — the
// URL of the *Next.js* app itself (defaults to the same origin, i.e. "").
// ---------------------------------------------------------------------------

import type { TicketRequest, TicketResponse, ApiErrorResponse } from "./types";

// When NEXT_PUBLIC_API_URL is not set, requests go to the same origin.
// In production this is correct; in development Next.js dev server handles both.
const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Internal helper — parse backend error responses consistently
// ---------------------------------------------------------------------------

async function parseErrorResponse(res: Response): Promise<ApiError> {
  let body: ApiErrorResponse | null = null;

  try {
    body = (await res.json()) as ApiErrorResponse;
  } catch {
    // Body wasn't valid JSON — fall through to generic message
  }

  // 422 Unprocessable Entity from Pydantic: detail is an array
  if (res.status === 422) {
    const detail =
      Array.isArray(body?.detail)
        ? "Validation error: " + (body.detail as Array<{ msg?: string }>).map((e) => e.msg).join(", ")
        : "Request validation failed.";
    return new ApiError(detail, 422, "validation_error");
  }

  // 401
  if (res.status === 401) {
    return new ApiError("Unauthorized — invalid or missing API key.", 401, "unauthorized");
  }

  // 502 — backend unreachable or LLM parse failure
  if (res.status === 502) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : "Backend is unavailable. Please try again later.";
    return new ApiError(detail, 502, body?.error ?? "bad_gateway");
  }

  // Generic fallback
  const detail =
    typeof body?.detail === "string"
      ? body.detail
      : `Server error (${res.status}).`;
  return new ApiError(detail, res.status, body?.error);
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

/**
 * GET /health — public, no auth required.
 *
 * Returns true when the backend is reachable and responding 200.
 * Never throws — callers can use the boolean directly.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * POST /api/tickets/respond — proxied through the Next.js route handler.
 *
 * The Next.js handler forwards to FastAPI at /api/v1/tickets/respond and
 * injects the X-API-Key server-side. The client never sees or sends the key.
 *
 * @throws {ApiError} on any non-200 response, with a user-facing message.
 */
export async function submitTicket(payload: TicketRequest): Promise<TicketResponse> {
  let res: Response;

  try {
    res = await fetch(`${BASE}/api/tickets/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
  } catch {
    // Network-level failure (no connection, DNS, etc.)
    throw new ApiError(
      "Could not reach the server. Check your connection and try again.",
      0,
      "network_error",
    );
  }

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json() as Promise<TicketResponse>;
}
