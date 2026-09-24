import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "nirman-ai-frontend",
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || "production",
    },
    { status: 200 }
  );
}
