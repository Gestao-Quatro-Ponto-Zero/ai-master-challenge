"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { channelLabel, ticketTypeLabel } from "@/lib/labels";
import { useHydrated } from "@/lib/use-hydrated";

type InsightsPayload = {
  generated_at?: string;
  data_source?: string;
  ticket_status_summary?: {
    total_tickets: number;
    open_tickets: number;
    pending_tickets: number;
    closed_tickets: number;
    resolved_tickets: number;
    resolved_definition?: string;
  };
  channel_bottlenecks?: Array<{
    channel: string;
    avg_resolution_hours: number;
    median_resolution_hours: number;
    ticket_volume: number;
  }>;
  ticket_type_analysis?: Array<{
    ticket_type: string;
    ticket_volume: number;
    share_pct: number;
    avg_resolution_hours: number;
  }>;
  customer_satisfaction?: {
    positive_count: number;
    neutral_count: number;
    negative_count: number;
    unrated_count?: number;
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
    unrated_pct?: number;
    sample_size: number;
    total_tickets?: number;
  };
  deflection_metrics?: {
    top_resolved_questions?: string[];
  };
};

/* Icons removed — sidebar owns navigation icons now */

/* ── System color scheme hook ───────────────────────────────────────── */
function subscribeColorScheme(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => {};
  }
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", onStoreChange);
  return () => mq.removeEventListener("change", onStoreChange);
}

