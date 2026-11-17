"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Insight, Severity } from "@/engine/insights";

const SEV: Record<Severity, { dot: string; pill: string; label: string }> = {
  critical: { dot: "bg-red-500", pill: "text-red-300 border-red-400/25 bg-red-400/10", label: "Critical" },
  warning: { dot: "bg-amber-400", pill: "text-amber-300 border-amber-400/25 bg-amber-400/10", label: "Watch" },
  opportunity: { dot: "bg-emerald-400", pill: "text-emerald-300 border-emerald-400/25 bg-emerald-400/10", label: "Upside" },
  info: { dot: "bg-accent", pill: "text-muted border-edge bg-surface", label: "Info" },
};

/** A pinned insight as the API returns it (snake_case rows). */
interface Pin {
  id: number;
  source_kind: string;
  source_id: string;
  question: string | null;
  answer: string | null;
  cited_sql_json: string | null;
  chart_json: string | null;
  table_json: string | null;
  title: string | null;
  sort_order: number;
}

function evidenceCount(p: Pin): number {
  try {
    const arr = JSON.parse(p.cited_sql_json ?? "[]");
    return Array.isArray(arr) ? arr.length : 0;
  } catch {
    return 0;
  }
}

/** Kind tag for a part pin — chart type ("PIE"), table width ("TABLE · 4 col"), or "NOTE". */
function partTag(p: Pin): { tag: string; snippet?: string } | null {
  try {
    if (p.source_kind === "chart") {
      const c = p.chart_json ? (JSON.parse(p.chart_json) as { type?: string; transform?: { type?: string } }) : null;
      const t = c?.transform?.type ?? c?.type;
      return { tag: (typeof t === "string" ? t : "chart").toUpperCase() };
    }
    if (p.source_kind === "table") {
      const t = p.table_json ? (JSON.parse(p.table_json) as { columns?: unknown[] }) : null;
      const n = Array.isArray(t?.columns) ? t.columns.length : 0;
      return { tag: n > 0 ? `TABLE · ${n} col` : "TABLE" };
    }
    if (p.source_kind === "narrative") {
      const s = (p.answer ?? "").trim().replace(/\s+/g, " ").slice(0, 80);
      return { tag: "NOTE", snippet: s || undefined };
    }
  } catch {
    /* malformed payload — fall through to the plain row */
  }
  return null;
}

/** Small glyph per part kind, matching the tag pill. */
function PartGlyph({ kind }: { kind: string }) {
  const cls = "h-3 w-3";
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (kind === "chart")
    return (
      <svg viewBox="0 0 24 24" className={cls} {...common}><path d="M3 3v18h18M8 17v-6M13 17V7M18 17v-4" /></svg>
    );
  if (kind === "table")
    return (
      <svg viewBox="0 0 24 24" className={cls} {...common}><path d="M3 5h18v14H3zM3 10h18M9 5v14M15 5v14" /></svg>
    );
  return (
    <svg viewBox="0 0 24 24" className={cls} {...common}><path d="M4 6h16M4 10h16M4 14h10M4 18h7" /></svg>
  );
}

function ask(question: string): void {
  window.dispatchEvent(new CustomEvent("veta:ask", { detail: { question } }));
}

function deckChanged(): void {
  window.dispatchEvent(new CustomEvent("veta:deck-changed"));
}

/** Three shimmering placeholders while the discovery engine works. */
function FeedSkeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      {[0, 1, 2].map((i) => (
        <div key={i} className="rounded-lg border border-edge bg-surface/60 p-3">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-edge-strong" />
            <span className="veta-pulse h-2.5 w-24 rounded bg-edge-strong/60" />
          </div>
          <div className="mt-2.5 h-2 w-full rounded bg-edge-strong/40" />
          <div className="mt-1.5 h-2 w-3/4 rounded bg-edge-strong/40" />
        </div>
      ))}
    </div>
  );
}

