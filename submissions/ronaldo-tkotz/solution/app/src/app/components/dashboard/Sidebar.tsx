"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { openConnect } from "./ConnectDialog";
import { useTotalMarcados } from "../telas/Marcados";
import { MinhasTelasNav } from "../telas/MinhasTelasNav";
import { logout } from "@/app/actions/auth";

/**
 * The nav is honest about what this app is: a single grounded-conversation
 * surface with one other route (the deck). There are no scrollable "sections"
 * to jump between — so every item performs a real action instead of scrolling
 * to an anchor that doesn't exist:
 *   reset   → clear the transcript, bringing back the executive brief
 *   route   → a real page (the deck)
 *   connect → open the connect/swap-dataset dialog
 *   ask     → drop a grounded question into the chat (Chat listens for veta:ask)
 */
type NavAction =
  | { kind: "reset" }
  | { kind: "route"; href: string }
  | { kind: "connect" }
  | { kind: "ask"; question: string };

interface NavItem {
  id: string;
  label: string;
  action: NavAction;
}

/** The executive overview (D28) and the two screens left after D44 and D49. Links keep the global filters. */
const TELAS: { id: string; icon: string; label: string; href: string }[] = [
  { id: "visao", icon: "overview", label: "Visão geral", href: "/" },
  { id: "tela2", icon: "library", label: "O que causa o churn", href: "/tela/2" },
  { id: "tela3", icon: "accounts", label: "Suporte e uso do produto", href: "/tela/3" },
];

const WORKSPACE: NavItem[] = [
  { id: "marcados", label: "Gráficos marcados", action: { kind: "route", href: "/marcados" } },
  { id: "engine", label: "Conectar dados", action: { kind: "connect" } },
];

function Icon({ id }: { id: string }) {
  const p: Record<string, React.ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    insights: <path d="M3 12h4l3 8 4-16 3 8h4" />,
    accounts: <><path d="M3 21h18" /><path d="M5 21V7l8-4v18" /><path d="M19 21V11l-6-4" /></>,
    usage: <><path d="M3 3v18h18" /><rect x="7" y="11" width="3" height="6" /><rect x="12" y="7" width="3" height="10" /><rect x="17" y="13" width="3" height="4" /></>,
    execdeck: <path d="M5 3v4M3 5h4M6 17v4M4 19h4M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5z" />,
    library: <><path d="M3 7l9-4 9 4-9 4-9-4Z" /><path d="M3 12l9 4 9-4" /><path d="M3 17l9 4 9-4" /></>,
    marcados: <path d="M6 3h12v18l-6-4.5L6 21z" />,
    engine: <path d="m8 9-3 3 3 3M16 9l3 3-3 3M13 7l-2 10" />,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 shrink-0">
      {p[id]}
    </svg>
  );
}

// ── History: the saved conversations, restorable + renamable + deletable ──────

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

/** Tiny inline icons for the per-item controls. */
function MiniIcon({ kind }: { kind: "edit" | "trash" | "check" | "x" | "plus" }) {
  const p: Record<string, React.ReactNode> = {
    edit: <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />,
    trash: <><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" /></>,
    check: <path d="M20 6 9 17l-5-5" />,
    x: <path d="M18 6 6 18M6 6l12 12" />,
    plus: <path d="M12 5v14M5 12h14" />,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
      {p[kind]}
    </svg>
  );
}

