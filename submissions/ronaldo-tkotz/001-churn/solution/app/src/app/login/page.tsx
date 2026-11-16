import type { Metadata } from "next";
import { LoginForm } from "@/app/components/LoginForm";

export const metadata: Metadata = {
  title: "Sign in — Veta",
};

/** The judge-login gate. On-brand with the app (dark, ore-vein gold), single credential. */
export default function LoginPage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-md bg-accent-soft">
            <span className="h-3 w-3 rotate-45 bg-accent" />
          </span>
          <div className="leading-tight">
            <div className="text-[16px] font-semibold tracking-tight text-foreground">Veta</div>
            <div className="text-[11px] text-faint">insight engine</div>
          </div>
        </div>

        <div className="rounded-xl border border-edge bg-panel p-6">
          <h1 className="text-[18px] font-semibold tracking-tight text-foreground">Sign in</h1>
          <p className="mt-1 mb-5 text-[12.5px] leading-snug text-muted">
            Diagnóstico de churn da RavenStack, com cada número rastreável até o SQL. Entre com o usuário informado.
          </p>
          <LoginForm />
        </div>

        <p className="mt-4 text-center text-[11px] text-faint">Every answer inside cites the exact SQL it ran.</p>
      </div>
    </main>
  );
}
