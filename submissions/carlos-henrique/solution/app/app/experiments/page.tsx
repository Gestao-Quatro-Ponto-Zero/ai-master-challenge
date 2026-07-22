import { loadData } from "@/lib/data";
import type { Experiment } from "@/lib/types";
import { DataFreshness, LimitationCallout, SectionHeader } from "@/components/ui";
import { GroupedSampleChart, MultiColorBarChart } from "@/components/DashboardCharts";
import { ExperimentExplorer } from "@/components/ExperimentExplorer";

interface Registry { cutoff: string; experiments: Experiment[] }
interface Details { experiments: Experiment[] }

export default async function ExperimentsPage() {
  const [registry, details] = await Promise.all([loadData<Registry>("experiment_registry.json"), loadData<Details>("experiment_details.json")]);
  const samples = registry.experiments.map((item) => ({ experiment: item.experiment_id, available: item.eligible_accounts, required: item.required_sample }));
  const statusMap = new Map<string, number>();
  registry.experiments.forEach((item) => statusMap.set(item.status, (statusMap.get(item.status) ?? 0) + 1));
  const statuses = Array.from(statusMap, ([status, experiments]) => ({ status, experiments }));
  return <div><SectionHeader eyebrow="Laboratório de Experimentos" title="Observação não é causalidade." description="Oito desenhos futuros transformam observações governadas em hipóteses falseáveis. Viabilidade, tamanho de amostra, plano estatístico e ética aparecem antes de qualquer revisão operacional." /><DataFreshness cutoff={registry.cutoff} /><div className="mt-7"><LimitationCallout title="Hipótese não testada">Todos os status causais permanecem não testados. Alocações simuladas validam somente a mecânica do desenho; nenhum experimento ou intervenção foi executado.</LimitationCallout></div><section className="mt-6 grid gap-5 xl:grid-cols-2"><GroupedSampleChart data={samples} /><MultiColorBarChart data={statuses} category="status" value="experiments" title="Status de viabilidade experimental" subtitle="Oito desenhos governados · sem estado de sucesso ou fracasso" summary="Um desenho está pronto para revisão; os demais são somente piloto, subdimensionados ou não viáveis." /></section><div className="mt-8"><ExperimentExplorer registry={registry.experiments} details={details.experiments} /></div></div>;
}