function getColorSchemeSnapshot() {
  if (typeof window === "undefined") {
    return false;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function getColorSchemeServerSnapshot() {
  return false;
}

function useColorScheme() {
  return useSyncExternalStore(
    subscribeColorScheme,
    getColorSchemeSnapshot,
    getColorSchemeServerSnapshot
  );
}

/* ── Satisfaction bar colors (readable in both themes) ──────────────── */
const SAT_COLORS: Record<string, string> = {
  Positivo:       "#10b981",
  Negativo:       "#ef4444",
  Neutro:         "#f59e0b",
  "Sem avaliação": "#94a3b8",
};

type KpiCardProps = {
  label: string;
  value: string;
  note?: string;
};

function KpiCard({ label, value, note }: KpiCardProps) {
  return (
    <article className="ad-card p-5">
      <p className="ad-label">{label}</p>
      <p className="ad-kpi mt-3">{value}</p>
      {note ? <p className="mt-2 text-xs" style={{ color: "var(--ad-text-muted)" }}>{note}</p> : null}
    </article>
  );
}

export default function AdminDashboardPage() {
  const [insights, setInsights] = useState<InsightsPayload | null>(null);
  const [error, setError]       = useState<string>("");
  const isHydrated              = useHydrated();
  const isDark                  = useColorScheme();

  /* Chart colour tokens — adapt to OS theme */
  const C = useMemo(() => isDark ? {
    primary: "#4a7fa8",   /* lighter navy for dark bg */
    gold:    "#c9a96a",   /* lighter gold for dark bg */
    grid:    "rgba(255,255,255,0.06)",
    label:   "#a1a1aa",
    cursor:  "rgba(255,255,255,0.04)",
    tooltip: { background: "#18181b", border: "1px solid rgba(255,255,255,0.10)", borderRadius: 8 },
  } : {
    primary: "#021E35",   /* brand navy */
    gold:    "#B48E5A",   /* brand gold */
    grid:    "rgba(0,0,0,0.06)",
    label:   "#64748b",
    cursor:  "rgba(0,0,0,0.04)",
    tooltip: { background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8 },
  }, [isDark]);

  useEffect(() => {
    let active = true;
    fetch("/api/insights")
      .then(async (r) => {
        const payload = (await r.json()) as InsightsPayload & { error?: string };
        if (!active) return;
        if (!r.ok) { setError(payload.error ?? "Falha ao carregar insights"); return; }
        setInsights(payload);
      })
      .catch(() => { if (active) setError("Falha ao carregar insights"); });
    return () => { active = false; };
  }, []);

  const statusSummary = insights?.ticket_status_summary;

  const channelData = useMemo(() =>
    (insights?.channel_bottlenecks ?? []).map((i) => ({ ...i, canal_pt: channelLabel(i.channel) })),
    [insights]);

  const ticketTypeData = useMemo(() =>
    (insights?.ticket_type_analysis ?? []).map((i) => ({ ...i, tipo_pt: ticketTypeLabel(i.ticket_type) })),
    [insights]);

  const satisfactionData = useMemo(() => {
    const s = insights?.customer_satisfaction;
    if (!s) return [];
    return [
      { sentimento: "Positivo",      percentual: s.positive_pct, volume: s.positive_count },
      { sentimento: "Negativo",      percentual: s.negative_pct, volume: s.negative_count },
      { sentimento: "Neutro",        percentual: s.neutral_pct,  volume: s.neutral_count  },
      { sentimento: "Sem avaliação", percentual: s.unrated_pct ?? 0, volume: s.unrated_count ?? 0 },
    ];
  }, [insights]);

  const topResolvedQuestions = useMemo(
    () => insights?.deflection_metrics?.top_resolved_questions ?? [],
    [insights]);

  const tooltipStyle = { contentStyle: C.tooltip, cursor: { fill: C.cursor } };
  const axisProps    = { stroke: "none", tick: { fontSize: 11, fill: C.label } };

  const emptyChart = (msg: string) => (
    <div className="flex h-full items-center justify-center text-sm" style={{ color: C.label }}>{msg}</div>
  );
  const skeleton = (
    <div className="h-full w-full animate-pulse rounded-lg"
      style={{ background: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)" }} />
  );

  return (
    <>
        {/* ── Header ───────────────────────────────────────────────────── */}
        <header className="admin-header">
          <nav style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
            <span style={{ color: "var(--ad-text-dim)" }}>Painel</span>
            <span style={{ color: "var(--ad-text-dim)" }}>/</span>
            <span style={{ color: "var(--ad-text)", fontWeight: 500 }}>Visão geral</span>
          </nav>
        </header>

        {/* Content */}
        <main className="admin-content">
          {/* ── Page title ─────────────────────────────────────────────── */}
          <div style={{ marginBottom: "1.75rem" }}>
            <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.03em", color: "var(--ad-text)", lineHeight: 1.15 }}>
              Visão Geral
            </h1>
            <p style={{ margin: "0.375rem 0 0", fontSize: "0.9375rem", color: "var(--ad-text-muted)" }}>
              Análise de performance de suporte · 8.469 tickets
            </p>
          </div>

          {error ? (
            <div style={{
              marginBottom: "1rem", padding: "0.75rem 1rem", borderRadius: "0.5rem",
              border: "1px solid var(--ad-danger)", background: "rgba(239,68,68,0.08)",
              color: "#fca5a5", fontSize: "0.875rem",
            }}>
              {error}
            </div>
          ) : null}

          {/* ── KPI cards ──────────────────────────────────────────────── */}
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              label="Tickets abertos"
              value={statusSummary?.open_tickets?.toLocaleString("pt-BR") ?? "—"}
              note="Aguardando atendimento"
            />
            <KpiCard
              label="Tickets pendentes"
              value={statusSummary?.pending_tickets?.toLocaleString("pt-BR") ?? "—"}
              note="Aguardando resposta do cliente"
            />
            <KpiCard
              label="Tickets fechados"
              value={statusSummary?.closed_tickets?.toLocaleString("pt-BR") ?? "—"}
              note="Encerrados na base"
            />
            <KpiCard
              label="Tickets resolvidos"
              value={statusSummary?.resolved_tickets?.toLocaleString("pt-BR") ?? "—"}
              note={statusSummary?.resolved_definition ?? "Fechados com CSAT ≥ 4"}
            />
          </section>

          {/* ── Charts ─────────────────────────────────────────────────── */}
          <section className="mt-4 grid gap-4 xl:grid-cols-3">

            {/* Canal */}
            <article className="ad-card p-5">
              <p style={{ margin: "0 0 0.25rem", fontSize: "1.25rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>Gargalo por canal</p>
              <p className="mb-4 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                Tempo médio de resolução (h)
              </p>
              <div className="h-64 w-full">
                {isHydrated && channelData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart layout="vertical" data={channelData} margin={{ top: 12, right: 28, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="4 4" stroke={C.grid} horizontal={false} />
                      <XAxis type="number" {...axisProps} />
                      <YAxis type="category" dataKey="canal_pt" width={88} {...axisProps} />
                      <Tooltip {...tooltipStyle} formatter={(value) => [`${Number(value ?? 0).toFixed(1)}h`, "Média"]} />
                      <Bar dataKey="avg_resolution_hours" fill={C.primary} radius={[0, 4, 4, 0]}>
                        <LabelList dataKey="avg_resolution_hours" position="right"
                          style={{ fontSize: 13, fill: C.label, fontWeight: 700 }}
                          formatter={(value) => `${Number(value ?? 0).toFixed(1)}h`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : isHydrated ? emptyChart("Sem dados.") : skeleton}
              </div>
            </article>

            {/* Tipo */}
            <article className="ad-card p-5">
              <p style={{ margin: "0 0 0.25rem", fontSize: "1.25rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>Tipo de ticket</p>
              <p className="mb-4 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                Participação % por tipo
              </p>
              <div className="h-64 w-full">
                {isHydrated && ticketTypeData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart layout="vertical" data={ticketTypeData} margin={{ top: 12, right: 28, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="4 4" stroke={C.grid} horizontal={false} />
                      <XAxis type="number" {...axisProps} unit="%" />
                      <YAxis type="category" dataKey="tipo_pt" width={132} {...axisProps} />
                      <Tooltip {...tooltipStyle} formatter={(value) => [`${Number(value ?? 0).toFixed(1)}%`, "Participação"]} />
                      <Bar dataKey="share_pct" fill={C.gold} radius={[0, 4, 4, 0]}>
                        <LabelList dataKey="share_pct" position="right"
                          style={{ fontSize: 13, fill: C.label, fontWeight: 700 }}
                          formatter={(value) => `${Number(value ?? 0).toFixed(1)}%`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : isHydrated ? emptyChart("Sem dados.") : skeleton}
              </div>
            </article>

            {/* Satisfação */}
            <article className="ad-card p-5">
              <p style={{ margin: "0 0 0.25rem", fontSize: "1.25rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>Satisfação do cliente</p>
              <p className="mb-1 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                % sobre {insights?.customer_satisfaction?.total_tickets?.toLocaleString("pt-BR") ?? "—"} tickets
              </p>
              <p className="mb-4 text-xs" style={{ color: "var(--ad-text-dim)" }}>
                Coluna: Customer Satisfaction Rating (1–5) · Sem avaliação = Open/Pending
              </p>
              <div className="h-52 w-full">
                {isHydrated && satisfactionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart data={satisfactionData} margin={{ top: 24, right: 8, left: 4, bottom: 36 }}>
                      <CartesianGrid strokeDasharray="4 4" stroke={C.grid} vertical={false} />
                      <XAxis dataKey="sentimento" {...axisProps} angle={-15} textAnchor="end" interval={0}
                        tick={{ fontSize: 10, fill: C.label }} />
                      <YAxis {...axisProps} unit="%" domain={[0, 100]} />
                      <Tooltip
                        {...tooltipStyle}
                        formatter={(value) => [`${Number(value ?? 0).toFixed(1)}%`, "Percentual"]}
                      />
                      <Bar dataKey="percentual" radius={[4, 4, 0, 0]}>
                        {satisfactionData.map((e) => (
                          <Cell key={e.sentimento} fill={SAT_COLORS[e.sentimento] ?? C.primary} />
                        ))}
                        <LabelList dataKey="percentual" position="top"
                          style={{ fontSize: 13, fill: C.label, fontWeight: 700 }}
                          formatter={(value) => `${Number(value ?? 0).toFixed(1)}%`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : isHydrated ? emptyChart("Sem dados.") : skeleton}
              </div>
            </article>
          </section>

          {/* ── EDA Insights ───────────────────────────────────────────── */}
          <section className="mt-6">
            <h2 style={{ margin: "0 0 0.25rem", fontSize: "1.5rem", fontWeight: 800, color: "var(--ad-text)", letterSpacing: "-0.025em" }}>Análise Exploratória</h2>
            <p style={{ margin: "0 0 1.25rem", fontSize: "0.875rem", color: "var(--ad-text-muted)" }}>Baseado em 2.769 tickets fechados</p>

            <div className="grid gap-3 lg:grid-cols-3">

              {/* 1 — Piores combinações */}
              <article className="ad-card" style={{ padding: "1.75rem" }}>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.6875rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ad-text-dim)" }}>Piores tempos de resolução</p>
                <p style={{ margin: "0 0 0.375rem", fontSize: "1.375rem", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-0.025em", color: "var(--ad-text)" }}>
                  Chat técnico é 3× mais lento — triagem de prioridade inexistente
                </p>
                <p className="mb-4 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                  Combinação Chat + Técnico + Low chega a 14,6 h médias de resolução
                </p>
                <table className="w-full">
                  <thead>
                    <tr className="ad-tr text-left">
                      {["Canal", "Tipo", "Prior.", "Média"].map((h, i) => (
                        <th key={h}
                          className={`pb-2 pr-3 text-[10px] font-medium uppercase tracking-wider${i === 3 ? " text-right pr-0" : ""}`}
                          style={{ color: "var(--ad-text-dim)" }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { canal: "Chat",   tipo: "Técnico",   prio: "Low",      h: "14,6 h" },
                      { canal: "Chat",   tipo: "Reembolso", prio: "High",     h: "14,1 h" },
                      { canal: "Social", tipo: "Técnico",   prio: "Medium",   h: "14,1 h" },
                      { canal: "Social", tipo: "Produto",   prio: "Critical", h: "13,9 h" },
                      { canal: "Phone",  tipo: "Produto",   prio: "Medium",   h: "13,8 h" },
                    ].map((r, i) => (
                      <tr key={i} className="ad-tr text-sm" style={{ color: "var(--ad-text-muted)" }}>
                        <td className="py-2 pr-3">{r.canal}</td>
                        <td className="py-2 pr-3">{r.tipo}</td>
                        <td className="py-2 pr-3 text-xs" style={{ color: "var(--ad-text-dim)" }}>{r.prio}</td>
                        <td className="py-2 text-right font-semibold tabular-nums" style={{ color: "var(--ad-text)" }}>{r.h}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <hr className="ad-divider mt-5" />
                <p className="mt-4 text-xs leading-relaxed" style={{ color: "var(--ad-text-muted)" }}>
                  <span className="font-medium" style={{ color: "var(--ad-warning)" }}>Atenção:</span>{" "}
                  tickets Low demoram mais (11,94 h) que Critical (11,44 h) — triagem sem SLA por prioridade.
                </p>
              </article>

              {/* 2 — Drivers de CSAT */}
              <article className="ad-card" style={{ padding: "1.75rem" }}>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.6875rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ad-text-dim)" }}>O que impacta satisfação (CSAT)?</p>
                <p style={{ margin: "0 0 0.375rem", fontSize: "1.375rem", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-0.025em", color: "var(--ad-text)" }}>
                  CSAT desconectado da operação — satisfação não responde ao atendimento
                </p>
                <p className="mb-4 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                  Nenhuma variável operacional explica o CSAT neste dataset
                </p>
                <div className="space-y-2">
                  {[
                    { label: "Tempo de resolução × CSAT", stat: "r = −0,019 · p = 0,33" },
                    { label: "Canal (ANOVA)",             stat: "F = 1,28 · p = 0,28"   },
                    { label: "Tipo de ticket (ANOVA)",    stat: "F = 0,55 · p = 0,70"   },
                    { label: "Prioridade (ANOVA)",        stat: "F = 0,57 · p = 0,63"   },
                    { label: "Random Forest (R² CV)",     stat: "R² = −0,08"             },
                  ].map((r) => (
                    <div key={r.label} className="flex items-center justify-between gap-3 border-b py-2"
                      style={{ borderColor: "var(--ad-border)" }}>
                      <span className="text-xs" style={{ color: "var(--ad-text-muted)" }}>{r.label}</span>
                      <span className="shrink-0 font-mono text-[11px]" style={{ color: "var(--ad-text-dim)" }}>{r.stat}</span>
                    </div>
                  ))}
                </div>
                <hr className="ad-divider mt-5" />
                <p className="mt-4 text-xs leading-relaxed" style={{ color: "var(--ad-text-muted)" }}>
                  <span className="font-medium" style={{ color: "var(--ad-text)" }}>Diagnóstico:</span>{" "}
                  CSAT uniforme (553·549·580·543·544 para notas 1–5) — dado sintético sem correlação real.
                  Único sinal fraco: <em>Fitbit Versa</em> (CSAT 2,54 vs. média 2,99).
                </p>
              </article>

              {/* 3 — Desperdício */}
              <article className="ad-card" style={{ padding: "1.75rem" }}>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.6875rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ad-text-dim)" }}>Desperdício recuperável</p>
                <p style={{ margin: "0 0 0.375rem", fontSize: "1.375rem", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-0.025em", color: "var(--ad-success)" }}>
                  R$ 921 mil em eficiência represados na operação hoje
                </p>
                <p className="mb-4 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                  26,4% do tempo total recuperável sem nenhum novo sistema
                </p>
                <div className="space-y-3">
                  {[
                    { label: "Excesso na amostra Closed",    val: "8.601 h",  sub: "R$ 301k estimados" },
                    { label: "Projeção para 8.469 tickets",  val: "26.307 h", sub: "R$ 921k estimados" },
                    { label: "Quick win — 278 tickets P90+", val: "3.108 h",  sub: "R$ 109k com intervenção pontual" },
                  ].map((r) => (
                    <div key={r.label} className="flex items-start justify-between gap-3 border-b pb-3"
                      style={{ borderColor: "var(--ad-border)" }}>
                      <div>
                        <p className="text-xs" style={{ color: "var(--ad-text-muted)" }}>{r.label}</p>
                        <p className="text-[10px]" style={{ color: "var(--ad-text-dim)" }}>{r.sub}</p>
                      </div>
                      <span className="shrink-0 font-mono text-sm font-bold tabular-nums"
                        style={{ color: "var(--ad-success)" }}>{r.val}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-5">
                  <p className="ad-label mb-2">Maior desperdício por segmento</p>
                  {[
                    { seg: "Phone × Técnico",      val: "539 h · R$ 18,9k" },
                    { seg: "Email × Reembolso",    val: "528 h · R$ 18,5k" },
                    { seg: "Email × Cancelamento", val: "520 h · R$ 18,2k" },
                  ].map((r, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 border-b"
                      style={{ borderColor: "var(--ad-border)" }}>
                      <span className="text-xs" style={{ color: "var(--ad-text-muted)" }}>{r.seg}</span>
                      <span className="font-mono text-xs font-semibold" style={{ color: "var(--ad-text)" }}>{r.val}</span>
                    </div>
                  ))}
                  <p className="mt-3 text-[10px]" style={{ color: "var(--ad-text-dim)" }}>
                    Excesso = tempo acima da mediana do segmento (canal × tipo). Custo-hora: R$ 35.
                  </p>
                </div>
              </article>
            </div>
          </section>

          {/* ── Raw data table ─────────────────────────────────────────── */}
          <section className="ad-card mt-4 overflow-x-auto p-5">
            <p className="ad-label mb-4">Dados brutos — tipo de ticket</p>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--ad-border)" }}>
                  {["Tipo", "Volume", "Participação", "Tempo médio resolução"].map((h, i) => (
                    <th key={h}
                      className={`pb-3 text-[10px] font-medium uppercase tracking-wider${i > 0 ? " text-right" : ""}`}
                      style={{ color: "var(--ad-text-dim)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(insights?.ticket_type_analysis ?? []).map((row) => (
                  <tr key={row.ticket_type} style={{ borderBottom: "1px solid var(--ad-border)" }}>
                    <td className="py-2.5 font-medium" style={{ color: "var(--ad-text)" }}>
                      {ticketTypeLabel(row.ticket_type)}
                    </td>
                    <td className="py-2.5 text-right tabular-nums" style={{ color: "var(--ad-text-muted)" }}>
                      {row.ticket_volume.toLocaleString("pt-BR")}
                    </td>
                    <td className="py-2.5 text-right tabular-nums" style={{ color: "var(--ad-text-muted)" }}>
                      {row.share_pct}%
                    </td>
                    <td className="py-2.5 text-right tabular-nums font-mono" style={{ color: "var(--ad-text-muted)" }}>
                      {row.avg_resolution_hours}h
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td className="pt-3 font-semibold" style={{ color: "var(--ad-text)" }}>Total</td>
                  <td className="pt-3 text-right font-semibold tabular-nums" style={{ color: "var(--ad-text)" }}>
                    {(insights?.ticket_type_analysis ?? []).reduce((s, r) => s + r.ticket_volume, 0).toLocaleString("pt-BR")}
                  </td>
                  <td className="pt-3 text-right font-semibold" style={{ color: "var(--ad-text)" }}>100%</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </section>

          {/* ── Deflection ─────────────────────────────────────────────── */}
          <section className="ad-card mt-4 p-5">
            <p className="ad-label mb-3">Perguntas resolvidas sem abrir ticket</p>
            <ul className="space-y-1.5">
              {topResolvedQuestions.length > 0 ? (
                topResolvedQuestions.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm" style={{ color: "var(--ad-text-muted)" }}>
                    <span style={{ color: "var(--ad-success)" }}>·</span>
                    {item}
                  </li>
                ))
              ) : (
                <li className="text-sm" style={{ color: "var(--ad-text-dim)" }}>Sem eventos suficientes ainda.</li>
              )}
            </ul>
          </section>
        </main>
    </>
  );
}
