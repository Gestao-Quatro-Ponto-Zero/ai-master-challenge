"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { WELCOME_STORAGE_KEY } from "./WelcomeModal";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^|;)\\s*" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

export function Navbar() {
  const path      = usePathname();
  const router    = useRouter();
  const [role, setRole]         = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => { setRole(getCookie("role")); }, []);
  useEffect(() => { setMenuOpen(false); }, [path]); // close on navigate

  const isInsights = path === "/insights";
  const isManager  = path === "/manager";
  const isAdmin    = path === "/admin";

  async function handleLogout() {
    setLoggingOut(true);
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  function reopenWelcome() {
    localStorage.removeItem(WELCOME_STORAGE_KEY);
    window.dispatchEvent(new CustomEvent("reopen-welcome"));
    setMenuOpen(false);
  }

  const linkCls = (active: boolean) =>
    `text-sm px-3 py-2 rounded-lg transition-colors ${
      active
        ? "bg-gray-800 text-white"
        : "text-gray-400 hover:text-white hover:bg-gray-800/50"
    }`;

  const NavLinks = () => (
    <>
      <Link href="/"         className={linkCls(!isManager && !isInsights && !isAdmin)} onClick={() => setMenuOpen(false)}>Pipeline</Link>
      <Link href="/insights" className={linkCls(isInsights)} onClick={() => setMenuOpen(false)}>Insights</Link>
      <Link href="/manager"  className={linkCls(isManager)} onClick={() => setMenuOpen(false)}>Equipe</Link>
      {role === "admin" && (
        <Link href="/admin" className={linkCls(isAdmin)} onClick={() => setMenuOpen(false)}>⚙️ Admin</Link>
      )}
    </>
  );

  const RoleBadge = () => role ? (
    <span className={`text-xs px-2 py-1 rounded-md font-medium ${
      role === "admin"
        ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
        : "bg-gray-700/50 text-gray-400 border border-gray-700"
    }`}>
      {role === "admin" ? "Admin" : "Viewer"}
    </span>
  ) : null;

  return (
    <nav className="border-b border-gray-800 bg-gray-950/90 backdrop-blur-sm sticky top-0 z-40">
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">

        {/* Brand */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
            <span className="text-amber-400 font-black text-xs tracking-widest">G4</span>
          </div>
          <div className="hidden sm:block">
            <div className="text-white font-bold text-sm leading-tight">Lead Scorer</div>
            <div className="text-white text-[10px] leading-tight font-medium">Powered by Lucas de Paula</div>
          </div>
          {/* "Lead Scorer" text only on very small without subtitle */}
          <div className="sm:hidden">
            <div className="text-white font-bold text-sm leading-tight">Lead Scorer</div>
          </div>
        </div>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          <NavLinks />
          <button
            onClick={reopenWelcome}
            title="Abrir guia de boas-vindas"
            className="text-sm w-8 h-8 rounded-lg text-gray-600 hover:text-gray-300 hover:bg-gray-800/50 transition-colors flex items-center justify-center font-bold"
          >
            ?
          </button>
        </div>

        {/* Desktop right */}
        <div className="hidden md:flex items-center gap-3">
          <RoleBadge />
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-colors disabled:opacity-50"
          >
            {loggingOut ? "Saindo..." : "Sair"}
          </button>
        </div>

        {/* Hamburger — mobile only */}
        <button
          onClick={() => setMenuOpen((o) => !o)}
          className="md:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
        >
          {menuOpen ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-800 bg-gray-950 px-4 py-3 space-y-1">
          <NavLinks />
          <div className="pt-3 mt-2 border-t border-gray-800 flex items-center justify-between">
            <RoleBadge />
            <div className="flex items-center gap-2">
              <button
                onClick={reopenWelcome}
                className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white transition-colors"
              >
                📋 Guia
              </button>
              <button
                onClick={handleLogout}
                disabled={loggingOut}
                className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-colors disabled:opacity-50"
              >
                {loggingOut ? "Saindo..." : "Sair"}
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
