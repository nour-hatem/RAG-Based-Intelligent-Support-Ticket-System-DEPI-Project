import { NextRequest, NextResponse } from "next/server";

// Server-only env vars — NOT prefixed with NEXT_PUBLIC_, so they never
// leak into the client bundle.
const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
const BACKEND_API_KEY = process.env.BACKEND_API_KEY ?? "";

export async function POST(req: NextRequest) {
  const body = await req.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_API_URL}/api/v1/tickets/respond`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": BACKEND_API_KEY,
      },
      body,
      // Prevents Next from caching a POST response
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { error: "bad_gateway", detail: "Backend is unreachable." },
      { status: 502 }
    );
  }

  const data = await upstream.text();
  return new NextResponse(data, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}