"use client";

import { useState } from "react";
import type { DeckChart, DeckTable, Evidence, Slide, DeckSpec } from "@/engine/deck";
import { LineChart } from "../charts/LineChart";
import { BarChart } from "../charts/BarChart";
import { ChartView } from "../charts/ChartView";

const GOLD = "#e3b341";
const OBSIDIAN = "#0E0E10";
const PAPER = "#faf8f4";

const TEXTURE: Record<string, string> = {
  cover: "/deck-textures/ore-cover.png",
  divider: "/deck-textures/ore-divider.png",
  recommendation: "/deck-textures/ore-closing.png",
};

function usdAxis(n: number): string {
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n}`;
}

// ── Draft editing affordances ─────────────────────────────────────────────────

/** What SlideView can ask the viewer to persist — prose only, by construction. */
export interface SlideEditHandlers {
  onEditText: (field: "title" | "subtitle", value: string) => void;
  onEditBody: (lineIndex: number, value: string) => void;
}

/**
 * Click-to-edit prose. Renders the plain text until clicked, then an input /
 * textarea styled to disappear into the slide (inherits font + color). Enter or
 * blur saves; Esc cancels. Keyed remount on `value` keeps it reconciled with
 * the server's authoritative spec after a PATCH round-trips.
 */
function EditableText({
  value,
  editable,
  multiline,
  onSave,
  className,
}: {
  value: string;
  editable: boolean;
  multiline?: boolean;
  onSave: (v: string) => void;
  className?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [v, setV] = useState(value);
  if (!editable) return <>{value}</>;
  if (!editing)
    return (
      <span
        role="button"
        tabIndex={0}
        title="Click to edit"
        onClick={() => { setV(value); setEditing(true); }}
        onKeyDown={(e) => { if (e.key === "Enter") { setV(value); setEditing(true); } }}
        className={`cursor-text rounded-sm outline-none transition-shadow hover:ring-1 hover:ring-[#e3b341]/50 focus-visible:ring-1 focus-visible:ring-[#e3b341]/50 ${className ?? ""}`}
      >
        {value}
      </span>
    );
  const commit = () => {
    setEditing(false);
    if (v.trim() && v.trim() !== value) onSave(v);
  };
  const keys = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { e.preventDefault(); setEditing(false); }
    else if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); commit(); }
  };
  const common = {
    autoFocus: true,
    value: v,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setV(e.target.value),
    onBlur: commit,
    onKeyDown: keys,
    className: "w-full resize-none rounded-sm bg-transparent ring-1 ring-[#e3b341]/60 outline-none px-1 -mx-1",
    style: { font: "inherit", color: "inherit", letterSpacing: "inherit", lineHeight: "inherit" } as const,
  };
  return multiline ? <textarea {...common} rows={Math.max(2, Math.ceil(v.length / 60))} /> : <input {...common} />;
}

/**
 * The visual guarantee of the thesis: a grounded element (chart / table /
 * evidence) gets NO edit affordance — hovering it in draft mode shows a lock.
 */
function GroundedLock({ children, editable }: { children: React.ReactNode; editable: boolean }) {
  if (!editable) return <>{children}</>;
  return (
    <div className="group/lock relative">
      {children}
      <span
        title="Grounded by SQL — not editable"
        className="absolute right-1.5 top-1.5 hidden h-5 w-5 place-items-center rounded bg-black/50 text-neutral-300 group-hover/lock:grid"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3">
          <rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </svg>
      </span>
    </div>
  );
}

/** The per-slide trace back to the chat that produced it. In-app only — pptx never renders lineage. */
function LineageFooter({ slide }: { slide: Slide }) {
  const l = slide.lineage;
  if (!l) return null;
  const q = (l.question ?? "").trim();
  const n = l.citedSql?.length ?? 0;
  const label = `From: ${q.length > 60 ? `${q.slice(0, 60)}…` : q || "chat"} · ${n} ${n === 1 ? "query" : "queries"}`;
  return (
    <div className="mt-2 shrink-0 text-[10px] text-neutral-400">
      {l.conversationId ? (
        <a href={`/?conversation=${encodeURIComponent(l.conversationId)}`} className="transition-colors hover:text-neutral-600 hover:underline">
          {label}
        </a>
      ) : (
        <span>{label}</span>
      )}
    </div>
  );
}

