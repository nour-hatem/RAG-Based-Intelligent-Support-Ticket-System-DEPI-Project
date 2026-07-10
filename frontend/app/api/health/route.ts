import { NextResponse } from "next/server";

const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const upstream = await fetch(`${BACKEND_API_URL}/health`, { cache: "no-store" });
    if (upstream.ok) {
      return new NextResponse("OK", { status: 200 });
    }
  } catch {}
  return new NextResponse("Error", { status: 502 });
}
