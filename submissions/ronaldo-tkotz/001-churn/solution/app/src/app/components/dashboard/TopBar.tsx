"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { TableInfo } from "@/engine/dashboard";
import { openConnect } from "./ConnectDialog";
import { openDataSource } from "./DataSourceDialog";

/** What the top bar states about the connected warehouse — all grounded facts. */
export interface DatasetContext {
  source: string; // "RavenStack"
  tableCount: number; // 8
  asOf: string; // the dataset's "today", YYYY-MM-DD
  firstDate: string; // first day of data
  lastDate: string; // last day of data
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-06-12" → "Jun 2026". */
function monthYear(iso: string): string {
  const [y, m] = iso.split("-").map(Number);
  return m && y ? `${MONTHS[m - 1]} ${y}` : iso;
}

/** "2026-06-12" → "Jun 12, 2026". */
function prettyDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return m && d && y ? `${MONTHS[m - 1]} ${d}, ${y}` : iso;
}

const compact = (n: number): string => (n >= 1000 ? `${Math.round(n / 1000)}k` : String(n));

/**
 * The connection status pill. Clicking it opens the data inventory — the full
 * table list with real row counts, plus the dataset frame. The inventory lives
 * here (with "Connected") rather than on the left rail, so the left is free for
 * the conversation workspace. Read-only facts, grounded — no decoration.
 */
function ConnectedStatus({ tables, ctx }: { tables: TableInfo[]; ctx: DatasetContext }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  // Close on outside-click + Esc; listeners live only while open. Esc returns
  // focus to the trigger so keyboard users aren't stranded. The wrapper-ref check
  // (which contains the trigger) avoids the mousedown-then-click reopen flicker.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={wrapRef} className="relative">
      <button
        ref={triggerRef}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="true"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`Connected to ${ctx.source}, ${ctx.tableCount} tables. Show data inventory.`}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-colors ${
          open
            ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200"
            : "border-emerald-400/25 bg-emerald-400/5 text-emerald-300/90 hover:border-emerald-400/40"
        }`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        Connected
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div
          id={panelId}
          role="dialog"
          aria-label="Data inventory"
          className="absolute right-0 top-full z-50 mt-2 max-h-[70vh] w-72 overflow-y-auto rounded-xl border border-edge bg-panel p-3 shadow-xl shadow-black/50"
        >
          <div className="mb-2 border-b border-edge pb-2.5">
            <div className="flex items-center gap-2 text-[12px]">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span className="font-medium text-foreground">{ctx.source}</span>
              <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-emerald-300/90">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> live
              </span>
            </div>
            <div className="mt-1.5 font-mono text-[10.5px] leading-relaxed text-faint">
              {monthYear(ctx.firstDate)} – {monthYear(ctx.lastDate)} · as of {prettyDate(ctx.asOf)}
            </div>
          </div>

          <div className="mb-1.5 flex items-center gap-2 text-[10px] font-medium uppercase tracking-wider text-faint">
            Data inventory
            <span className="rounded-full border border-edge px-1.5 py-0.5 text-[9px] normal-case tracking-normal">
              {tables.length} tables
            </span>
          </div>
          <ul className="space-y-0.5">
            {tables.map((t) => (
              <li key={t.name} className="flex items-center gap-2 py-1 text-[12px]">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400/80" />
                <span className="font-mono text-muted">{t.name}</span>
                <span className="ml-auto font-mono text-[10.5px] text-faint tabular-nums">{compact(t.rows)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function TopBar({ ctx, tables }: { ctx: DatasetContext; tables: TableInfo[] }) {
  // The "Connect" affordance is a builder tool (it opens the MCP/agent-connect docs).
  // Judges hit a warehouse that is ALREADY connected, so it only reads as confusing to
  // them — gate it behind a dev-only flag (off in production; set NEXT_PUBLIC_VETA_DEV_TOOLS=1
  // locally to keep it). The "Connected" status pill stays for everyone.
  const devTools = process.env.NEXT_PUBLIC_VETA_DEV_TOOLS === "1";
  return (
    <header className="flex shrink-0 items-center gap-3 border-b border-edge bg-surface px-4 py-2.5">
      {/* Dataset context — grounded facts about what's connected, and the switch
          point: click to pick a different warehouse or upload your own. */}
      <button
        onClick={() => openDataSource()}
        aria-label={`Data source: ${ctx.source}. Switch or upload a warehouse.`}
        className="group flex min-w-0 items-center gap-2 rounded-lg px-1.5 py-1 text-[12px] text-muted transition-colors hover:bg-panel"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 shrink-0 text-faint">
          <ellipse cx="12" cy="5" rx="8" ry="3" />
          <path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5" />
          <path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
        </svg>
        <span className="truncate font-medium text-foreground">{ctx.source}</span>
        <span className="text-faint">·</span>
        <span className="font-mono tabular-nums">{ctx.tableCount} tables</span>
        {ctx.firstDate && (
          <>
            <span className="hidden text-faint sm:inline">·</span>
            <span className="hidden font-mono tabular-nums sm:inline">
              {monthYear(ctx.firstDate)} – {monthYear(ctx.lastDate)}
            </span>
          </>
        )}
        {ctx.asOf && (
          <>
            <span className="hidden text-faint md:inline">·</span>
            <span className="hidden text-faint md:inline">as of {prettyDate(ctx.asOf)}</span>
          </>
        )}
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3 shrink-0 text-faint opacity-0 transition-opacity group-hover:opacity-100">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <div className="ml-auto flex items-center gap-2.5">
        <ConnectedStatus tables={tables} ctx={ctx} />
        {devTools && (
          <button
            onClick={() => openConnect()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-edge bg-panel px-3 py-1.5 text-[12.5px] font-medium text-foreground transition-colors hover:border-edge-strong"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
              <path d="m8 9-3 3 3 3M16 9l3 3-3 3M13 7l-2 10" />
            </svg>
            Connect
          </button>
        )}
      </div>
    </header>
  );
}
