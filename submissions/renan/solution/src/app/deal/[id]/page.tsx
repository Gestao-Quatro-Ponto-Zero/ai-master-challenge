import { ArrowRight, Building2, ChevronRight, CircleAlert, Hourglass, Package, UserRound } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { DayRuler, MomentumChip } from "@/components/momentum";
import { SectionTitle } from "@/components/ui";
import { count, dateBr, pct, points, usd } from "@/lib/format";
import { findDeal, history, pipeline } from "@/lib/pipeline";
import { companySizeBand } from "@/lib/scoring/history";
import type { ScoredDeal } from "@/lib/scoring/score";

/** Abaixo de meio ponto percentual, o fator é tratado como ruído na explicação. */
const NOISE_THRESHOLD = 0.5;
const activeCount = pipeline.filter((s) => s.winProbability !== null).length;

export default function DealPage(props: PageProps<"/deal/[id]">) {
  return (
    <Suspense fallback={<p className="text-secondary">Carregando o deal…</p>}>
      <Deal params={props.params} />
    </Suspense>
  );
}

async function Deal({ params }: { params: PageProps<"/deal/[id]">["params"] }) {
  const { id } = await params;
  const scored = findDeal(id);
  if (!scored) notFound();
  const { deal } = scored;
  const stalled = scored.winProbability === null;

  return (
    <article className="space-y-6">
      <nav aria-label="Trilha" className="flex items-center gap-1 text-[14px] text-secondary">
        <Link href="/pipeline" className="hover:text-primary hover:underline">
          Pipeline
        </Link>
        <ChevronRight className="size-4" aria-hidden />
        <span className="deal-id text-primary">{deal.id}</span>
      </nav>

      <header className="card p-6 sm:p-8">
        <div className="flex flex-wrap items-start gap-5">
          <span className="grid size-14 shrink-0 place-items-center rounded-2xl bg-hover text-secondary">
            <Package className="size-7" aria-hidden />
          </span>
          <div className="min-w-0 flex-1">
            <p className="deal-id text-[14px] text-secondary">{deal.id}</p>
            <h1 className="text-[clamp(32px,4vw,52px)] leading-none font-bold tracking-[-0.04em]">{deal.product}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <MomentumChip scored={scored} />
              <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1 text-[13px]">
                <UserRound className="size-3.5" aria-hidden /> {deal.agent}
              </span>
              {deal.account ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1 text-[13px]">
                  <Building2 className="size-3.5" aria-hidden /> {deal.account}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-stalled-soft px-2.5 py-1 text-[13px] text-stalled">
                  <CircleAlert className="size-3.5" aria-hidden /> Conta não informada
                </span>
              )}
            </div>
          </div>
          <dl className="flex gap-8">
            <div>
              <dt className="field">Score</dt>
              <dd className="mt-1 text-[34px] leading-none font-bold tabular-nums">{scored.score ?? "—"}</dd>
            </div>
            <div>
              <dt className="field">{stalled ? "Valor de tabela" : "Valor esperado"}</dt>
              <dd className={`mt-1 text-[34px] leading-none font-bold tabular-nums ${stalled ? "text-stalled" : ""}`}>
                {usd(stalled ? deal.listPrice : scored.expectedValue)}
              </dd>
            </div>
          </dl>
        </div>

        <div className={`mt-6 flex items-start gap-3 rounded-xl p-4 ${stalled ? "bg-stalled-soft text-stalled" : "bg-moment-soft text-moment"}`}>
          {stalled ? <Hourglass className="mt-0.5 size-5 shrink-0" aria-hidden /> : <ArrowRight className="mt-0.5 size-5 shrink-0" aria-hidden />}
          <p className="text-[16px] font-semibold">{scored.nextAction}</p>
        </div>

        <div className="mt-8">
          <p className="field mb-3">Régua de dias no pipeline</p>
          <DayRuler scored={scored} showLabels />
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)]">
        <section aria-labelledby="ficha" className="card p-6">
          <SectionTitle title="Ficha do CRM" />
          <h2 id="ficha" className="sr-only">
            Ficha do CRM
          </h2>
          <dl className="mt-4 divide-y divide-line text-[15px]">
            <Row label="Vendedor" value={deal.agent} />
            <Row label="Manager" value={deal.manager} />
            <Row label="Escritório" value={deal.regionalOffice} />
            <Row label="Stage no CRM" value={deal.stage} />
            <Row label="Conta" value={deal.account ?? "Não informada: cadastre para setor e porte entrarem na análise"} warn={!deal.account} />
            {deal.account && <Row label="Setor" value={deal.sector ?? "—"} capitalize />}
            {deal.account && <Row label="Porte" value={companySizeBand(deal.accountEmployees) ?? "—"} />}
            <Row label="Engajamento" value={deal.engageDate ? dateBr(deal.engageDate) : "Ainda não engajado"} />
            <Row label="Preço de tabela" value={usd(deal.listPrice)} />
          </dl>
        </section>

        <section aria-labelledby="recibo" className="card p-6">
          <SectionTitle title="Por que este score" />
          <h2 id="recibo" className="sr-only">
            Por que este score
          </h2>
          {stalled ? <StalledExplanation scored={scored} /> : <Receipt scored={scored} />}
        </section>
      </div>
    </article>
  );
}

