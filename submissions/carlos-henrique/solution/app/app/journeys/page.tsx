import { loadData } from "@/lib/data";
import type { JourneySample } from "@/lib/types";
import { DataFreshness, SectionHeader } from "@/components/ui";
import { JourneyExplorer } from "@/components/JourneyExplorer";
import { MultiColorBarChart, SimpleBarChart } from "@/components/DashboardCharts";

interface Samples { cutoff: string; samples: JourneySample[] }
interface JourneyIndex { outcome_distribution: Array<{ outcome: string; accounts: number }>; taxonomy_distribution: Array<{ taxonomy: string; accounts: number }> }

export default async function JourneysPage() {
  const [samples, index] = await Promise.all([loadData<Samples>("journey_samples.json"), loadData<JourneyIndex>("journey_index.json")]);
  return <div><SectionHeader eyebrow="Explorador de jornadas" title="Três jornadas reais, delimitadas para explicação." description="Selecione um perfil anônimo para examinar sua linha do tempo governada, desfecho observado, taxonomia, cobertura de qualidade, padrões vinculados e limites de interpretação." /><DataFreshness cutoff={samples.cutoff} /><div className="mt-7"><JourneyExplorer samples={samples.samples} /></div><section className="mt-8 grid gap-5 xl:grid-cols-2"><MultiColorBarChart data={index.outcome_distribution} category="outcome" value="accounts" title="Distribuição dos desfechos das jornadas" subtitle="Contas únicas · jornada completa observada · população principal" summary="Sem churn observado, churn único, churn recorrente e reativação são classes históricas de desfecho." /><SimpleBarChart data={index.taxonomy_distribution.slice(0, 8)} category="taxonomy" value="accounts" title="Distribuição da taxonomia de jornadas" subtitle="Principais classes determinísticas · contas únicas" summary="As taxonomias organizam evidências; não são pontuações nem previsões." /></section></div>;
}
