"use client";

import { useState } from "react";
import Link from "next/link";
import type { DeckSummary } from "@/engine/deck";

/** A gallery card: the summary plus its lifecycle state (absent = legacy = published). */
export type DeckCard = DeckSummary & { status?: "draft" | "published" };

/** A built deck's "as of" + built date, formatted compactly. */
function fmtDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/**
 * The Deck Library grid — the user's built decks, each reopenable + exportable +
 * removable. Delete is optimistic (drop from the grid, then DELETE /api/decks/{id});
 * a failure restores the card so the list never silently loses a deck.
 */
export function DeckLibrary({ initialDecks }: { initialDecks: DeckCard[] }) {
  const [decks, setDecks] = useState<DeckCard[]>(initialDecks);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const remove = async (id: string) => {
    setConfirmId(null);
    const prev = decks;
    setDecks((d) => d.filter((x) => x.id !== id));
    try {
      const res = await fetch(`/api/decks/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (!res.ok) setDecks(prev); // restore — nothing was actually removed
    } catch {
      setDecks(prev);
    }
  };

  if (decks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-edge bg-panel/40 px-6 py-20 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-xl bg-surface text-faint">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
            <path d="M3 7l9-4 9 4-9 4-9-4Z" /><path d="M3 12l9 4 9-4" /><path d="M3 17l9 4 9-4" />
          </svg>
        </span>
        <p className="text-[13px] font-medium text-muted">No decks in your library yet</p>
        <p className="max-w-[360px] text-[12px] leading-snug text-faint">
          Pin grounded answers in a conversation, then <span className="text-muted">Build deck from these</span> in the
          right-rail <span className="text-muted">Deck</span> tab — every deck you build lands here, ready to reopen or export.
        </p>
        <p className="mt-1 max-w-[360px] text-[11px] leading-snug text-faint">
          Looking for the auto-generated deck? That&apos;s <span className="text-accent">Veta Executive Deck</span> on the left — it&apos;s always live.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {decks.map((d) => (
        <div
          key={d.id}
          className="group flex flex-col rounded-xl border border-edge bg-panel p-4 transition-colors hover:border-edge-strong"
        >
          <Link href={`/deck/${encodeURIComponent(d.id)}`} className="flex flex-1 flex-col">
            {/* Mini cover — title + apex, matching the deck's editorial tone. */}
            <div className="relative mb-3 overflow-hidden rounded-lg border border-edge bg-gradient-to-br from-accent-soft/50 via-surface to-background p-3.5">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-faint">
                <span className="h-1.5 w-1.5 rotate-45 bg-accent" /> RavenStack
              </div>
              <div className="mt-2 line-clamp-2 text-[14px] font-semibold leading-tight tracking-tight text-foreground">
                {d.title}
              </div>
            </div>
            {d.governingThought && (
              <p className="mb-3 line-clamp-3 text-[11.5px] leading-snug text-muted">{d.governingThought}</p>
            )}
            <div className="mt-auto flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[10.5px] text-faint">
              <span>{d.slideCount} slides</span>
              <span className="text-edge-strong">·</span>
              <span className="inline-flex items-center gap-1">
                <span className="h-1 w-1 rounded-full bg-emerald-400/80" />
                {d.citedCount} quer{d.citedCount === 1 ? "y" : "ies"} cited
              </span>
              <span className="text-edge-strong">·</span>
              {d.status === "draft" ? (
                <span className="rounded-full border border-accent/40 px-1.5 py-px font-medium text-accent">draft</span>
              ) : (
                <span>published</span>
              )}
              {d.asOf && (
                <>
                  <span className="text-edge-strong">·</span>
                  <span>as of {d.asOf}</span>
                </>
              )}
            </div>
          </Link>

          {/* Actions — open is the card body; this row is export + remove. */}
          <div className="mt-3.5 flex items-center gap-2 border-t border-edge pt-3">
            <Link
              href={`/deck/${encodeURIComponent(d.id)}`}
              className="inline-flex items-center gap-1.5 rounded-md bg-accent px-2.5 py-1 text-[11px] font-medium text-black transition-opacity hover:opacity-90"
            >
              Open
            </Link>
            <a
              href={`/api/deck/${encodeURIComponent(d.id)}/pptx`}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-edge px-2.5 py-1 text-[11px] font-medium text-muted transition-colors hover:border-edge-strong hover:text-foreground"
            >
              .pptx
            </a>
            <span className="ml-auto text-[10px] text-faint">{fmtDate(d.builtAt)}</span>
            {confirmId === d.id ? (
              <span className="flex items-center gap-1.5">
                <button onClick={() => void remove(d.id)} title="Confirm delete" className="text-[10px] font-medium text-red-400 hover:text-red-300">
                  Delete?
                </button>
                <button onClick={() => setConfirmId(null)} title="Cancel" className="text-[10px] text-faint hover:text-foreground">
                  ✕
                </button>
              </span>
            ) : (
              <button
                onClick={() => setConfirmId(d.id)}
                title="Remove this deck from the library"
                className="grid h-5 w-5 place-items-center rounded text-faint transition-colors hover:text-red-400"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
                  <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                </svg>
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
