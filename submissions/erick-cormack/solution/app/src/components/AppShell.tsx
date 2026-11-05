import { Link, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { BarChart3, Home, ListChecks, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { supabase } from "@/integrations/supabase/client";
import { ACCESS_EXPIRES_LABEL } from "@/lib/access";

const nav = [
  { to: "/", label: "Início", icon: Home },
  { to: "/pipeline", label: "Meu pipeline", icon: ListChecks },
  { to: "/gestor", label: "Visão do gestor", icon: BarChart3 },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function handleSignOut() {
    await queryClient.cancelQueries();
    queryClient.clear();
    await supabase.auth.signOut();
    navigate({ to: "/login", replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col bg-background md:flex-row">
      <aside className="flex shrink-0 flex-col bg-sidebar text-sidebar-foreground md:w-60">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="h-2.5 w-2.5 rounded-full bg-sidebar-primary" />
          <span className="font-display text-2xl italic text-sidebar-accent-foreground">Lead Scorer</span>
        </div>
        <nav className="flex gap-1 px-3 pb-3 md:flex-col">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              activeOptions={{ exact: true }}
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              activeProps={{ className: "bg-sidebar-accent text-sidebar-accent-foreground font-medium" }}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto flex items-center justify-between gap-2 px-5 py-4">
          <span className="text-xs text-sidebar-foreground">Acesso até {ACCESS_EXPIRES_LABEL}</span>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sair
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="border-b border-border px-8 py-10">
      <h1 className="font-display text-5xl text-foreground">{title}</h1>
      <p className="mt-2 text-muted-foreground">{subtitle}</p>
    </header>
  );
}
