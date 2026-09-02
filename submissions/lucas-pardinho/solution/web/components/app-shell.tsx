"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BriefcaseBusiness,
  ChartNoAxesCombined,
  FlaskConical,
  ListFilter,
  Sparkles,
} from "lucide-react";

const NAVIGATION = [
  { href: "/", label: "Visão executiva", icon: ChartNoAxesCombined },
  { href: "/pipeline", label: "Pipeline", icon: ListFilter },
  { href: "/carteira", label: "Carteira", icon: BriefcaseBusiness },
  { href: "/metodologia", label: "Metodologia", icon: FlaskConical },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/" className="brand" aria-label="G4 Focus — início">
          <span className="brand-mark">G4</span>
          <span>
            <strong>Focus</strong>
            <small>Revenue intelligence</small>
          </span>
        </Link>

        <nav className="sidebar-nav" aria-label="Navegação principal">
          <span className="nav-eyebrow">Espaço de decisão</span>
          {NAVIGATION.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link${active ? " active" : ""}`}
                aria-current={active ? "page" : undefined}
              >
                <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <span className="status-icon"><Sparkles size={16} aria-hidden="true" /></span>
          <span>
            <strong>Motor de decisão ativo</strong>
            <small>Scores explicáveis e auditáveis</small>
          </span>
        </div>

        <p className="sidebar-footnote">G4 Focus · Challenge 003</p>
      </aside>

      <div className="mobile-topbar">
        <Link href="/" className="brand compact" aria-label="G4 Focus — início">
          <span className="brand-mark">G4</span>
          <strong>Focus</strong>
        </Link>
        <span className="live-pill"><span /> Dados do pipeline</span>
      </div>

      <nav className="mobile-nav" aria-label="Navegação principal móvel">
        {NAVIGATION.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={active ? "active" : ""}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{item.label.replace("Visão executiva", "Visão")}</span>
            </Link>
          );
        })}
      </nav>

      <main className="main-content">{children}</main>
    </div>
  );
}
