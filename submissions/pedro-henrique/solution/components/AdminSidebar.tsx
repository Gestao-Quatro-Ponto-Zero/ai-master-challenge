"use client";

import Image from "next/image";
import { usePathname } from "next/navigation";

/* ── Icons ──────────────────────────────────────────────────────────────── */
const IconHome = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1.5 6.5L7.5 1.5L13.5 6.5V13H9.5V9.5H5.5V13H1.5V6.5Z" />
  </svg>
);
const IconTicket = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1.5 5.5a1.5 1.5 0 1 1 0 4V5.5zM13.5 5.5a1.5 1.5 0 1 0 0 4V5.5zM3 5.5h9M3 9.5h9" />
  </svg>
);
const IconBook = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 3.5A1.5 1.5 0 0 1 3.5 2H12v11H3.5A1.5 1.5 0 0 1 2 11.5v-8z" />
    <path d="M12 2v11M5 5h4M5 7.5h3" />
  </svg>
);
const IconNlp = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7.5" cy="7.5" r="5.5" />
    <path d="M5 7.5h5M7.5 5v5" />
    <path d="M4 4.5C4.5 3.5 5.9 3 7.5 3c2 0 3.5 1.1 3.5 2.5 0 1.2-.9 2.2-2.2 2.7L8.5 10h-2l-.3-1.8C4.9 7.7 4 6.7 4 5.5" />
  </svg>
);
const IconLogout = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 2.5H5a1.5 1.5 0 0 0-1.5 1.5v7A1.5 1.5 0 0 0 5 12.5h4M10.5 5l3 2.5-3 2.5M13.5 7.5H7" />
  </svg>
);

const NAV = [
  { href: "/admin",         icon: <IconHome />,   label: "Visão geral" },
  { href: "/admin/tickets", icon: <IconTicket />, label: "Tickets" },
  { href: "/admin/kb",      icon: <IconBook />,   label: "Base de Conhecimento" },
  { href: "/admin/nlp",     icon: <IconNlp />,    label: "NLP & IA" },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="admin-sidebar">
      <div
        style={{
          height: "var(--ad-header-h, 56px)",
          display: "flex",
          alignItems: "center",
          gap: "0.625rem",
          padding: "0 1rem",
          borderBottom: "1px solid var(--ad-sb-sep)",
        }}
      >
        <Image src="/logo-g4.png" alt="Logo G4" width={24} height={24} />
        <p style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600, color: "var(--ad-sb-brand-name)" }}>
          G4 Help
        </p>
      </div>

      <nav style={{ flex: 1, padding: "0.75rem", display: "flex", flexDirection: "column", gap: "0.125rem" }}>
        {NAV.map(({ href, icon, label }) => {
          const active = pathname === href || (href !== "/admin" && pathname.startsWith(href));
          return (
            <a key={href} href={href} className={`sidebar-item${active ? " active" : ""}`}>
              {icon} {label}
            </a>
          );
        })}
      </nav>

      <div style={{ padding: "0.75rem", borderTop: "1px solid var(--ad-sb-sep)" }}>
        <a href="/api/auth/demo?logout=1" className="sidebar-item">
          <IconLogout /> Sair
        </a>
      </div>
    </aside>
  );
}
