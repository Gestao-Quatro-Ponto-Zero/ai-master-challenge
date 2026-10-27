import { ArrowRight, Hourglass, Users } from "lucide-react";
import Link from "next/link";
import { count, pct, usdCompact } from "@/lib/format";
import { closedCycles, history } from "@/lib/pipeline";
import type { ScoredDeal } from "@/lib/scoring/score";

const BIN_DAYS = 15;

/**
 * Fila de revisão em um painel: o tamanho do problema, a prova visual (o ciclo
 * de todos os deals fechados termina em 138 dias; os parados estão além dessa
 * linha) e onde está o valor parado.
 */
export function StalledPanel({ stalled, stalledValueShare, href }: { stalled: ScoredDeal[]; stalledValueShare: number; href: string }) {
  const stalledValue = stalled.reduce((sum, s) => sum + s.deal.listPrice, 0);
  const ages = stalled.map((s) => s.daysOpen ?? 0);
  const oldest = Math.max(history.maxCycle, ...ages);
  const medianAge = [...ages].sort((a, b) => a - b)[Math.floor(ages.length / 2)] ?? 0;

  // Histograma com faixas de ~15 dias alinhadas ao limite: à esquerda, todos os
  // deals fechados (0 a 138 dias); à direita, só os parados (139 em diante).
  const limit = history.maxCycle;
  const closedBins = Math.ceil((limit + 1) / BIN_DAYS);
  const stalledBins = Math.max(1, Math.ceil((oldest - limit) / BIN_DAYS));
  const closedWidth = (limit + 1) / closedBins;
  const stalledWidth = (oldest - limit) / stalledBins;
  const closedHist = new Array<number>(closedBins).fill(0);
  const stalledHist = new Array<number>(stalledBins).fill(0);
  for (const c of closedCycles) closedHist[Math.min(closedBins - 1, Math.floor(c / closedWidth))] += 1;
  for (const a of ages) stalledHist[Math.min(stalledBins - 1, Math.floor((a - limit - 1) / stalledWidth))] += 1;
  const maxClosed = Math.max(1, ...closedHist);
  const maxStalled = Math.max(1, ...stalledHist);
  const limitAt = closedBins / (closedBins + stalledBins);
  const bars = [
    ...closedHist.map((n, i) => ({ n, height: n / maxClosed, stalled: false, from: Math.round(i * closedWidth), to: Math.round((i + 1) * closedWidth) - 1 })),
    ...stalledHist.map((n, i) => ({ n, height: n / maxStalled, stalled: true, from: limit + 1 + Math.round(i * stalledWidth), to: limit + Math.round((i + 1) * stalledWidth) })),
  ];

  const byProduct = Object.values(
    stalled.reduce<Record<string, { product: string; deals: number; value: number }>>((acc, s) => {
      const row = (acc[s.deal.product] ??= { product: s.deal.product, deals: 0, value: 0 });
      row.deals += 1;
      row.value += s.deal.listPrice;
      return acc;
    }, {}),
  )
    .sort((a, b) => b.value - a.value)
    .slice(0, 4);

  return (
    <section aria-labelledby="revisao" className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line bg-stalled-soft/60 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-full bg-stalled text-surface">
            <Hourglass className="size-5" aria-hidden />
          </span>
          <div>
            <h2 id="revisao" className="text-[18px] font-semibold">
              Fila de revisão
            </h2>
            <p className="text-[13px] text-secondary">Deals que passaram do maior ciclo que este CRM já viu</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/time"
            className="inline-flex h-10 items-center gap-2 rounded-full border border-line bg-surface px-4 text-[14px] font-semibold hover:bg-hover"
          >
            <Users className="size-4" aria-hidden /> Por vendedor
          </Link>
          <Link href={href} className="inline-flex h-10 items-center gap-2 rounded-full bg-stalled px-4 text-[14px] font-semibold text-surface hover:opacity-90">
            Revisar fila <ArrowRight className="size-4" aria-hidden />
          </Link>
        </div>
      </div>

      <div className="grid gap-8 p-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.6fr)_minmax(0,1fr)]">
        <dl className="grid grid-cols-2 gap-6 lg:grid-cols-1">
          <div>
            <dt className="field">Deals parados</dt>
            <dd className="mt-1 text-[44px] leading-none font-bold tracking-[-0.04em] text-stalled tabular-nums">{count(stalled.length)}</dd>
            <dd className="mt-1 text-[13px] text-secondary">abertos há mais de {history.maxCycle} dias</dd>
          </div>
          <div>
            <dt className="field">Valor travado</dt>
            <dd className="mt-1 text-[28px] leading-none font-bold tracking-[-0.03em] tabular-nums">{usdCompact(stalledValue)}</dd>
            <dd className="mt-1 text-[13px] text-secondary">{pct(stalledValueShare)} do valor de tabela aberto</dd>
          </div>
          <div className="col-span-2 lg:col-span-1">
            <dt className="field">Idade mediana</dt>
            <dd className="mt-1 text-[28px] leading-none font-bold tracking-[-0.03em] tabular-nums">{medianAge} dias</dd>
            <dd className="mt-1 text-[13px] text-secondary">
              {pct(medianAge / history.maxCycle - 1)} além do limite histórico
            </dd>
          </div>
        </dl>

        <figure className="min-w-0">
          <figcaption className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[14px] font-semibold">Quantos dias cada deal ficou aberto</span>
            <span className="flex gap-3 text-[12px] text-secondary">
              <span className="flex items-center gap-1.5">
                <span aria-hidden className="size-2.5 rounded-sm bg-secondary/50" /> Fechados ({count(closedCycles.length)})
              </span>
              <span className="flex items-center gap-1.5">
                <span aria-hidden className="size-2.5 rounded-sm bg-stalled" /> Parados ({count(stalled.length)})
              </span>
            </span>
          </figcaption>
          <div
            className="relative mt-4 h-44"
            role="img"
            aria-label={`Todos os ${count(closedCycles.length)} deals fechados ficaram abertos entre 0 e ${history.maxCycle} dias. Os ${count(stalled.length)} deals parados estão entre ${history.maxCycle + 1} e ${oldest} dias.`}
          >
            <div className="absolute inset-0 flex items-end gap-[2px]">
              {bars.map((bar) => (
                <div
                  key={`${bar.stalled}-${bar.from}`}
                  className={`flex-1 rounded-t-[3px] ${bar.stalled ? "bg-stalled" : "bg-secondary/40"}`}
                  style={{ height: `${bar.n > 0 ? Math.max(bar.height * 100, 3) : 0}%` }}
                  title={`${bar.from}–${bar.to} dias: ${bar.n} ${bar.stalled ? "parados" : "fechados"}`}
                />
              ))}
            </div>
            <div className="absolute inset-y-0 border-l-2 border-dashed border-primary" style={{ left: `${limitAt * 100}%` }}>
              <span className="absolute -top-1 left-2 rounded-full bg-primary px-2 py-0.5 font-mono text-[10px] font-semibold whitespace-nowrap text-surface">
                {history.maxCycle}d · nenhum fechou depois
              </span>
            </div>
          </div>
          <div className="mt-2 flex justify-between font-mono text-[11px] text-secondary">
            <span>0 dias</span>
            <span>{oldest} dias</span>
          </div>
          <p className="mt-3 text-[13px] text-secondary">
            Cada lado da linha usa a própria escala. Nenhum dos {count(history.closedDeals)} deals fechados passou de {history.maxCycle} dias, e
            esses {count(stalled.length)} estão todos além dela.
          </p>
        </figure>

        <div>
          <p className="text-[14px] font-semibold">Onde está o valor travado</p>
          <ul className="mt-4 space-y-4">
            {byProduct.map((row) => (
              <li key={row.product}>
                <div className="flex items-baseline justify-between gap-3 text-[14px]">
                  <span className="font-medium">{row.product}</span>
                  <span className="font-mono text-[13px] tabular-nums">{usdCompact(row.value)}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-track">
                  <div className="h-full rounded-full bg-stalled" style={{ width: `${(row.value / stalledValue) * 100}%` }} />
                </div>
                <p className="mt-1 text-[12px] text-secondary">
                  {count(row.deals)} deals · {pct(row.value / stalledValue)} do valor travado
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
