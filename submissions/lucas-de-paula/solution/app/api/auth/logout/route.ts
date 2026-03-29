import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete("auth_token");
  cookieStore.delete("role");
  return NextResponse.json({ ok: true });
}
