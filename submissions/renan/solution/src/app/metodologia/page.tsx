import { ChartColumn, Hourglass, Scale, ShieldCheck, Timer } from "lucide-react";
import type { Metadata } from "next";
import { Bar, PageHeader, SectionTitle, StatCard } from "@/components/ui";
import { count, pct, usd } from "@/lib/format";
import { analysis, dataset, history } from "@/lib/pipeline";

export const metadata: Metadata = { title: "Metodologia" };

const FACTOR_NAME: Record<string, string> = {
  agent: "Vendedor",
  product: "Produto",
  sector: "Setor da conta",
  companySize: "Porte da conta",
};

const decimal = (x: number, digits = 3) =>
  x.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits }).replace("-", "−");

export default function MethodologyPage() {
  const { agentSignal } = analysis;
  const scoreTop20 = analysis.backtests.map((b) => b.strategies[0].top20Share);
  const randomTop20 = analysis.backtests.map((b) => b.strategies.at(-1)!.top20Share);
  const mean = (xs: number[]) => xs.reduce((s, x) => s + x, 0) / xs.length;
  return (
    <div className="space-y-8">
      <PageHeader
        title="Metodologia"
        description="Neste CRM, nenhum modelo, nem o feeling, consegue prever quais deals vão ser ganhos ou perdidos. O que dá para saber é quanto cada deal vale e quais estão mortos. A Régua prioriza por isso."
      />

      <section aria-label="Principais números" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Scale} label="Taxa geral" value={pct(history.baseRate, 1)} caption={`${count(history.closedDeals)} deals fechados`} />
        <StatCard icon={Timer} label="Maior ciclo" value={`${history.maxCycle} dias`} caption="nenhum deal fechou depois disso" tone="moment" />
        <StatCard icon={Hourglass} label="Engaging parados" value={pct(analysis.stalledShareOfEngaging)} caption={`${pct(analysis.stalledValueShare)} do valor aberto`} tone="stalled" />
        <StatCard icon={ChartColumn} label="Receita no top 20%" value={pct(mean(scoreTop20))} caption={`média dos 3 cortes; acaso: ${pct(mean(randomTop20))}`} tone="moment" />
      </section>

      <section aria-labelledby="score" className="card p-6">
        <SectionTitle title="Como o score é calculado" />
        <h2 id="score" className="sr-only">
          Como o score é calculado
        </h2>
        <ol className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {[
            `A chance parte da taxa geral de vitória (${pct(history.baseRate, 1)}).`,
            `É ajustada pelo tempo no pipeline: quem passa da fase das perdas (mediana de ${history.lostMedianCycle} dias) fecha mais.`,
            "Depois, por vendedor, produto, setor e porte, com pesos de Bayes empírico: só pesa o que supera o ruído.",
            "Valor esperado = chance × preço de tabela. O score (0–100) é a posição desse valor entre os deals ativos.",
            `Abertos há mais de ${history.maxCycle} dias saem da pauta e vão para a fila de revisão.`,
          ].map((text, i) => (
            <li key={i} className="rounded-xl bg-hover p-4 text-[14px]">
              <span className="mb-2 grid size-7 place-items-center rounded-full bg-primary font-mono text-[12px] font-semibold text-surface">{i + 1}</span>
              {text}
            </li>
          ))}
        </ol>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section id="fatores" aria-labelledby="fatores-titulo" className="card p-6">
          <SectionTitle title="O que separa ganhos de perdas" />
          <h2 id="fatores-titulo" className="sr-only">
            O que separa ganhos de perdas
          </h2>
          <table className="mt-4 w-full text-[14px]">
            <thead>
              <tr>
                <th scope="col" className="field pb-2 text-left font-medium">
                  Fator
                </th>
                <th scope="col" className="field pb-2 text-right font-medium">
                  Taxa bruta
                </th>
                <th scope="col" className="field pb-2 text-right font-medium">
                  Sem o ruído
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {analysis.factorSpread.map((f) => (
                <tr key={f.key}>
                  <td className="py-2.5 font-medium">{FACTOR_NAME[f.key]}</td>
                  <td className="py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {pct(f.rawMin, 1)} – {pct(f.rawMax, 1)}
                  </td>
                  <td className="py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {pct(f.shrunkMin, 1)} – {pct(f.shrunkMax, 1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-[13px] text-secondary">
            Vendedor: qui-quadrado de {decimal(agentSignal.chi2, 1)} com {agentSignal.degreesOfFreedom} graus de liberdade, o esperado se todos
            tivessem a mesma taxa real. Correlação entre semestres de {decimal(agentSignal.agentStability.correlation, 2)}; por produto,{" "}
            {decimal(agentSignal.agentProductStability.correlation, 2)}. Por isso não há ranking de vendedores.
          </p>
        </section>

        <section aria-labelledby="tempo" className="card p-6">
          <SectionTitle title="Chance por tempo no pipeline" />
          <h2 id="tempo" className="sr-only">
            Chance por tempo no pipeline
          </h2>
          <ul className="mt-4 space-y-3">
            {analysis.survivalPoints.map((p) => (
              <li key={p.day} className="grid grid-cols-[7rem_1fr_3.5rem] items-center gap-3 text-[14px]">
                <span className="text-secondary">após {p.day} dias</span>
                <Bar value={p.winRate} label={`${pct(p.winRate, 1)} de chance após ${p.day} dias`} />
                <span className="text-right font-mono text-[13px] font-semibold tabular-nums">{pct(p.winRate, 1)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-[13px] text-stalled">
            {pct(analysis.stalledShareOfEngaging)} dos deals em Engaging já passaram de {history.maxCycle} dias e somam{" "}
            {pct(analysis.stalledValueShare)} do valor aberto ({usd(analysis.openValue)}). Ordenando só por preço,{" "}
            {pct(analysis.stalledInTopByPrice)} do topo seriam esses deals.
          </p>
        </section>
      </div>

      <section aria-labelledby="backtest" className="card p-6">
        <SectionTitle title="Backtest: a Régua em datas passadas" />
        <h2 id="backtest" className="sr-only">
          Backtest
        </h2>
        <p className="mt-2 max-w-[80ch] text-[14px] text-secondary">
          Em cada corte, a Régua aprende só com o que tinha fechado até a data e é avaliada nos deals abertos naquele dia, cujo resultado hoje é
          conhecido. As barras mostram a parcela da receita realizada que estava no top 20% de cada estratégia.
        </p>
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {analysis.backtests.map((b) => (
            <div key={b.cutoff} className="rounded-xl bg-hover p-4">
              <p className="text-[15px] font-semibold">Corte em {b.cutoff.split("-").reverse().join("/")}</p>
              <p className="text-[12px] text-secondary">{count(b.evaluated)} deals avaliados</p>
              <ul className="mt-4 space-y-3">
                {b.strategies.map((s, i) => (
                  <li key={s.name} className="text-[13px]">
                    <div className="flex justify-between gap-2">
                      <span className={i === 0 ? "font-semibold" : ""}>{s.name}</span>
                      <span className="font-mono tabular-nums">{pct(s.top20Share, 1)}</span>
                    </div>
                    <div className="mt-1">
                      <Bar value={s.top20Share} tone={i === 0 ? "moment" : "secondary"} />
                    </div>
                    {s.auc !== null && <p className="mt-0.5 text-[11px] text-secondary">AUC da chance: {decimal(s.auc)}</p>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[13px] text-secondary">
          AUC ≈ 0,5 equivale a uma moeda: a chance não separa ganhos de perdas. A regra de parados não pôde ser validada no backtest, porque nos
          cortes nenhum deal tinha passado do ciclo máximo conhecido.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section aria-labelledby="qualidade" className="card p-6">
          <SectionTitle title="Qualidade dos dados" />
          <h2 id="qualidade" className="sr-only">
            Qualidade dos dados
          </h2>
          <ul className="mt-4 divide-y divide-line">
            {dataset.quality.map((q) => (
              <li key={q.code} className="flex gap-3 py-3">
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-moment" aria-hidden />
                <div className="text-[14px]">
                  <p className="font-medium">
                    {q.description} <span className="font-mono text-[12px] text-secondary tabular-nums">[{count(q.affected)}]</span>
                  </p>
                  <p className="text-secondary">{q.treatment}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="limites" className="card p-6">
          <SectionTitle title="Limitações" />
          <h2 id="limites" className="sr-only">
            Limitações
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-[14px]">
            <li>Dataset sintético: os padrões (ou a falta deles) podem não refletir um CRM real.</li>
            <li>Sem dados de atividade (e-mails, reuniões), que costumam ser o sinal mais forte de fechamento.</li>
            <li>
              Deals abertos usam o preço de tabela; nos ganhos, o valor fechado fica entre {pct(analysis.closeToList.p10)} e{" "}
              {pct(analysis.closeToList.p90)} dele (p10–p90).
            </li>
            <li>A regra de parados se apoia no histórico (nenhum ciclo acima de {history.maxCycle} dias), não em validação fora da amostra.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
