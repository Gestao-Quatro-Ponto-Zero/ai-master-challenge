"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function CollapsibleCard({
  icon,
  title,
  hint,
  defaultOpen = false,
  children,
}: {
  icon?: React.ReactNode;
  title: string;
  hint?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-[var(--shadow-metric)]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors duration-150 text-left"
        aria-expanded={open}
      >
        {icon && <div className="text-slate-500">{icon}</div>}
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-slate-900 text-sm">{title}</div>
          {hint && (
            <div className="text-[11px] text-slate-500 truncate">{hint}</div>
          )}
        </div>
        <ChevronDown
          className={cn("h-4 w-4 text-slate-400", open && "rotate-180")}
        />
      </button>
      {open && <div className="border-t border-slate-100 p-4">{children}</div>}
    </section>
  );
}

export function RecommendationCard({
  items,
}: {
  items: { title: string; body: string }[];
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-[var(--shadow-metric)]">
      <ol className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex gap-3">
            <div className="h-6 w-6 shrink-0 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold grid place-items-center border border-blue-100">
              {i + 1}
            </div>
            <div className="flex-1">
              <div className="font-medium text-slate-900 text-sm">
                {item.title}
              </div>
              <p className="text-[13px] text-slate-600 mt-0.5 leading-relaxed">
                {item.body}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export interface FocusPerson {
  name: string;
  subtitle?: string;
  metrics?: string;
  context?: string;
}

export function PeopleFocus({
  critical,
  attention,
  healthy,
  healthyLabel,
  emptyAttention,
}: {
  critical: FocusPerson[];
  attention: FocusPerson[];
  healthy: string[];
  healthyLabel?: string;
  emptyAttention?: string;
}) {
  const noneNeedsAttention = critical.length === 0 && attention.length === 0;
  return (
    <div className="space-y-2">
      {noneNeedsAttention ? (
        <div className="text-sm text-emerald-700 py-2 flex items-center gap-2">
          <span className="text-base">✅</span>
          {emptyAttention ?? "Ninguém precisa de atenção agora."}
        </div>
      ) : (
        <>
          {critical.map((row) => (
            <FocusRow key={row.name} row={row} level="critical" />
          ))}
          {attention.map((row) => (
            <FocusRow key={row.name} row={row} level="attention" />
          ))}
        </>
      )}
      {healthy.length > 0 && (
        <div className="text-xs text-slate-500 flex items-start gap-2 pt-2 px-3">
          <span className="text-emerald-500 shrink-0">✅</span>
          <span>
            <span className="font-medium text-slate-700">
              {healthy.join(" · ")}
            </span>{" "}
            <span className="text-slate-500">
              {healthyLabel ?? "operando dentro do esperado"}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}

function FocusRow({
  row,
  level,
}: {
  row: FocusPerson;
  level: "critical" | "attention";
}) {
  const styles =
    level === "critical"
      ? "bg-red-50/70 border-red-200"
      : "bg-amber-50/60 border-amber-200";
  const icon = level === "critical" ? "🔴" : "⚠️";
  return (
    <div
      className={cn(
        "flex items-start gap-3 py-3 px-3.5 rounded-lg border",
        styles,
      )}
    >
      <span className="text-base leading-none pt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="font-semibold text-slate-900 text-sm">
            {row.name}
          </span>
          {row.subtitle && (
            <span className="text-xs text-slate-500">{row.subtitle}</span>
          )}
        </div>
        {row.metrics && (
          <div className="text-xs text-slate-700 mt-0.5 tabular-nums">
            {row.metrics}
          </div>
        )}
        {row.context && (
          <div className="text-xs text-slate-600 italic mt-1 leading-snug">
            {row.context}
          </div>
        )}
      </div>
    </div>
  );
}
