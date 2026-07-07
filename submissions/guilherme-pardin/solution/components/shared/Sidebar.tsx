"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  KanbanSquare,
  ListChecks,
  LineChart,
  Users,
  TrendingUp,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/lib/hooks/useAuth";
import { useSidebar } from "@/lib/hooks/useSidebar";
import { avatarBg, cn, initials } from "@/lib/utils";
import { agentByName } from "@/lib/data";

type Item = { href: string; label: string; icon: React.ReactNode };

const SELLER_ITEMS: Item[] = [
  { href: "/pipeline", label: "Pipeline", icon: <KanbanSquare className="h-5 w-5" /> },
  { href: "/scores", label: "Priorização", icon: <ListChecks className="h-5 w-5" /> },
  { href: "/performance", label: "Meu desempenho", icon: <TrendingUp className="h-5 w-5" /> },
];

const LEADERSHIP_ITEMS: Item[] = [
  { href: "/pipeline", label: "Pipeline", icon: <KanbanSquare className="h-5 w-5" /> },
  { href: "/scores", label: "Priorização", icon: <ListChecks className="h-5 w-5" /> },
  { href: "/dashboard", label: "Painel gerencial", icon: <LineChart className="h-5 w-5" /> },
  { href: "/team", label: "Mapa do time", icon: <Users className="h-5 w-5" /> },
];

const SIDEBAR_EXPANDED = 240;
const SIDEBAR_COLLAPSED = 68;

export function Sidebar() {
  const { user, logout } = useAuth();
  const { collapsed, toggle } = useSidebar();
  const pathname = usePathname();
  const router = useRouter();

  if (!user) return null;

  const items = user.role === "seller" ? SELLER_ITEMS : LEADERSHIP_ITEMS;
  const agent = user.role === "seller" ? agentByName(user.name) : null;
  const roleLabel =
    user.role === "gestor"
      ? "Gestor"
      : user.role === "manager"
        ? "Gerente"
        : agent
          ? `${agent.region} · Conv. ${(agent.overallWr * 100).toFixed(0)}%`
          : "Vendedor";

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <aside
      style={{
        width: collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED,
        transition: "width 150ms ease",
      }}
      className="hidden md:flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border fixed left-0 top-0 h-screen z-30 overflow-hidden shadow-[var(--shadow-sidebar)]"
    >
      <div
        className={cn(
          "flex items-center border-b border-white/10 h-[73px] shrink-0",
          collapsed ? "justify-center px-2" : "gap-3 px-5",
        )}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo-g4.png"
          alt="G4"
          className={cn(
            "shrink-0 rounded-md object-cover",
            collapsed ? "h-9 w-9" : "h-12 w-12",
          )}
        />
        {!collapsed && (
          <span className="text-white font-light text-lg tracking-wide whitespace-nowrap">
            Lead Scorer
          </span>
        )}
      </div>

      <button
        onClick={toggle}
        aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
        title={collapsed ? "Expandir menu" : "Recolher menu"}
        className={cn(
          "self-end mr-3 mt-3 mb-1 h-6 w-6 rounded grid place-items-center text-sidebar-foreground hover:bg-white/5 hover:text-white transition-colors duration-150",
          collapsed && "self-center mr-0",
        )}
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>

      <nav className={cn("flex-1 space-y-1", collapsed ? "px-2" : "px-3")}>
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center rounded-md text-sm font-medium relative border-l-2",
                collapsed
                  ? "justify-center h-10 px-0 border-l-0"
                  : "gap-3 pl-3 pr-3 py-2",
                active
                  ? collapsed
                    ? "bg-[var(--brand-navy-700)] text-white"
                    : "bg-[var(--brand-navy-700)] text-white border-l-[color:var(--brand-gold-500)]"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white border-l-transparent transition-colors duration-150",
              )}
            >
              {item.icon}
              {!collapsed && (
                <span className="whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <div
        className={cn(
          "mb-4",
          collapsed ? "px-2" : "p-3 mx-3 rounded-lg bg-[var(--brand-navy-800)] border border-white/10",
        )}
      >
        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <div
              className={cn(
                "h-9 w-9 shrink-0 rounded-full grid place-items-center text-white text-xs font-semibold ring-2 ring-[color:var(--brand-gold-500)]",
                avatarBg(user.name),
              )}
              title={`${user.name} · ${roleLabel}`}
            >
              {initials(user.name)}
            </div>
            <button
              onClick={handleLogout}
              aria-label="Trocar perfil"
              title="Trocar perfil"
              className="h-8 w-8 grid place-items-center rounded-md text-sidebar-foreground hover:bg-white/5 hover:text-white transition-colors duration-150"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2.5">
              <div
                className={cn(
                  "h-9 w-9 shrink-0 rounded-full grid place-items-center text-white text-xs font-semibold ring-2 ring-[color:var(--brand-gold-500)] ring-offset-2 ring-offset-[color:var(--brand-navy-800)]",
                  avatarBg(user.name),
                )}
              >
                {initials(user.name)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-white truncate">
                  {user.name}
                </div>
                <div className="text-[11px] text-[color:var(--brand-gold-300)] truncate">
                  {roleLabel}
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-[13px] font-medium text-sidebar-foreground hover:bg-white/5 hover:text-white transition-colors duration-150"
            >
              <LogOut className="h-3.5 w-3.5" />
              Trocar perfil
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
