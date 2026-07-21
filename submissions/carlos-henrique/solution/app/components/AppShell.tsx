"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { BarChart3, Beaker, BookOpen, Database, GitBranch, Menu, Network, ShieldCheck, Sparkles, X } from "lucide-react";

const navigation = [
  { href: "/", label: "Overview", icon: BarChart3 },
  { href: "/quality", label: "Data & Quality", icon: Database },
  { href: "/journeys", label: "Journey Explorer", icon: GitBranch },
  { href: "/graph", label: "JourneyGraph", icon: Network },
  { href: "/watchlist", label: "Watchlist", icon: BookOpen },
  { href: "/experiments", label: "Experiment Lab", icon: Beaker },
  { href: "/governance", label: "Governance", icon: ShieldCheck },
  { href: "/demo", label: "Guided Demo", icon: Sparkles }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[17rem_1fr]">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2">Skip to content</a>
      <aside className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-slate-700 bg-ink text-white transition-transform lg:sticky lg:top-0 lg:h-screen lg:w-auto lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`} aria-label="Primary navigation">
        <div className="flex h-full flex-col p-5">
          <div className="mb-7 flex items-start justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-300">JourneyGraph</p>
              <h1 className="mt-2 text-xl font-semibold">Retention Intelligence</h1>
            </div>
            <button className="rounded p-1 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={20} /></button>
          </div>
          <nav className="space-y-1">
            {navigation.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return <Link key={href} href={href} onClick={() => setOpen(false)} aria-current={active ? "page" : undefined} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? "bg-white text-ink" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}><Icon size={18} aria-hidden />{label}</Link>;
            })}
          </nav>
          <div className="mt-auto rounded-xl border border-slate-600 bg-slate-800 p-3 text-xs text-slate-300">
            <span className="mb-2 inline-flex rounded-full bg-gold px-2 py-1 font-bold text-white">Demo · historical observational data</span>
            <p>Local snapshot · cutoff Dec 31, 2024 · no mutations</p>
          </div>
        </div>
      </aside>
      {open && <button className="fixed inset-0 z-30 bg-ink/50 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}
      <div className="min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white/95 px-4 backdrop-blur md:px-8">
          <button className="rounded-lg border border-line p-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
          <p className="hidden text-sm text-muted sm:block">Governed evidence · human decisions · no causal claim</p>
          <Link href="/demo" className="button-secondary">Start guided demo</Link>
        </header>
        <main id="main-content" className="mx-auto max-w-[96rem] p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
