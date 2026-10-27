import { ArrowRight, Flag, Hourglass, Sprout, Target } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { DealCard } from "@/components/deal-card";
import { StalledPanel } from "@/components/stalled-panel";
import { asOptions, SelectField, SubmitButton } from "@/components/select-field";
import { PageHeader, Ring, SectionTitle, StatCard } from "@/components/ui";
import { count, usd } from "@/lib/format";
import { applyFilters, filterQuery, history, options, parseFilters, pipeline, summarize } from "@/lib/pipeline";

const FOCUS_SIZES = [6, 10, 20] as const;

export default function TodayPage(props: PageProps<"/">) {
  return (
    <Suspense fallback={<p className="text-secondary">Carregando o pipeline…</p>}>
      <Today searchParams={props.searchParams} />
    </Suspense>
  );
}

async function Today({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  const params = await searchParams;
  const { agent } = parseFilters(params);
  const requested = Number(params.foco);
  const size = FOCUS_SIZES.find((n) => n === requested) ?? 6;

  const mine = applyFilters(pipeline, { agent });
  const { active, stalled, activeExpectedValue, stalledValueShare, withoutAccount } = summarize(mine);
  const focus = active.slice(0, size);
  const closing = active.filter((s) => s.momentum === "closing");
  const prospecting = active.filter((s) => s.momentum === "prospecting");
  const firstName = agent?.split(" ")[0];

  return (
    <div className="space-y-10">
      <section className="grid items-center gap-8 xl:grid-cols-[minmax(0,1fr)_auto]">
        <div>
          <PageHeader
            title={firstName ? `Bom dia, ${firstName}!` : "Onde focar hoje"}
            description={
              <>
                {firstName ? "Sua pauta" : "A pauta do time"} está ordenada por valor esperado (chance × preço). Deals abertos há mais de{" "}
                {history.maxCycle} dias, mais que qualquer deal já fechado, saem da pauta e vão para a revisão.
              </>
            }
          />
          <form method="get" className="mt-6 flex flex-wrap items-end gap-3">
            <SelectField
              name="vendedor"
              label="Vendedor"
              value={agent}
              options={asOptions(options.agents)}
              allLabel="Todo o time"
              className="w-[min(100%,18rem)]"
            />
            <SelectField
              name="foco"
              label="Deals na pauta"
              value={String(size)}
              options={FOCUS_SIZES.slice(1).map((n) => ({ value: String(n), label: `${n} deals` }))}
              allLabel="6 deals"
              className="w-[10rem]"
            />
            <SubmitButton>Ver pauta</SubmitButton>
          </form>
        </div>

        <div className="card flex flex-wrap items-center justify-around gap-10 px-8 py-6">
          <div className="text-center">
            <p className="text-[13px] font-semibold">Valor esperado ativo</p>
            <p className="mt-3 text-[34px] leading-none font-bold tracking-[-0.03em] tabular-nums">{usd(activeExpectedValue)}</p>
            <p className="mt-2 text-[12px] text-secondary">em {count(active.length)} deals ativos</p>
          </div>
          <div className="text-center">
            <p className="mb-3 text-[13px] font-semibold">Pipeline parado</p>
            <Ring value={stalledValueShare} label="do valor de tabela está em deals parados" />
          </div>
        </div>
      </section>

      <section aria-label="Resumo" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Target} label="Ativos" value={count(active.length)} caption="com chance e valor esperado" tone="moment" />
        <StatCard
          icon={Flag}
          label="Reta final"
          value={count(closing.length)}
          caption={`entre ${history.wonP75Cycle} e ${history.maxCycle} dias: hora de fechar`}
          href={`/pipeline${filterQuery({ agent, momentum: "closing" })}`}
          tone="moment"
        />
        <StatCard
          icon={Sprout}
          label="Prospecção"
          value={count(prospecting.length)}
          caption={`${count(withoutAccount)} deals abertos sem conta cadastrada`}
          href={`/pipeline${filterQuery({ agent, momentum: "prospecting" })}`}
        />
        <StatCard
          icon={Hourglass}
          label="Parados"
          value={count(stalled.length)}
          caption={`há mais de ${history.maxCycle} dias: revisar ou desqualificar`}
          href={`/parados${filterQuery({ agent })}`}
          tone="stalled"
        />
      </section>

      <section aria-labelledby="pauta" className="space-y-4">
        <SectionTitle
          title={`Pauta de hoje · ${focus.length} deals`}
          action={
            active.length > focus.length && (
              <Link href={`/pipeline${filterQuery({ agent })}`} className="flex items-center gap-1 text-[14px] font-semibold text-moment hover:underline">
                Ver os {count(active.length)} ativos <ArrowRight className="size-4" aria-hidden />
              </Link>
            )
          }
        />
        <h2 id="pauta" className="sr-only">
          Pauta de hoje
        </h2>
        {focus.length === 0 ? (
          <p className="card p-6 text-secondary">Nenhum deal ativo para este vendedor.</p>
        ) : (
          <ol className="grid grid-cols-1 gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {focus.map((scored, i) => (
              <DealCard key={scored.deal.id} scored={scored} rank={i + 1} />
            ))}
          </ol>
        )}
      </section>

      {stalled.length > 0 && <StalledPanel stalled={stalled} stalledValueShare={stalledValueShare} href={`/parados${filterQuery({ agent })}`} />}
    </div>
  );
}