function Ctrl({ label, onClick, disabled, children }: { label: string; onClick: () => void; disabled?: boolean; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      aria-label={label}
      className="grid h-5 w-5 place-items-center rounded text-faint transition-colors hover:text-foreground disabled:opacity-30 disabled:hover:text-faint"
    >
      {children}
    </button>
  );
}

/**
 * The right rail: two tabs, both the USER's deliberate work. "Insights" is the
 * proactive discovery feed (Ask Veta / pin). "Deck" is the collection of pinned
 * grounded answers the builder assembles into a curated deck; every built deck
 * lands in the Deck Library. The autonomous "Veta Executive Deck" is a SYSTEM
 * concern — it lives on the left nav (always-live from current data), not here —
 * so user intent and system automation never compete for the same surface. One
 * tab at a time keeps no-scroll at 1440×900.
 */
export function RightRail({ initialInsights }: { initialInsights: Insight[] | null }) {
  const router = useRouter();
  const [tab, setTab] = useState<"insights" | "draft">("insights");
  const [insights, setInsights] = useState<Insight[]>(initialInsights ?? []);
  const [loading, setLoading] = useState(initialInsights === null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [pins, setPins] = useState<Pin[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [brief, setBrief] = useState("");
  const [building, setBuilding] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);

  const pinnedFindingIds = new Set(pins.filter((p) => p.source_kind === "finding").map((p) => p.source_id));

  // Cold cache → discover client-side so the page never blocks on the LLM.
  useEffect(() => {
    if (initialInsights !== null) return;
    let alive = true;
    (async () => {
      try {
        const res = await fetch("/api/insights");
        const data = (await res.json()) as { insights?: Insight[]; error?: string };
        if (!alive) return;
        if (data.error) setError(data.error);
        else setInsights(data.insights ?? []);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [initialInsights]);

  const refetchPins = useCallback(async () => {
    try {
      const res = await fetch("/api/saved-insights");
      if (!res.ok) return;
      const data = (await res.json()) as { savedInsights?: Pin[] };
      setPins(Array.isArray(data.savedInsights) ? data.savedInsights : []);
    } catch {
      /* best-effort */
    }
  }, []);

  // Load the deck draft on mount + whenever it changes (pin/remove/reorder).
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const res = await fetch("/api/saved-insights");
        if (!res.ok || !alive) return;
        const data = (await res.json()) as { savedInsights?: Pin[] };
        if (alive) setPins(Array.isArray(data.savedInsights) ? data.savedInsights : []);
      } catch {
        /* best-effort */
      }
    })();
    const onDeck = () => void refetchPins();
    window.addEventListener("veta:deck-changed", onDeck);
    return () => {
      alive = false;
      window.removeEventListener("veta:deck-changed", onDeck);
    };
  }, [refetchPins]);

  const reanalyze = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/insights", { method: "POST" });
      const data = (await res.json()) as { insights?: Insight[]; error?: string };
      if (data.error) setError(data.error);
      else setInsights(data.insights ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  // Toggle a finding in the deck draft — pin it, or unpin it if it's already in.
  // Mirrors the chat window's pin toggle; unpin is by natural key so we needn't
  // resolve the (optimistic) numeric id first.
  const toggleFinding = async (ins: Insight, isPinned: boolean) => {
    if (isPinned) {
      setPins((prev) => prev.filter((p) => !(p.source_kind === "finding" && p.source_id === ins.id)));
      try {
        await fetch("/api/saved-insights", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sourceKind: "finding", sourceId: ins.id }),
        });
      } catch {
        /* best-effort */
      }
    } else {
      setPins((prev) => [...prev, { id: -Date.now(), source_kind: "finding", source_id: ins.id, question: ins.title, answer: ins.headline, cited_sql_json: JSON.stringify([ins.evidenceSql]), chart_json: null, table_json: null, title: ins.title, sort_order: prev.length }]);
      try {
        await fetch("/api/saved-insights", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sourceKind: "finding", sourceId: ins.id, question: ins.title, answer: ins.headline, citedSql: [ins.evidenceSql], title: ins.title }),
        });
      } catch {
        /* best-effort */
      }
    }
    deckChanged();
  };

  const move = async (index: number, dir: -1 | 1) => {
    const j = index + dir;
    if (j < 0 || j >= pins.length) return;
    // Optimistic-id guard: a just-pinned finding sits in state with a fake negative
    // id until the refetch reconciles it. Reordering then would persist a bogus id —
    // reconcile first and let the user click again on real rows.
    if (pins.some((p) => p.id < 0)) {
      void refetchPins();
      return;
    }
    const next = [...pins];
    [next[index], next[j]] = [next[j], next[index]];
    setPins(next);
    try {
      await fetch("/api/saved-insights/reorder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: next.map((p) => p.id) }),
      });
    } catch {
      /* best-effort */
    }
    deckChanged();
  };

  const remove = async (id: number) => {
    setPins((prev) => prev.filter((p) => p.id !== id));
    try {
      await fetch(`/api/saved-insights/${id}`, { method: "DELETE" });
    } catch {
      /* best-effort */
    }
    deckChanged();
  };

  const commitRename = async (id: number) => {
    const title = draft.trim();
    setEditingId(null);
    if (!title) return;
    setPins((prev) => prev.map((p) => (p.id === id ? { ...p, title } : p)));
    try {
      await fetch(`/api/saved-insights/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
    } catch {
      /* best-effort */
    }
    deckChanged();
  };

  // Build a grounded deck from the pinned collection. Reads pins server-side, so we
  // send only the optional one-line brief; the route re-grounds every number.
  const buildDeck = useCallback(async () => {
    if (building) return;
    setBuilding(true);
    setBuildError(null);
    try {
      const res = await fetch("/api/deck/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief: brief.trim() || undefined }),
      });
      const data = (await res.json()) as { id?: string; error?: string };
      if (!res.ok || !data.id) {
        setBuildError(data.error ?? "Deck build failed.");
        return;
      }
      router.push(`/deck/${encodeURIComponent(data.id)}`);
    } catch (e) {
      setBuildError(e instanceof Error ? e.message : String(e));
    } finally {
      setBuilding(false);
    }
  }, [brief, building, router]);

  const top = insights.slice(0, 3);

  return (
    <div className="flex h-full flex-col gap-3 overflow-hidden">
      {/* Tabs */}
      <div className="flex shrink-0 gap-1 rounded-lg border border-edge bg-panel p-1">
        {([
          ["insights", "Insights"],
          ["draft", "Deck"],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            aria-current={tab === key ? "true" : undefined}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-medium transition-colors ${
              tab === key ? "bg-surface text-foreground" : "text-faint hover:text-muted"
            }`}
          >
            {label}
            {key === "draft" && pins.length > 0 && (
              <span className="rounded-full bg-accent-soft px-1.5 text-[10px] font-semibold text-accent">{pins.length}</span>
            )}
          </button>
        ))}
      </div>

      {tab === "insights" ? (
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto">
          {/* What needs attention — the discovery feed. */}
          <div className="rounded-xl border border-edge bg-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <h3 className="text-[13px] font-semibold text-foreground">Needs your attention</h3>
              <button
                onClick={reanalyze}
                disabled={busy || loading}
                title="Re-analyze the connected dataset"
                className="ml-auto inline-flex items-center gap-1 rounded-md border border-edge px-1.5 py-0.5 text-[10px] text-muted transition-colors hover:border-edge-strong hover:text-foreground disabled:opacity-50"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`h-3 w-3 ${busy ? "veta-spin" : ""}`}>
                  <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6" />
                </svg>
                {busy ? "Analyzing…" : "Re-analyze"}
              </button>
            </div>

            {loading || busy ? (
              <FeedSkeleton />
            ) : error ? (
              <p className="rounded-lg border border-amber-400/30 bg-amber-400/5 px-3 py-2.5 text-[12px] leading-snug text-amber-200/90">
                Discovery failed: {error}
              </p>
            ) : top.length === 0 ? (
              <p className="rounded-lg border border-edge bg-surface/60 px-3 py-2.5 text-[12px] leading-snug text-muted">
                No material signals surfaced in the current data.
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {top.map((ins) => {
                  const s = SEV[ins.severity];
                  const isPinned = pinnedFindingIds.has(ins.id);
                  return (
                    <div key={ins.id} className="rounded-lg border border-edge bg-surface/60 p-3 transition-colors hover:border-edge-strong">
                      <div className="flex items-center gap-2">
                        <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
                        <span className="text-[12.5px] font-semibold text-foreground">{ins.title}</span>
                        <span className={`ml-auto rounded-full border px-1.5 py-[1px] text-[9px] font-semibold uppercase tracking-wide ${s.pill}`}>
                          {s.label}
                        </span>
                      </div>
                      <p className="mt-1.5 text-[11.5px] leading-snug text-muted">{ins.headline}</p>
                      <div className="mt-2 flex items-center gap-3">
                        <button
                          onClick={() => ask(`Walk me through "${ins.title}": ${ins.headline} Name the accounts involved and what we should do about it.`)}
                          className="text-[11px] font-medium text-accent transition-opacity hover:opacity-80"
                        >
                          Ask Veta →
                        </button>
                        <button
                          onClick={() => void toggleFinding(ins, isPinned)}
                          title={isPinned ? "Pinned to your deck draft — click to remove" : "Pin to the deck draft"}
                          aria-pressed={isPinned}
                          className={`group ml-auto inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium transition-colors ${
                            isPinned ? "border-accent/30 bg-accent-soft/50 text-accent hover:border-red-400/40 hover:bg-red-400/5 hover:text-red-300" : "border-edge text-faint hover:border-edge-strong hover:text-foreground"
                          }`}
                        >
                          <svg viewBox="0 0 24 24" fill={isPinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3">
                            <path d="M12 17v5M9 10.76V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4.76a2 2 0 0 0 .59 1.42l1.41 1.41A2 2 0 0 1 18 15.83V17H6v-1.17a2 2 0 0 1 .59-1.42L8 13a2 2 0 0 0 .59-1.42Z" />
                          </svg>
                          {isPinned ? (
                            <>
                              <span className="group-hover:hidden">Pinned</span>
                              <span className="hidden group-hover:inline">Remove</span>
                            </>
                          ) : (
                            "Pin"
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      ) : (
        /* Deck draft — the pinned collection the phase-3 builder assembles. */
        <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-edge bg-panel">
          <div className="flex shrink-0 items-center gap-2 border-b border-edge px-4 py-3">
            <h3 className="text-[13px] font-semibold text-foreground">Deck draft</h3>
            <span className="text-[11px] text-faint">{pins.length} pinned</span>
          </div>

          {pins.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-2.5 px-6 py-10 text-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className="h-7 w-7 text-faint">
                <path d="M12 17v5M9 10.76V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4.76a2 2 0 0 0 .59 1.42l1.41 1.41A2 2 0 0 1 18 15.83V17H6v-1.17a2 2 0 0 1 .59-1.42L8 13a2 2 0 0 0 .59-1.42Z" />
              </svg>
              <p className="text-[12.5px] font-medium text-muted">No pins yet</p>
              <p className="max-w-[235px] text-[11.5px] leading-snug text-faint">
                Hit <span className="text-muted">Pin to deck</span> on any grounded answer — or a finding — to curate your own deck. Build it here and it&apos;s saved to your <span className="text-muted">Deck Library</span>.
              </p>
              <p className="mt-1 max-w-[235px] text-[11px] leading-snug text-faint">
                Want Veta&apos;s auto deck instead? It&apos;s <span className="text-accent">Veta Executive Deck</span> on the left — always live.
              </p>
            </div>
          ) : (
            <>
              <ul className="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
                {pins.map((p, i) => {
                  const ev = evidenceCount(p);
                  const part = partTag(p);
                  return (
                    <li key={p.id} className="rounded-lg border border-edge bg-surface/60 p-2.5">
                      <div className="flex items-start gap-2">
                        <span className="mt-[3px] font-mono text-[10px] text-faint">{i + 1}</span>
                        <div className="min-w-0 flex-1">
                          {editingId === p.id ? (
                            <input
                              autoFocus
                              value={draft}
                              onChange={(e) => setDraft(e.target.value)}
                              onBlur={() => void commitRename(p.id)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") void commitRename(p.id);
                                if (e.key === "Escape") setEditingId(null);
                              }}
                              className="w-full rounded border border-edge-strong bg-panel px-1.5 py-0.5 text-[12.5px] text-foreground focus:outline-none"
                            />
                          ) : (
                            <div className="truncate text-[12.5px] font-medium text-foreground">{p.title || p.question || "Untitled insight"}</div>
                          )}
                          {part?.snippet ? (
                            <div className="mt-0.5 truncate text-[11px] text-faint">{part.snippet}</div>
                          ) : (
                            p.question && <div className="mt-0.5 truncate text-[11px] text-faint">{p.question}</div>
                          )}
                          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-faint">
                            {part && (
                              <span className="inline-flex items-center gap-1 rounded border border-edge px-1 py-[1px] font-medium uppercase tracking-wide text-muted">
                                <PartGlyph kind={p.source_kind} />
                                {part.tag}
                              </span>
                            )}
                            <span className="inline-flex items-center gap-1">
                              <span className="h-1 w-1 rounded-full bg-emerald-400/80" />
                              {ev} quer{ev === 1 ? "y" : "ies"} cited
                            </span>
                          </div>
                        </div>
                        <div className="flex shrink-0 items-center gap-0.5">
                          <Ctrl label="Move up" onClick={() => void move(i, -1)} disabled={i === 0}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3"><path d="m18 15-6-6-6 6" /></svg>
                          </Ctrl>
                          <Ctrl label="Move down" onClick={() => void move(i, 1)} disabled={i === pins.length - 1}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3"><path d="m6 9 6 6 6-6" /></svg>
                          </Ctrl>
                          <Ctrl label="Rename" onClick={() => { setEditingId(p.id); setDraft(p.title || p.question || ""); }}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>
                          </Ctrl>
                          <Ctrl label="Remove" onClick={() => void remove(p.id)}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3"><path d="M18 6 6 18M6 6l12 12" /></svg>
                          </Ctrl>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
              <div className="shrink-0 space-y-2 border-t border-edge p-3">
                <input
                  value={brief}
                  onChange={(e) => setBrief(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void buildDeck();
                  }}
                  disabled={building}
                  placeholder="Optional: angle or audience (e.g. for the board, focus on churn)"
                  className="w-full rounded-lg border border-edge bg-surface/60 px-2.5 py-1.5 text-[11.5px] text-foreground placeholder:text-faint focus:border-edge-strong focus:outline-none disabled:opacity-60"
                />
                <button
                  onClick={() => void buildDeck()}
                  disabled={building}
                  title="Assemble a grounded Minto deck from these pins"
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2.5 text-[12.5px] font-medium text-black transition-opacity hover:opacity-90 disabled:cursor-wait disabled:opacity-60"
                >
                  {building ? (
                    <>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="veta-spin h-4 w-4">
                        <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6" />
                      </svg>
                      Arranging &amp; grounding…
                    </>
                  ) : (
                    <>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                        <path d="M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5z" />
                      </svg>
                      Build deck from these {pins.length}
                    </>
                  )}
                </button>
                {buildError ? (
                  <p className="text-center text-[10px] text-amber-300/90">{buildError}</p>
                ) : (
                  <p className="text-center text-[10px] text-faint">Minto pyramid — every figure re-grounded from its SQL.</p>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
