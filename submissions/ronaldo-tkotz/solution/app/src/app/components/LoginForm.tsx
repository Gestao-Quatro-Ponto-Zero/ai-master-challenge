"use client";

import { useState } from "react";
import { useActionState } from "react";
import { login, signup, type LoginState } from "@/app/actions/auth";

export function LoginForm() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [loginState, loginAction, loginPending] = useActionState<LoginState, FormData>(login, { mode: "login" });
  const [signupState, signupAction, signupPending] = useActionState<LoginState, FormData>(signup, { mode: "signup" });
  const pending = mode === "login" ? loginPending : signupPending;
  const state = mode === "login" ? loginState : signupState;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 rounded-md border border-edge bg-background/40 p-1 text-[12px]">
        <button
          type="button"
          onClick={() => setMode("login")}
          className={`rounded px-3 py-1.5 font-medium transition ${mode === "login" ? "bg-accent text-[#1a1406]" : "text-muted hover:text-foreground"}`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => setMode("signup")}
          className={`rounded px-3 py-1.5 font-medium transition ${mode === "signup" ? "bg-accent text-[#1a1406]" : "text-muted hover:text-foreground"}`}
        >
          Sign up
        </button>
      </div>

      <form action={mode === "login" ? loginAction : signupAction} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1.5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-faint">Email</span>
          <input
            name="email"
            type="email"
            autoComplete="email"
            autoFocus
            className="rounded-md border border-edge bg-background/60 px-3 py-2 text-[14px] text-foreground outline-none placeholder:text-faint focus:border-edge-strong"
            placeholder="avaliador@ravenstack.app"
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-faint">Password</span>
          <input
            name="password"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            className="rounded-md border border-edge bg-background/60 px-3 py-2 text-[14px] text-foreground outline-none placeholder:text-faint focus:border-edge-strong"
            placeholder="••••••••"
          />
        </label>

        {state?.error ? (
          <p role="alert" className="text-[12px] text-red-400">
            {state.error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={pending}
          className="mt-1 rounded-md bg-accent px-3 py-2 text-[13px] font-semibold text-[#1a1406] transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {pending ? (mode === "login" ? "Signing in…" : "Creating account…") : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
    </div>
  );
}
