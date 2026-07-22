import { loadData } from "@/lib/data";
import { DataFreshness, LimitationCallout, SectionHeader } from "@/components/ui";
import { MultiColorBarChart, SimpleBarChart } from "@/components/DashboardCharts";
import { formatIntegerPtBr, formatPercentPtBr } from "@/lib/format";

interface QualityData { cutoff: string; distribution: Array<{ status: string; events: number }>; coverage: { main: number; strict: number }; quality_backlog: { accounts: number }; subscription_overlap: { episodes: number }; reconciliation: { unexplained_difference: number }; privacy: { pii_exposed: number; future_leakage: number } }

export default async function QualityPage() {
  const quality = await loadData<QualityData>("quality.json");
  const coverage = [{ population: "MAIN", coverage: quality.coverage.main * 100 }, { population: "STRICT", coverage: quality.coverage.strict * 100 }];
  return <div>
    <SectionHeader eyebrow="Qualidade dos dados" title="A qualidade é controlada, não escondida." description="Cada evento passa por controles antes do uso comportamental. Evidências com alertas permanecem visíveis, enquanto eventos em quarentena são reservados à revisão de qualidade dos dados." />
    <DataFreshness cutoff={quality.cutoff} />
    <div className="mt-7 grid gap-5 xl:grid-cols-2"><MultiColorBarChart data={quality.distribution} category="status" value="events" title="Distribuição da qualidade dos eventos" subtitle="Eventos processados antes e depois dos controles · data-limite em 31 de dez. de 2024" summary="13.927 eventos são utilizáveis na população principal; 21.659 eventos em quarentena são excluídos da evidência comportamental." /><SimpleBarChart data={coverage} category="population" value="coverage" title="Cobertura principal versus estrita" subtitle="Percentual dos 35.586 eventos processados" summary={`A população principal cobre ${formatPercentPtBr(quality.coverage.main)} e a estrita cobre ${formatPercentPtBr(quality.coverage.strict)}.`} /></div>
    <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[
      ["Pendências de qualidade", quality.quality_backlog.accounts, "Separadas das filas comportamentais"], ["Episódios de assinatura", quality.subscription_overlap.episodes, "Sobreposição mantida como alerta de origem"], ["Diferença não explicada", quality.reconciliation.unexplained_difference, "Controle de reconciliação"], ["PII e vazamento futuro", quality.privacy.pii_exposed + quality.privacy.future_leakage, "Os dois controles são iguais a zero"]
    ].map(([label, value, note]) => <article className="panel p-5" key={String(label)}><p className="data-label">{label}</p><p className="mt-2 font-mono text-3xl font-semibold">{formatIntegerPtBr(Number(value))}</p><p className="mt-2 text-sm text-muted">{note}</p></article>)}</div>
    <div className="mt-6"><LimitationCallout title="Pendências de qualidade dos dados">467 contas exigem uma ou mais revisões de qualidade antes de uma interpretação comportamental sem restrições.</LimitationCallout></div>
    <section className="mt-6 grid gap-5 lg:grid-cols-2"><article className="panel p-5"><h3 className="font-semibold">Como interpretar os estados de qualidade</h3><ul className="mt-4 space-y-3">{["Um alerta pode afetar um evento sem invalidar toda a jornada.", "Eventos em quarentena nunca geram sinais comportamentais.", "A população estrita é uma análise de sensibilidade que usa apenas eventos válidos.", "Baixa confiança dos dados impede interpretações comportamentais fortes."].map((item) => <li className="rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700" key={item}>{item}</li>)}</ul></article><article className="panel p-5"><h3 className="font-semibold">Limitações principais</h3><ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-6 text-slate-700">{["Eventos com alerta afetam materialmente a cobertura dos desfechos.", "Censura administrativa e timestamps diários limitam a interpretação.", "A quarentena é excluída de toda evidência comportamental, de receita e de jornada."].map((item) => <li key={item}>{item}</li>)}</ul></article></section>
  </div>;
}
