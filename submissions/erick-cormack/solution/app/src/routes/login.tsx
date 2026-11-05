import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { supabase } from "@/integrations/supabase/client";
import { ACCESS_EXPIRES_LABEL, isAccessExpired } from "@/lib/access";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Entrar — Lead Scorer" },
      { name: "description", content: "Acesso ao Lead Scorer, ferramenta de priorização de pipeline de vendas." },
      { property: "og:title", content: "Entrar — Lead Scorer" },
      { property: "og:description", content: "Acesso ao Lead Scorer, ferramenta de priorização de pipeline de vendas." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) {
      setLoading(false);
      setError("E-mail ou senha inválidos.");
      return;
    }
    if (isAccessExpired()) {
      await supabase.auth.signOut();
      setLoading(false);
      setError(`Seu acesso expirou em ${ACCESS_EXPIRES_LABEL}. Fale com a equipe G4 para renovar.`);
      return;
    }
    navigate({ to: "/", replace: true });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-sidebar px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display text-4xl italic text-sidebar-primary">Lead Scorer</span>
          <p className="mt-2 text-sm text-sidebar-foreground">Onde focar seu pipeline nesta semana</p>
        </div>
        <form onSubmit={handleSubmit} className="rounded-lg border border-sidebar-border bg-card p-6 shadow-lg">
          <label className="block text-sm font-medium text-foreground" htmlFor="email">
            E-mail
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-ring"
          />
          <label className="mt-4 block text-sm font-medium text-foreground" htmlFor="password">
            Senha
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-ring"
          />
          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="mt-5 w-full rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
        <p className="mt-4 text-center text-xs text-sidebar-foreground">
          Acesso de demonstração válido até {ACCESS_EXPIRES_LABEL}.
        </p>
      </div>
    </div>
  );
}
