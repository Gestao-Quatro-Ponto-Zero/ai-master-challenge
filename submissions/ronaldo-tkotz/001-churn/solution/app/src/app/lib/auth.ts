import { cookies } from "next/headers";
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
  return user;
}

export function authErrorResponse(error: unknown): Response | null {
  if (error instanceof UnauthorizedError) return Response.json({ error: "unauthorized" }, { status: 401 });
  return null;
}
