"use client";

import { BookOpen, Bot, Hourglass, House, Kanban, Menu, Search, Settings, Users, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense, useEffect, useState, type ReactNode } from "react";
import { ThemeToggle } from "./theme-toggle";

const NAV = [
  { href: "/", label: "Hoje", icon: House, match: (p: string) => p === "/" || p.startsWith("/deal") },
  { href: "/pipeline", label: "Pipeline", icon: Kanban, match: (p: string) => p.startsWith("/pipeline") },
  { href: "/parados", label: "Parados", icon: Hourglass, match: (p: string) => p.startsWith("/parados") },
  { href: "/time", label: "Time", icon: Users, match: (p: string) => p.startsWith("/time") },
  { href: "/agente", label: "Agente Gestor", icon: Bot, match: (p: string) => p.startsWith("/agente") },
  { href: "/metodologia", label: "Metodologia", icon: BookOpen, match: (p: string) => p.startsWith("/metodologia") },
  { href: "/configuracoes", label: "Configurações", icon: Settings, match: (p: string) => p.startsWith("/configuracoes") },
] as const;

/**
 * Estrutura do sistema: menu lateral fixo no desktop, gaveta no celular e barra
 * superior com busca. O caminho atual só existe em tempo de requisição, então o
 * destaque do item ativo chega por Suspense sobre um menu estático.
 */
export function AppShell({ referenceLabel, stalledCount, datasetLabel, children }: { referenceLabel: string; stalledCount: number; datasetLabel: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const sidebar = (
    <Suspense fallback={<Sidebar referenceLabel={referenceLabel} stalledCount={stalledCount} datasetLabel={datasetLabel} onNavigate={() => setOpen(false)} />}>
      <CurrentSidebar referenceLabel={referenceLabel} stalledCount={stalledCount} datasetLabel={datasetLabel} onNavigate={() => setOpen(false)} />
    </Suspense>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
      <a href="#conteudo" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-surface focus:px-4 focus:py-2">
        Pular para o conteúdo
      </a>

      <aside className="sticky top-0 hidden h-screen border-r border-line bg-surface lg:block">{sidebar}</aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <button type="button" aria-label="Fechar menu" className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="relative h-full w-[280px] max-w-[85vw] border-r border-line bg-surface shadow-xl">
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Fechar menu"
              className="absolute top-4 right-3 grid size-11 place-items-center rounded-full text-secondary hover:bg-hover"
            >
              <X className="size-5" aria-hidden />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-line bg-ground/85 px-4 py-3 backdrop-blur sm:px-8">
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Abrir menu"
            className="grid size-11 shrink-0 place-items-center rounded-full text-secondary hover:bg-hover lg:hidden"
          >
            <Menu className="size-5" aria-hidden />
          </button>
          <form action="/pipeline" method="get" role="search" className="relative min-w-0 flex-1 lg:max-w-[720px]">
            <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-secondary" aria-hidden />
            <label htmlFor="busca" className="sr-only">
              Buscar deal, conta, vendedor ou produto
            </label>
            <input
              id="busca"
              name="q"
              type="search"
              placeholder="Buscar deal, conta, vendedor ou produto"
              className="h-11 w-full rounded-full border border-line bg-surface pr-4 pl-12 text-[15px] placeholder:text-secondary focus:border-moment focus:outline-none"
            />
          </form>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
          </div>
        </header>
        <main id="conteudo" className="mx-auto max-w-[1280px] px-4 py-8 sm:px-8 sm:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}

function CurrentSidebar(props: { referenceLabel: string; stalledCount: number; datasetLabel: string; onNavigate: () => void }) {
  return <Sidebar {...props} pathname={usePathname()} />;
}

function Sidebar({
  referenceLabel,
  stalledCount,
  datasetLabel,
  pathname,
  onNavigate,
}: {
  referenceLabel: string;
  stalledCount: number;
  datasetLabel: string;
  pathname?: string;
  onNavigate: () => void;
}) {
  return (
    <div className="flex h-full flex-col px-3 py-5">
      <Link href="/" onClick={onNavigate} className="flex items-center gap-3 rounded-xl px-3 py-1">
        <span aria-hidden className="grid size-9 place-items-center rounded-xl bg-primary font-mono text-[13px] font-bold text-surface">
          R
        </span>
        <span className="text-[20px] font-bold tracking-[-0.03em]">Régua</span>
      </Link>
      <p className="mt-1 px-3 text-[13px] text-secondary">Onde focar hoje</p>

      <nav aria-label="Principal" className="mt-8">
        <ul className="space-y-1">
          {NAV.map(({ href, label, icon: Icon, match }) => {
            const current = pathname !== undefined && match(pathname);
            return (
              <li key={href}>
                <Link
                  href={href}
                  onClick={onNavigate}
                  aria-current={current ? "page" : undefined}
                  className={`flex min-h-11 items-center gap-3 rounded-xl px-3 text-[15px] transition-colors ${
                    current ? "bg-selected font-semibold text-primary" : "text-secondary hover:bg-hover hover:text-primary"
                  }`}
                >
                  <Icon className="size-5 shrink-0" aria-hidden />
                  <span className="flex-1">{label}</span>
                  {href === "/parados" && (
                    <span className="rounded-full bg-stalled-soft px-2 py-0.5 font-mono text-[11px] font-semibold text-stalled tabular-nums">
                      {stalledCount.toLocaleString("pt-BR")}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-auto space-y-1 border-t border-line px-3 pt-4">
        <p className="field">Dados do CRM</p>
        <p className="text-[13px] text-secondary">Pipeline em {referenceLabel}</p>
        <p className="text-[13px] text-secondary">{datasetLabel}</p>
      </div>
    </div>
  );
}
