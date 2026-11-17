import { cookies } from "next/headers";
import { after } from "next/server";
import { prepararEstado, persistirEstado } from "@/engine/estado";
import { SESSION_COOKIE, verifySessionToken } from "@/app/lib/session";

export interface CurrentUser {
  id: string;
  email: string;
}

export class UnauthorizedError extends Error {
  constructor() {
    super("Unauthorized");
    this.name = "UnauthorizedError";
  }
}

export async function currentUser(): Promise<CurrentUser | null> {
  const store = await cookies();
  const session = await verifySessionToken(store.get(SESSION_COOKIE)?.value);
  return session ? { id: session.uid, email: session.email } : null;
}

export async function requireUser(): Promise<CurrentUser> {
  const user = await currentUser();
  if (!user) throw new UnauthorizedError();
  // Deploy (D46.4): load the newest app state first, upload it after the response if it changed.
  await prepararEstado();
  after(persistirEstado);
  return user;
}

export function authErrorResponse(error: unknown): Response | null {
  if (error instanceof UnauthorizedError) return Response.json({ error: "unauthorized" }, { status: 401 });
  return null;
}