function History() {
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [chatBusy, setChatBusy] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/conversations");
      if (!res.ok) return;
      const data = (await res.json()) as { conversations?: Conversation[] };
      setConvs(Array.isArray(data.conversations) ? data.conversations : []);
    } catch {
      /* sidebar history is best-effort — never break the shell */
    }
  }, []);

  useEffect(() => {
    let alive = true;
    // Mount fetch inlined (setState lands after the await — no synchronous render cascade).
    void (async () => {
      try {
        const res = await fetch("/api/conversations");
        if (!res.ok || !alive) return;
        const data = (await res.json()) as { conversations?: Conversation[] };
        if (alive) setConvs(Array.isArray(data.conversations) ? data.conversations : []);
      } catch {
        /* best-effort */
      }
    })();
    const onChanged = () => void load();
    const onActive = (e: Event) => setActiveId((e as CustomEvent<{ id?: string | null }>).detail?.id ?? null);
    const onBusy = (e: Event) => setChatBusy(Boolean((e as CustomEvent<{ busy?: boolean }>).detail?.busy));
    window.addEventListener("veta:history-changed", onChanged);
    window.addEventListener("veta:active-conversation", onActive);
    window.addEventListener("veta:chat-busy", onBusy);
    return () => {
      alive = false;
      window.removeEventListener("veta:history-changed", onChanged);
      window.removeEventListener("veta:active-conversation", onActive);
      window.removeEventListener("veta:chat-busy", onBusy);
    };
  }, [load]);

  const open = (id: string) => {
    if (chatBusy || editingId) return;
    window.dispatchEvent(new CustomEvent("veta:load-conversation", { detail: { id } }));
  };

  const commitRename = async (id: string) => {
    const title = draft.trim();
    setEditingId(null);
    if (!title) return;
    await fetch(`/api/conversations/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    }).catch(() => {});
    void load();
  };

  const remove = async (id: string) => {
    setConfirmId(null);
    await fetch(`/api/conversations/${id}`, { method: "DELETE" }).catch(() => {});
    window.dispatchEvent(new CustomEvent("veta:conversation-deleted", { detail: { id } }));
    void load();
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-1.5 flex shrink-0 items-center gap-2 px-1 text-[10px] font-medium uppercase tracking-wider text-faint">
        History
        {convs.length > 0 && (
          <span className="rounded-full border border-edge px-1.5 py-0.5 text-[9px] normal-case tracking-normal">{convs.length}</span>
        )}
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("veta:new-chat"))}
          title="New chat"
          className="ml-auto inline-flex items-center gap-0.5 rounded text-faint transition-colors hover:text-foreground"
        >
          <MiniIcon kind="plus" />
        </button>
      </div>

      {convs.length === 0 ? (
        <p className="px-1 text-[11.5px] leading-snug text-faint">Your conversations will appear here once you ask Veta something.</p>
      ) : (
        <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto pr-0.5">
          {convs.map((c) => {
            const isActive = c.id === activeId;
            const isEditing = c.id === editingId;
            const isConfirming = c.id === confirmId;
            return (
              <li
                key={c.id}
                aria-current={isActive ? "true" : undefined}
                className={`group flex items-center gap-1 rounded-lg px-2 py-1.5 text-[12.5px] transition-colors ${
                  isActive ? "bg-accent-soft text-foreground" : "text-muted hover:bg-panel/60"
                }`}
              >
                {isEditing ? (
                  <input
                    autoFocus
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onBlur={() => void commitRename(c.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") void commitRename(c.id);
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    className="min-w-0 flex-1 rounded border border-edge-strong bg-panel px-1.5 py-0.5 text-[12.5px] text-foreground focus:outline-none"
                  />
                ) : (
                  <>
                    <button
                      onClick={() => open(c.id)}
                      disabled={chatBusy}
                      title={chatBusy ? "Finish the current answer first" : c.title}
                      className="min-w-0 flex-1 truncate text-left disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isActive && <span className="mr-1.5 inline-block h-1 w-1 -translate-y-px rounded-full bg-accent align-middle" />}
                      {c.title}
                    </button>
                    {isConfirming ? (
                      <span className="flex shrink-0 items-center gap-1">
                        <span className="text-[10px] text-faint">Delete?</span>
                        <button onClick={() => void remove(c.id)} title="Confirm delete" className="text-red-400 hover:text-red-300">
                          <MiniIcon kind="check" />
                        </button>
                        <button onClick={() => setConfirmId(null)} title="Cancel" className="text-faint hover:text-foreground">
                          <MiniIcon kind="x" />
                        </button>
                      </span>
                    ) : (
                      <span className="flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
                        <button
                          onClick={() => {
                            setEditingId(c.id);
                            setDraft(c.title);
                          }}
                          title="Rename"
                          className="text-faint hover:text-foreground"
                        >
                          <MiniIcon kind="edit" />
                        </button>
                        <button onClick={() => setConfirmId(c.id)} title="Delete" className="text-faint hover:text-red-400">
                          <MiniIcon kind="trash" />
                        </button>
                      </span>
                    )}
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function Sidebar({ email }: { email: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const query = useSearchParams().toString();
  // Show the signed-in user, never a hardcoded name — SP05: "every user sees only their own work".
  const displayName = email.split("@")[0] || email;
  const initial = (displayName[0] ?? "?").toUpperCase();

  const run = (item: NavItem): void => {
    const a = item.action;
    switch (a.kind) {
      case "reset":
        window.dispatchEvent(new CustomEvent("veta:new-chat"));
        break;
      case "route":
        router.push(a.href);
        break;
      case "connect":
        openConnect();
        break;
      case "ask":
        window.dispatchEvent(new CustomEvent("veta:ask", { detail: { question: a.question } }));
        break;
    }
  };

  const totalMarcados = useTotalMarcados();

  const NavButton = ({ item }: { item: NavItem }) => (
    <button
      onClick={() => run(item)}
      className="group flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-muted transition-colors hover:bg-panel/60 hover:text-foreground"
    >
      <span className="text-muted group-hover:text-accent">
        <Icon id={item.id} />
      </span>
      <span>{item.label}</span>
      {item.id === "marcados" && totalMarcados !== null && totalMarcados > 0 && (
        <span className="ml-auto rounded-full bg-accent-soft px-1.5 font-mono text-[10.5px] text-accent">{totalMarcados}</span>
      )}
      {item.action.kind === "ask" && (
        <span className="ml-auto text-[13px] leading-none text-faint opacity-0 transition-opacity group-hover:opacity-100">→</span>
      )}
    </button>
  );

  return (
    <aside className="flex h-full w-[232px] shrink-0 flex-col border-r border-edge bg-surface">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <span className="grid h-7 w-7 place-items-center rounded-md bg-accent-soft">
          <span className="h-2.5 w-2.5 rotate-45 bg-accent" />
        </span>
        <div className="leading-tight">
          <div className="text-[14px] font-semibold tracking-tight text-foreground">RavenStack</div>
          <div className="text-[10px] text-faint">diagnóstico de churn</div>
        </div>
      </div>

      <nav className="flex flex-col gap-3 px-2.5 py-2">
        <div className="flex flex-col gap-0.5">
          <div className="px-2.5 pb-1 text-[10px] font-medium uppercase tracking-wider text-faint">Telas</div>
          {TELAS.map((t) => {
            const active = t.href === "/" ? pathname === "/" : pathname.startsWith(t.href);
            return (
              <button
                key={t.id}
                onClick={() => router.push(query ? `${t.href}?${query}` : t.href)}
                aria-current={active ? "page" : undefined}
                className={`group flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[12.5px] transition-colors hover:bg-panel/60 hover:text-foreground ${
                  active ? "bg-panel text-foreground" : "text-muted"
                }`}
              >
                <span className={active ? "text-accent" : "text-muted group-hover:text-accent"}>
                  <Icon id={t.icon} />
                </span>
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>
        <MinhasTelasNav />
        <div className="flex flex-col gap-0.5">
          {WORKSPACE.map((item) => (
            <NavButton key={item.id} item={item} />
          ))}
        </div>
      </nav>

      <div className="mt-2 flex min-h-0 flex-1 flex-col px-3 py-3">
        <History />
      </div>

      <div className="flex items-center gap-2 border-t border-edge px-4 py-3 text-[11px] text-faint">
        <span className="grid h-6 w-6 place-items-center rounded-full bg-panel text-[10px] font-semibold text-muted">{initial}</span>
        <span className="max-w-[110px] truncate" title={email}>{displayName}</span>
        <span className="inline-flex items-center gap-1 text-emerald-400/90">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> live
        </span>
        <form action={logout} className="ml-auto">
          <button
            type="submit"
            title="Sign out"
            aria-label="Sign out"
            className="inline-flex items-center gap-1 rounded px-1.5 py-1 text-faint transition-colors hover:text-foreground"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </form>
      </div>
    </aside>
  );
}
