import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST(req: NextRequest) {
  const { password } = await req.json();

  const adminToken  = process.env.ADMIN_TOKEN;
  const viewerToken = process.env.VIEWER_TOKEN;

  let role: "admin" | "viewer" | null = null;

  if (password && password === adminToken)  role = "admin";
  else if (password && password === viewerToken) role = "viewer";

  if (!role) {
    return NextResponse.json({ error: "Credenciais inválidas" }, { status: 401 });
  }

  const cookieStore = await cookies();
  const maxAge = 60 * 60 * 24 * 7; // 7 days

  // httpOnly token (not accessible by JS)
  cookieStore.set("auth_token", password, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    maxAge,
    path: "/",
  });

  // role cookie (readable by client to show/hide Admin tab)
  cookieStore.set("role", role, {
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    maxAge,
    path: "/",
  });

  return NextResponse.json({ ok: true, role });
}