/** A chart on its own dark inset panel — keeps the dark-themed chart legible on a light slide. */
function ChartPanel({ chart, height = 184 }: { chart: DeckChart; height?: number }) {
  return (
    <div className="rounded-lg p-3.5" style={{ backgroundColor: OBSIDIAN }}>
      <div className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-neutral-400">{chart.title}</div>
      {chart.spec ? (
        // The true re-grounded chart — any of the 10 types — drawn by the same ChartView the chat uses.
        <ChartView spec={chart.spec} height={height} bare />
      ) : chart.kind === "bar" ? (
        <BarChart
          data={chart.categories.map((c, i) => ({ label: c, value: chart.series[0]?.values[i] ?? 0, color: chart.series[0]?.color ?? GOLD }))}
          height={height}
          valueFormat={usdAxis}
          bare
        />
      ) : (
        <LineChart categories={chart.categories} series={chart.series} height={height} bare />
      )}
    </div>
  );
}

function TableBlock({ table }: { table: DeckTable }) {
  const numeric = new Set(table.numericColumns);
  return (
    <table className="w-full border-collapse text-[12.5px]">
      <thead>
        <tr className="border-b border-black/20">
          {table.columns.map((c, i) => (
            <th
              key={i}
              className={`px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-neutral-500 ${numeric.has(i) ? "text-right" : "text-left"}`}
            >
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, r) => (
          <tr key={r} className="border-b border-black/[0.06]">
            {row.map((cell, c) => (
              <td
                key={c}
                className={`px-2 py-[7px] ${numeric.has(c) ? "text-right font-mono tabular-nums text-neutral-900" : "text-neutral-700"}`}
              >
                {String(cell)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** The dark "hero number" card — the headline value, pulled from evidence (never typed). */
function HeroStat({ evidence }: { evidence: Evidence }) {
  return (
    <div className="rounded-lg px-5 py-4" style={{ backgroundColor: OBSIDIAN }}>
      <div className="font-mono text-[30px] font-bold leading-none" style={{ color: GOLD }}>
        {evidence.value}
      </div>
      <div className="mt-1.5 text-[11.5px] text-neutral-400">
        {evidence.label} · {evidence.rowCount} rows
      </div>
    </div>
  );
}

function darkBg(layout: string) {
  return {
    backgroundColor: OBSIDIAN,
    backgroundImage: TEXTURE[layout] ? `url(${TEXTURE[layout]})` : undefined,
    backgroundSize: "cover",
    backgroundPosition: "center",
  } as const;
}

/**
 * Render one slide in the hybrid system: dark cover/divider/closing, light data
 * slides. In draft mode (`editable` + handlers) prose becomes click-to-edit and
 * grounded elements grow a hover lock — decks without draft status render
 * exactly as before.
 */
export function SlideView({
  slide,
  spec,
  editable = false,
  edit,
}: {
  slide: Slide;
  spec: DeckSpec;
  editable?: boolean;
  edit?: SlideEditHandlers;
}) {
  const canEdit = editable && !!edit;
  const title = (
    <EditableText value={slide.title} editable={canEdit} onSave={(v) => edit?.onEditText("title", v)} />
  );
  const subtitle = slide.subtitle ? (
    <EditableText value={slide.subtitle} editable={canEdit} onSave={(v) => edit?.onEditText("subtitle", v)} />
  ) : null;
  const bodyLine = (b: string, i: number) => (
    <EditableText value={b} editable={canEdit} multiline onSave={(v) => edit?.onEditBody(i, v)} />
  );

  switch (slide.layout) {
    case "cover":
      return (
        <div className="flex h-full w-full flex-col justify-center px-16" style={darkBg("cover")}>
          <div className="text-[12px] font-semibold uppercase tracking-[0.28em]" style={{ color: GOLD }}>
            RavenStack
          </div>
          <h1 className="mt-4 max-w-[78%] text-[42px] font-semibold leading-[1.05] tracking-tight text-white">{title}</h1>
          {subtitle && <p className="mt-5 max-w-[66%] text-[16px] leading-snug text-neutral-300">{subtitle}</p>}
          {slide.evidence && (
            <GroundedLock editable={canEdit}>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="font-mono text-[24px] font-bold" style={{ color: GOLD }}>{slide.evidence.value}</span>
                <span className="text-[14px] text-neutral-400">{slide.evidence.label}</span>
              </div>
            </GroundedLock>
          )}
          <div className="mt-7 h-px w-72" style={{ backgroundColor: `${GOLD}59` }} />
          <div className="mt-4 font-mono text-[11.5px] text-neutral-500">Veta · grounded as of {spec.asOf}</div>
        </div>
      );

    case "divider":
      return (
        <div className="flex h-full w-full flex-col justify-center px-16" style={darkBg("divider")}>
          {slide.sectionNumber && (
            <div className="font-mono text-[68px] font-bold leading-none" style={{ color: GOLD }}>{slide.sectionNumber}</div>
          )}
          <h2 className="mt-3 text-[34px] font-semibold tracking-tight text-white">{title}</h2>
          {subtitle && <p className="mt-3 max-w-[62%] text-[15px] leading-snug text-neutral-400">{subtitle}</p>}
        </div>
      );

    case "context":
      return (
        <div className="flex h-full w-full flex-col px-14 py-10" style={{ backgroundColor: PAPER }}>
          <h2 className="max-w-[90%] text-[28px] font-semibold leading-tight tracking-tight text-neutral-900">{title}</h2>
          <div className="mt-6 flex flex-1 gap-10 min-h-0">
            <div className="flex w-[46%] flex-col justify-center gap-3 text-[14.5px] leading-relaxed text-neutral-700">
              {slide.body?.map((b, i) => <p key={`${i}-${b}`}>{bodyLine(b, i)}</p>)}
            </div>
            <div className="flex flex-1 flex-col justify-center">
              {slide.chart && (
                <GroundedLock editable={canEdit}>
                  <ChartPanel chart={slide.chart} height={196} />
                </GroundedLock>
              )}
            </div>
          </div>
        </div>
      );

    case "argument":
      return (
        <div className="flex h-full w-full flex-col px-14 py-9" style={{ backgroundColor: PAPER }}>
          <h2 className="max-w-[92%] text-[25px] font-semibold leading-[1.18] tracking-tight text-neutral-900">{title}</h2>
          <div className="mt-5 flex flex-1 gap-8 min-h-0">
            <div className="flex w-[40%] flex-col justify-center gap-4">
              {slide.body?.map((b, i) => (
                <p key={`${i}-${b}`} className="text-[13.5px] leading-relaxed text-neutral-600">{bodyLine(b, i)}</p>
              ))}
              {slide.evidence && (
                <GroundedLock editable={canEdit}>
                  <HeroStat evidence={slide.evidence} />
                </GroundedLock>
              )}
            </div>
            <div className="flex flex-1 flex-col justify-center gap-4 min-h-0 overflow-hidden">
              {slide.chart && (
                <GroundedLock editable={canEdit}>
                  <ChartPanel chart={slide.chart} height={170} />
                </GroundedLock>
              )}
              {slide.table && (
                <GroundedLock editable={canEdit}>
                  <TableBlock table={slide.table} />
                </GroundedLock>
              )}
            </div>
          </div>
          <LineageFooter slide={slide} />
        </div>
      );

    case "recommendation":
      return (
        <div className="flex h-full w-full flex-col justify-center px-16" style={darkBg("recommendation")}>
          <h2 className="text-[33px] font-semibold tracking-tight text-white">{title}</h2>
          <ul className="mt-7 flex flex-col gap-4">
            {slide.body?.map((b, i) => (
              <li key={`${i}-${b}`} className="flex items-start gap-3 text-[16px] leading-snug text-neutral-200">
                <span className="mt-[7px] h-2.5 w-2.5 shrink-0" style={{ backgroundColor: GOLD }} />
                <span className="max-w-[78%] flex-1">{bodyLine(b, i)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-9 h-px w-72" style={{ backgroundColor: `${GOLD}59` }} />
          <div className="mt-4 text-[12.5px]" style={{ color: GOLD }}>Veta · fundamentado no banco da RavenStack</div>
        </div>
      );

    default:
      return <div className="flex h-full w-full items-center justify-center" style={{ backgroundColor: OBSIDIAN }} />;
  }
}
