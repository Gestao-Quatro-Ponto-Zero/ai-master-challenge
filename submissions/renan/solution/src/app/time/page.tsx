import { CalendarClock, CircleDollarSign, Hourglass, Target } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { asOptions, SelectField, SubmitButton } from "@/components/select-field";
import { Bar, PageHeader, SectionTitle, StatCard } from "@/components/ui";
import { count, pct, usd } from "@/lib/format";
import { analysis, applyFilters, dataset, filterQuery, history, options, parseFilters, pipeline, summarize } from "@/lib/pipeline";

export const metadata: Metadata = { title: "Time" };

export default function TeamPage(props: PageProps<"/time">) {
  return (
    <Suspense fallback={<p className="text-secondary">Carregando o time…</p>}>
      <Team searchParams={props.searchParams} />
    </Suspense>
  );
}

const initials = (name: string) =>
  name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("");

async function Team({ searchParams }: { searchParams: PageProps<"/time">["searchParams"] }) {
  const { manager } = parseFilters(await searchParams);
  const team = applyFilters(pipeline, { manager });
  const totals = summarize(team);
  const agents = dataset.agents
    .filter((a) => !manager || a.manager === manager)
    .map((a) => ({ agent: a, ...summarize(team.filter((s) => s.deal.agent === a.name)) }))
    .filter((row) => row.active.length + row.stalled.length > 0)
    .sort((a, b) => a.agent.name.localeCompare(b.agent.name, "pt-BR"));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Time"
        description={
          <>
            Higiene do pipeline por vendedor: deals parados para revisar e contas para cadastrar. Ordem alfabética, sem ranking de desempenho:
            as diferenças de taxa de vitória entre vendedores são compatíveis com o acaso (
            <Link href="/metodologia#fatores" className="underline underline-offset-4">
              ver metodologia
            </Link>
            ).
          </>
        }
      />

      <form method="get" className="flex flex-wrap items-end gap-3">
        <SelectField name="manager" label="Manager" value={manager} options={asOptions(options.managers)} allLabel="Todos os managers" className="w-[min(100%,18rem)]" />
        <SubmitButton>Ver time</SubmitButton>
      </form>

      <section aria-label="Resumo do time" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Target} label="Deals ativos" value={count(totals.active.length)} tone="moment" />
        <StatCard icon={CircleDollarSign} label="Valor esperado" value={usd(totals.activeExpectedValue)} />
        <StatCard icon={Hourglass} label="Parados" value={count(totals.stalled.length)} href={`/parados${filterQuery({ manager })}`} tone="stalled" />
        <StatCard icon={Hourglass} label="Valor parado" value={pct(totals.stalledValueShare)} caption="do valor de tabela aberto" tone="stalled" />
      </section>

      <section aria-labelledby="vendedores" className="space-y-4">
        <SectionTitle title={`Vendedores · ${agents.length}`} />
        <h2 id="vendedores" className="sr-only">
          Vendedores
        </h2>
        <div className="card overflow-hidden">
          <table className="w-full border-collapse text-left text-[14px]">
            <thead className="hidden border-b border-line bg-hover/60 lg:table-header-group">
              <tr>
                {["Vendedor", "Ativos", "Valor esperado", "Parados", "Valor parado", "Sem conta"].map((h, i) => (
                  <th key={h} scope="col" className={`field px-4 py-3 font-medium ${i >= 1 ? "text-right" : ""}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {agents.map(({ agent, active, stalled, activeExpectedValue, stalledValueShare, withoutAccount }) => (
                <tr key={agent.name} className="block px-4 py-4 hover:bg-hover lg:table-row lg:p-0">
                  <td className="flex items-center gap-3 lg:table-cell lg:px-4 lg:py-3">
                    <span className="flex items-center gap-3">
                      <span aria-hidden className="grid size-9 shrink-0 place-items-center rounded-full bg-selected font-mono text-[11px] font-semibold">
                        {initials(agent.name)}
                      </span>
                      <span>
                        <Link href={`/${filterQuery({ agent: agent.name })}`} className="font-semibold hover:underline">
                          {agent.name}
                        </Link>
                        <span className="block text-[12px] text-secondary">
                          {agent.manager} · {agent.regionalOffice}
                        </span>
                      </span>
                    </span>
                  </td>
                  <Num label="Ativos">{count(active.length)}</Num>
                  <Num label="Valor esperado">{usd(activeExpectedValue)}</Num>
                  <Num label="Parados">
                    <Link href={`/parados${filterQuery({ agent: agent.name })}`} className="font-semibold text-stalled hover:underline">
                      {count(stalled.length)}
                    </Link>
                  </Num>
                  <td className="flex items-center justify-between gap-3 pt-1 lg:table-cell lg:w-[200px] lg:px-4 lg:py-3">
                    <span className="field lg:hidden">Valor parado</span>
                    <span className="flex w-[160px] items-center gap-2 lg:ml-auto">
                      <Bar value={stalledValueShare} tone="stalled" label={`${pct(stalledValueShare)} do valor parado`} />
                      <span className="w-10 text-right font-semibold text-stalled tabular-nums">{pct(stalledValueShare)}</span>
                    </span>
                  </td>
                  <Num label="Sem conta">{count(withoutAccount)}</Num>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="trimestre" className="card flex items-start gap-4 p-6">
        <span className="grid size-11 shrink-0 place-items-center rounded-full bg-moment-soft text-moment">
          <CalendarClock className="size-5" aria-hidden />
        </span>
        <div>
          <h2 id="trimestre" className="text-[18px] font-semibold">
            Fim de trimestre: {pct(analysis.quarter.quarterEnd.winRate)} de vitória contra {pct(analysis.quarter.otherMonths.winRate)} nos outros meses
          </h2>
          <p className="mt-1 max-w-[75ch] text-[14px] text-secondary">
            Pode ser um padrão comercial real (vitórias puxadas para o fechamento, perdas baixadas no início do trimestre seguinte) ou um artefato
            do dataset, por isso não entra no score. Vale observar antes de desqualificar deals em janeiro e fevereiro. Base:{" "}
            {count(history.closedDeals)} deals fechados.
          </p>
        </div>
      </section>
    </div>
  );
}

function Num({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <td className="flex items-center justify-between gap-3 pt-1 tabular-nums lg:table-cell lg:px-4 lg:py-3 lg:text-right">
      <span className="field lg:hidden">{label}</span>
      <span>{children}</span>
    </td>
  );
}
