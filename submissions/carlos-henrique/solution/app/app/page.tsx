import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { loadData } from "@/lib/data";
import type { Metric } from "@/lib/types";
import { DataFreshness, LimitationCallout, MetricCard, SectionHeader } from "@/components/ui";
import { MultiColorBarChart } from "@/components/DashboardCharts";

interface Overview { cutoff: string; metrics: Metric[]; cards: Array<{ title: string; metric: string; summary: string }> }
interface JourneyIndex { outcome_distribution: Array<{ outcome: string; accounts: number }> }

const metricCopy = [
  ["Contas", "População analítica anônima"], ["Eventos processados", "Antes dos controles de qualidade"], ["Eventos utilizáveis", "População principal"], ["Jornadas", "Em todos os escopos governados"],
  ["Padrões promovíveis", "Robustos ou sensíveis"], ["Transições promovíveis", "Sem dependência alta"], ["Filas de revisão", "Somente investigação humana"], ["Desenhos experimentais", "Todas as hipóteses não testadas"]
] as const;
const pipeline = ["Dados brutos", "Eventos auditados", "Jornadas de clientes", "JourneyGraph", "Revisão humana", "Desenho experimental"];
const cardCopy = [
  ["Qualidade dos dados", "13.927 eventos utilizáveis", "Alertas permanecem visíveis; eventos em quarentena são excluídos da evidência comportamental."],
  ["Inteligência de jornadas", "4.221 jornadas governadas", "Caminhos repetidos são contados por conta e testados nas populações principal e estrita."],
  ["Fila de revisão explicável", "7 filas de revisão humana", "Regras determinísticas priorizam a investigação sem criar uma pontuação preditiva."],
  ["Prontidão experimental", "1 desenho pronto para revisão", "Sete desenhos permanecem somente piloto, subdimensionados ou não viáveis."]
] as const;

export default async function OverviewPage() {
  const [overview, journeys] = await Promise.all([loadData<Overview>("overview.json"), loadData<JourneyIndex>("journey_index.json")]);
  const metrics = overview.metrics.slice(0, 8).map((metric, index) => ({ ...metric, label: metricCopy[index][0], context: metricCopy[index][1] }));
  return <div>
    <SectionHeader eyebrow="Visão executiva" title="De eventos fragmentados à inteligência de retenção governada." description="Uma narrativa de produto que transforma evidência histórica auditada em jornadas explicáveis, filas de revisão humana e hipóteses testáveis." />
    <DataFreshness cutoff={overview.cutoff} />
    <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}</div>
    <section className="mt-8 panel p-6"><p className="eyebrow">Fluxo de evidência</p><ol className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">{pipeline.map((step, index) => <li key={step} className="relative rounded-xl border border-line bg-slate-50 p-4"><span className="font-mono text-xs text-muted">0{index + 1}</span><p className="mt-2 text-sm font-semibold">{step}</p>{index < pipeline.length - 1 && <ArrowRight className="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 rounded-full bg-white text-muted xl:block" size={20} aria-hidden />}</li>)}</ol></section>
    <section className="mt-8 grid gap-5 xl:grid-cols-2"><div className="grid gap-4 sm:grid-cols-2">{overview.cards.map((card, index) => <article className="panel p-5" key={card.title}><p className="eyebrow">{cardCopy[index][0]}</p><h3 className="mt-3 text-xl font-semibold">{cardCopy[index][1]}</h3><p className="mt-2 text-sm leading-6 text-muted">{cardCopy[index][2]}</p></article>)}</div><MultiColorBarChart data={journeys.outcome_distribution} category="outcome" value="accounts" title="Desfechos observados das jornadas" subtitle="Contas · jornada completa observada · população principal" summary="Os desfechos observados são classificações descritivas e não implicam comportamento futuro." /></section>
    <div className="mt-8"><LimitationCallout>Toda evidência é histórica até 31 de dez. de 2024. MRR associado não representa receita em risco. As filas exigem revisão humana e cada hipótese experimental continua não testada.</LimitationCallout></div>
    <div className="mt-8 flex flex-wrap gap-3"><Link className="button-primary" href="/demo">Iniciar demonstração guiada de 3 minutos</Link><Link className="button-secondary" href="/methodology">Ler metodologia</Link></div>
  </div>;
}