function Row({ label, value, warn, capitalize }: { label: string; value: string; warn?: boolean; capitalize?: boolean }) {
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-4 py-2.5">
      <dt className="field self-center">{label}</dt>
      <dd className={`${warn ? "text-stalled" : ""} ${capitalize ? "capitalize" : ""}`}>{value}</dd>
    </div>
  );
}

function Receipt({ scored }: { scored: ScoredDeal }) {
  const relevant = scored.factors.filter((f) => Math.abs(f.points) >= NOISE_THRESHOLD);
  const noise = scored.factors.filter((f) => Math.abs(f.points) < NOISE_THRESHOLD);
  const maxPoints = Math.max(10, ...scored.factors.map((f) => Math.abs(f.points)));
  return (
    <div className="mt-4">
      <Step label="Taxa geral de vitória" value={pct(history.baseRate, 1)} note={`Base: ${count(history.closedDeals)} deals fechados`} />
      {relevant.map((f) => (
        <Step key={f.key} label={f.label} value={points(f.points)} note={f.detail} bar={f.points / maxPoints} />
      ))}
      {noise.length > 0 && (
        <Step
          label={noise.map((f) => f.label.split(":")[0]).join(", ")}
          value={points(noise.reduce((s, f) => s + f.points, 0))}
          note="Diferenças dentro do ruído estatístico: não mudam a chance"
          muted
        />
      )}
      <div className="mt-3 space-y-1 rounded-xl bg-hover p-4">
        <Total label="Chance de fechar" value={pct(scored.winProbability!, 1)} />
        <Total label="× Preço de tabela" value={usd(scored.deal.listPrice)} small />
        <Total label="= Valor esperado" value={usd(scored.expectedValue)} />
      </div>
      <p className="mt-4 text-[13px] text-secondary">
        Score {scored.score}: posição do valor esperado deste deal entre os {count(activeCount)} deals ativos, de 0 (menor) a 100 (maior).
      </p>
    </div>
  );
}

function Step({ label, value, note, bar, muted }: { label: string; value: string; note?: string; bar?: number; muted?: boolean }) {
  return (
    <div className={`border-b border-line py-3 ${muted ? "text-secondary" : ""}`}>
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-[15px] font-medium">{label}</span>
        <span className="font-mono text-[14px] font-semibold whitespace-nowrap tabular-nums">{value}</span>
      </div>
      {bar !== undefined && (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-track">
          <div className={`h-full rounded-full ${bar >= 0 ? "bg-moment" : "bg-stalled"}`} style={{ width: `${Math.abs(bar) * 100}%` }} />
        </div>
      )}
      {note && <p className="mt-1 text-[13px] text-secondary">{note}</p>}
    </div>
  );
}

function Total({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className={small ? "text-[14px] text-secondary" : "text-[15px] font-semibold"}>{label}</span>
      <span className={`whitespace-nowrap tabular-nums ${small ? "text-[14px] text-secondary" : "text-[22px] font-bold"}`}>{value}</span>
    </div>
  );
}

function StalledExplanation({ scored }: { scored: ScoredDeal }) {
  return (
    <div className="mt-4 space-y-3 text-[15px] leading-relaxed">
      <p className="font-semibold text-stalled">
        Aberto há {scored.daysOpen} dias. Nenhum dos {count(history.closedDeals)} deals já fechados levou mais que {history.maxCycle} dias.
      </p>
      <p>
        Não há base histórica para estimar a chance deste deal, então ele fica fora da pauta. O valor de tabela de {usd(scored.deal.listPrice)}{" "}
        provavelmente não é receita real.
      </p>
      <p className="text-secondary">Ação: confirme com o cliente se ainda há projeto. Se não houver, desqualifique para limpar a previsão.</p>
    </div>
  );
}
