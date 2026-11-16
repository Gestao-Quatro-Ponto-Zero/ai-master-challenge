import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, verifySessionToken } from "@/app/lib/session";

/**
 * The judge-login gate (Next 16 `proxy`, formerly `middleware`). Runs before every
 * route: no valid session → API requests get 401, page requests redirect to /login.
 * Optimistic check only — it reads the signed cookie, never the database (proxy runs before protected requests, incl. prefetches). Ownership is enforced in handlers/data layer.
 */

// Reachable without a session: the login screen + its actions, and the deploy health check.
function isPublicPath(pathname: string): boolean {
  return (
    pathname === "/login" ||
    pathname.startsWith("/login/") ||
    pathname === "/signup" ||
    pathname.startsWith("/signup/") ||
    pathname.startsWith("/api/auth") ||
    pathname === "/api/health"
  );
}

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const session = await verifySessionToken(req.cookies.get(SESSION_COOKIE)?.value);

  if (isPublicPath(pathname)) {
    // Already signed in and staring at the login page → send them into the app.
    if (session && pathname === "/login") {
      return NextResponse.redirect(new URL("/", req.nextUrl));
    }
    return NextResponse.next();
  }

  if (!session) {
    if (pathname.startsWith("/api/")) {
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }
    const url = new URL("/login", req.nextUrl);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Run on everything except Next internals + the favicon (so login assets load unauthenticated).
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
