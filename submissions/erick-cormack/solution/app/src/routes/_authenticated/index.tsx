import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { useMemo } from "react";
import { PageHeader } from "@/components/AppShell";
import { CurvaChart } from "@/components/lead/CurvaChart";
import { ResumoDialog } from "@/components/lead/ResumoDialog";
import { FilasChart, RegiaoChart, ScoreChart } from "@/components/lead/HomeCharts";
import { ErrorState, LoadingState } from "@/components/lead/States";
import { useDeals } from "@/hooks/useDeals";
import { useParametros } from "@/hooks/useParametros";
import { calcResumo } from "@/lib/homeStats";
import { formatNumber, formatPct, formatUSD, formatUSDCompact } from "@/lib/format";

export const Route = createFileRoute("/_authenticated/")({
  head: () => ({
    meta: [
      { title: "Lead Scorer — Onde focar seu pipeline" },
      { name: "description", content: "Priorize seu pipeline de vendas B2B e saiba onde focar nesta semana." },
      { property: "og:title", content: "Lead Scorer — Onde focar seu pipeline" },
      { property: "og:description", content: "Priorize seu pipeline de vendas B2B e saiba onde focar nesta semana." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  const { data: params } = useParametros();
  const { data: deals, isLoading, error, refetch } = useDeals();
  const resumo = useMemo(() => (deals ? calcResumo(deals) : undefined), [deals]);

  const ciclo = params ? String(params.ciclo_max_dias) : "…";
  const risco = params ? String(params.fase_risco_dias) : "…";
  const passos = [
    { n: "1", t: "Primeiro, a fila certa", d: `Deals parados há mais de ${ciclo} dias saem do ranking e vão para “Requalificar ou encerrar”. Nenhum deal do histórico fechou depois disso.` },
    { n: "2", t: "Depois, o valor esperado", d: `Chance de ganho pela idade do deal × preço de lista, em escala 0–100. Perdas se concentram nos primeiros ${risco} dias; quem sobrevive ganha mais.` },
    { n: "3", t: "O que não entra", d: "Vendedor, produto, setor e região. Testados com o histórico, não previram o resultado." },
  ];

  return (
    <>
      <PageHeader title="Lead Scorer" subtitle="Onde focar seu pipeline nesta semana" />

      <section className="px-4 py-8 md:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-3xl">Resumo executivo</h2>
          <ResumoDialog
            trigger={
              <button className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent">
                Detalhar mais
              </button>
            }
          />
        </div>
        {error ? (
          <div className="mt-4"><ErrorState error={error} onRetry={() => refetch()} /></div>
        ) : isLoading || !resumo ? (
          <div className="mt-4"><LoadingState rows={3} /></div>
        ) : (
          <>
            <div className="mt-4 rounded-lg border border-border bg-accent p-6 shadow-sm">
              <p className="max-w-4xl text-base leading-relaxed text-accent-foreground md:text-lg">
                Dos <strong>{formatNumber(resumo.abertos)} deals abertos</strong> ({formatUSDCompact(resumo.valorPipeline)} em pipeline),{" "}
                <strong>{formatNumber(resumo.focar)} estão prontos para foco imediato</strong> e concentram{" "}
                <strong>{formatUSD(resumo.valorEsperadoFoco)} de valor esperado</strong>. Outros{" "}
                <strong>{formatPct(resumo.pctParado)}</strong> estão parados além do limite histórico de {ciclo} dias —{" "}
                {formatUSDCompact(resumo.valorParado)} de lista travado que precisa ser requalificado ou encerrado.
                {resumo.semConta > 0 && <> Há ainda {formatNumber(resumo.semConta)} deals sem conta cadastrada no CRM.</>}
              </p>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
              {[
                { label: "Deals abertos", value: formatNumber(resumo.abertos), hint: formatUSDCompact(resumo.valorPipeline) + " em pipeline" },
                { label: "Foco imediato", value: formatNumber(resumo.focar), hint: formatUSDCompact(resumo.valorEsperadoFoco) + " de valor esperado" },
                { label: "Parados além do limite", value: formatNumber(resumo.requalificar), hint: formatUSDCompact(resumo.valorParado) + " travado", warn: true },
                { label: "Sem conta cadastrada", value: formatNumber(resumo.semConta) },
              ].map((c) => (
                <div key={c.label} className={`rounded-lg border p-4 ${c.warn ? "border-warning bg-warning-soft" : "border-border bg-card"}`}>
                  <p className={`text-xs font-medium ${c.warn ? "text-warning-foreground" : "text-muted-foreground"}`}>{c.label}</p>
                  <p className={`mt-1 font-numeric text-3xl font-semibold tabular-nums ${c.warn ? "text-warning-foreground" : "text-foreground"}`}>{c.value}</p>
                  {c.hint && <p className="mt-0.5 text-xs text-muted-foreground">{c.hint}</p>}
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="px-4 pb-8 md:px-8">
        <h2 className="font-display text-3xl">Como o score funciona</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {passos.map((p) => (
            <div key={p.n} className="rounded-lg border border-border bg-card p-5">
              <span className="font-numeric text-4xl font-semibold tabular-nums text-primary">{p.n}</span>
              <h3 className="mt-2 font-semibold">{p.t}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{p.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 pb-10 md:px-8">
        <div className="rounded-lg border border-border bg-card p-4 md:p-6">
          <h2 className="font-display text-2xl">Chance de ganhar pela idade do deal</h2>
          <p className="mt-1 text-sm text-muted-foreground">Probabilidade de fechar ganho para um deal que já sobreviveu X dias sem fechar.</p>
          <div className="mt-4"><CurvaChart height={340} /></div>
        </div>

        {deals && deals.length > 0 && (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-4 md:p-6">
              <h2 className="font-display text-2xl">Deals abertos por fila</h2>
              <p className="mt-1 text-sm text-muted-foreground">Para onde o pipeline aberto aponta nesta semana.</p>
              <div className="mt-4"><FilasChart deals={deals} /></div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 md:p-6">
              <h2 className="font-display text-2xl">Valor esperado em foco por região</h2>
              <p className="mt-1 text-sm text-muted-foreground">Onde está o dinheiro dos deals prontos para focar.</p>
              <div className="mt-4"><RegiaoChart deals={deals} /></div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 md:p-6 lg:col-span-2">
              <h2 className="font-display text-2xl">Distribuição do score nos deals em foco</h2>
              <p className="mt-1 text-sm text-muted-foreground">Quantos deals em foco caem em cada faixa de score (0–100).</p>
              <div className="mt-4"><ScoreChart deals={deals} /></div>
            </div>
          </div>
        )}

        <Link to="/pipeline" className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90">
          Ver meu pipeline <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </>
  );
}
