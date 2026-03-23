import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// ─── In-memory rate limiter (resets on cold start) ──────────────────
// For production at scale, use Redis/Upstash. For a demo prototype this is fine.

const WINDOW_MS = 60_000; // 1 minute
const MAX_WRITES_PER_WINDOW = 15; // 15 POST/PUT/DELETE per minute per IP
const MAX_READS_PER_WINDOW = 60; // 60 GET per minute per IP (polling, dashboard)
const DAILY_OPENAI_CAP = 200; // ~200 OpenAI calls/day across all users

interface RateEntry {
  reads: number;
  writes: number;
  resetAt: number;
}

const ipMap = new Map<string, RateEntry>();
let dailyOpenAICalls = 0;
let dailyResetAt = Date.now() + 86_400_000;

function getClientIP(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Only rate-limit prototype API routes (the ones that call OpenAI)
  if (!pathname.startsWith("/api/prototype/")) {
    return NextResponse.next();
  }

  // Bypass rate limiter for internal server-to-server calls (e.g., classify self-call)
  if (req.headers.get("x-internal-call") === "optiflow") {
    return NextResponse.next();
  }

  const ip = getClientIP(req);
  const now = Date.now();

  // ── Per-IP rate limit (separate buckets for reads vs writes) ──
  const isWrite = req.method !== "GET" && req.method !== "HEAD";
  let entry = ipMap.get(ip);
  if (!entry || now > entry.resetAt) {
    entry = { reads: 0, writes: 0, resetAt: now + WINDOW_MS };
    ipMap.set(ip, entry);
  }

  if (isWrite) {
    entry.writes++;
    if (entry.writes > MAX_WRITES_PER_WINDOW) {
      return NextResponse.json(
        { error: "Limite de requisições excedido. Tente novamente em 1 minuto." },
        {
          status: 429,
          headers: {
            "Retry-After": "60",
            "X-RateLimit-Limit": String(MAX_WRITES_PER_WINDOW),
            "X-RateLimit-Remaining": "0",
          },
        }
      );
    }
  } else {
    entry.reads++;
    if (entry.reads > MAX_READS_PER_WINDOW) {
      return NextResponse.json(
        { error: "Limite de requisições excedido. Tente novamente em 1 minuto." },
        {
          status: 429,
          headers: {
            "Retry-After": "60",
            "X-RateLimit-Limit": String(MAX_READS_PER_WINDOW),
            "X-RateLimit-Remaining": "0",
          },
        }
      );
    }
  }

  const currentLimit = isWrite ? MAX_WRITES_PER_WINDOW : MAX_READS_PER_WINDOW;
  const currentCount = isWrite ? entry.writes : entry.reads;

  // ── Daily OpenAI cap (only for message endpoints that trigger LLM) ─
  const isLLMRoute =
    pathname.includes("/messages") || pathname.includes("/classify");

  if (isLLMRoute) {
    if (now > dailyResetAt) {
      dailyOpenAICalls = 0;
      dailyResetAt = now + 86_400_000;
    }
    dailyOpenAICalls++;

    if (dailyOpenAICalls > DAILY_OPENAI_CAP) {
      return NextResponse.json(
        {
          error:
            "Limite diário de classificações atingido. Este protótipo tem um cap de uso para proteger a API key. Tente novamente amanhã.",
        },
        { status: 429, headers: { "Retry-After": "3600" } }
      );
    }
  }

  // ── Cleanup stale entries periodically ─────────────────────────
  if (ipMap.size > 1000) {
    for (const [key, val] of ipMap) {
      if (now > val.resetAt) ipMap.delete(key);
    }
  }

  const response = NextResponse.next();
  response.headers.set("X-RateLimit-Limit", String(currentLimit));
  response.headers.set(
    "X-RateLimit-Remaining",
    String(Math.max(0, currentLimit - currentCount))
  );
  return response;
}

export const config = {
  matcher: "/api/prototype/:path*",
};
