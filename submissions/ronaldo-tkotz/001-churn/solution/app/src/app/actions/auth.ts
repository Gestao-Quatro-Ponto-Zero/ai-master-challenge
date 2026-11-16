"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createSessionToken, SESSION_COOKIE } from "@/app/lib/session";
import { authenticateUser, createUser, seedJudgeUser } from "@/engine/appdb";

export interface LoginState {
  error?: string;
  mode?: "login" | "signup";
}

async function setSession(user: { id: string; email: string }): Promise<void> {
  const token = await createSessionToken(user);
  const store = await cookies();
  store.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 7 * 24 * 60 * 60,
  });
}

export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  await seedJudgeUser();
  const email = String(formData.get("email") ?? formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const user = await authenticateUser(email, password);
  if (!user) return { mode: "login", error: "Incorrect email or password." };
  await setSession({ id: user.id, email: user.email });
  redirect("/");
}

export async function signup(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  try {
    const user = await createUser(email, password);
    await setSession({ id: user.id, email: user.email });
  } catch (e) {
    const message = e instanceof Error && /valid email|at least 8/.test(e.message)
      ? e.message
      : "We couldn't create that account. Try signing in or use another email.";
    return { mode: "signup", error: message };
  }
  redirect("/");
}

export async function logout(): Promise<void> {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
  redirect("/login");
}
