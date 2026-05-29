import { NextRequest, NextResponse } from "next/server";

const COOKIE_MAX_AGE = 60 * 60 * 8;

function makeRedirect(request: NextRequest, fallback: string) {
  const target = request.nextUrl.searchParams.get("next") || fallback;
  return NextResponse.redirect(new URL(target, request.url));
}

export async function GET(request: NextRequest) {
  const role = request.nextUrl.searchParams.get("role");
  const logout = request.nextUrl.searchParams.get("logout");

  if (logout === "1") {
    const response = makeRedirect(request, "/login");
    response.cookies.delete("demo-role");
    response.cookies.delete("demo-user-id");
    response.cookies.delete("demo-email");
    return response;
  }

  if (role !== "admin" && role !== "customer") {
    return NextResponse.json({ error: "role inválido" }, { status: 400 });
  }

  const response = makeRedirect(request, role === "admin" ? "/admin" : "/customer/new");

  response.cookies.set("demo-role", role, {
    httpOnly: true,
    sameSite: "lax",
    maxAge: COOKIE_MAX_AGE,
    path: "/",
  });

  response.cookies.set("demo-user-id", role === "admin" ? "demo-admin-001" : "demo-customer-001", {
    httpOnly: true,
    sameSite: "lax",
    maxAge: COOKIE_MAX_AGE,
    path: "/",
  });

  response.cookies.set(
    "demo-email",
    role === "admin" ? "admin@g4.local" : "customer@g4.local",
    {
      httpOnly: true,
      sameSite: "lax",
      maxAge: COOKIE_MAX_AGE,
      path: "/",
    }
  );

  return response;
}
