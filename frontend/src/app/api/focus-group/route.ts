import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/focus-group
 *
 * Proxy to the Python LangGraph backend.
 * In dev mode with mock data, this returns mock responses.
 * In production, it forwards to the backend service.
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { message, filters, step } = body;

  // TODO: In production, forward to the Python backend container
  // const backendUrl = process.env.BACKEND_URL || "http://notebook:8000";
  // const res = await fetch(`${backendUrl}/api/focus-group`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ message, filters, step }),
  // });
  // return NextResponse.json(await res.json());

  // For now, return a signal that the frontend should use mock data
  return NextResponse.json({
    status: "mock",
    message: "Backend not connected yet. Using client-side mock data.",
  });
}
