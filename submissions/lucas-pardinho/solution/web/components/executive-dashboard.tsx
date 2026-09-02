import Link from "next/link";
import {
  ArrowRight,
  CircleDollarSign,
  Clock3,
  Crosshair,
  DatabaseZap,
  Info,
  MapPinned,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { summarizeOpportunities } from "@/lib/analytics";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import type { DataStatus, Opportunity } from "@/lib/types";
import { DataSourcePill } from "@/components/data-source-pill";
import { PageHeader } from "@/components/page-header";
import { QueueBadge, queueClass } from "@/components/queue-badge";
import { ScoreRing } from "@/components/score-ring";

export function ExecutiveDashboard({
  opportunities,
  status,
}: {
  opportunities: Opportunity[];
  status: DataStatus;
}) {
  const metrics = summarizeOpportunities(opportunities);
  const maxQueue = Math.max(...metrics.queues.map((item) => item.count), 1);
  const highConfidenceShare = metrics.openDeals
    ? Math.round((metrics.confidence.high / metrics.openDeals) * 100)
    : 0;

  return (
    <div className="page executive-page">
      <PageHeader
        eyebrow="Visão executiva"
        title="Onde o time deve colocar energia agora?"
        description="Uma leitura acionável do pipeline: prioridade, potencial e risco em uma única visão."
        icon={Sparkles}
        action={<DataSourcePill status={status} />}
      />

      <section className="decision-callout" aria-label="Recomendação principal">
        <div className="callout-icon"><Crosshair size={21} aria-hidden="true" /></div>
        <div>
          <span className="callout-label">Decisão da semana</span>
          <strong>
            Comece pelos {formatNumber(metrics.focusNow)} deals em <em>Foco agora</em> e revise os {formatNumber(metrics.staleDeals)} que perderam tração.
          </strong>
          <p>O ranking equilibra chance de conversão, momento de ação e valor — nunca apenas ticket.</p>
        </div>
        <Link href="/pipeline?queue=Foco%20agora" className="button primary">
          Abrir fila prioritária <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </section>

      <section className="metrics-grid" aria-label="Indicadores principais">
        <MetricCard
          label="Pipeline aberto"
          value={formatNumber(metrics.openDeals)}
          detail={`${formatCurrency(metrics.estimatedPipeline)} em valor estimado`}
          icon={TrendingUp}
          tone="neutral"
        />
        <MetricCard
          label="Pipeline ponderado"
          value={formatCurrency(metrics.weightedPipeline)}
          detail="Valor ajustado pela chance de ganho"
          icon={CircleDollarSign}
          tone="green"
        />
        <MetricCard
          label="Foco agora"
          value={formatNumber(metrics.focusNow)}
          detail="Melhor relação entre chance e timing"
          icon={Crosshair}
          tone="lime"
        />
        <MetricCard
          label="Deals em risco"
          value={formatNumber(metrics.staleDeals)}
          detail="Resgatar com prazo ou desqualificar"
          icon={Clock3}
          tone="red"
        />
      </section>

      <section className="dashboard-grid primary-grid">
        <article className="panel queue-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Alocação do esforço</p>
              <h2>Filas recomendadas</h2>
            </div>
            <Link href="/pipeline" className="text-link">Ver pipeline <ArrowRight size={14} /></Link>
          </div>
          <p className="panel-intro">Cada oportunidade cai em uma fila com um próximo passo coerente com o seu momento.</p>
          <div className="queue-bars">
            {metrics.queues.map((item) => (
              <Link
                href={`/pipeline?queue=${encodeURIComponent(item.queue)}`}
                className="queue-row"
                key={item.queue}
              >
                <div className="queue-row-top">
                  <QueueBadge queue={item.queue} compact />
                  <span><strong>{formatNumber(item.count)}</strong> deals · {formatCurrency(item.estimatedValue)}</span>
                </div>
                <span className="bar-track" aria-hidden="true">
                  <span
                    className={`bar-fill ${queueClass(item.queue)}`}
                    style={{ width: `${Math.max(3, (item.count / maxQueue) * 100)}%` }}
                  />
                </span>
              </Link>
            ))}
          </div>
        </article>

        <article className="panel priority-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Próximas ações</p>
              <h2>Oportunidades no radar</h2>
            </div>
            <span className="ranking-caption">ordenado por score</span>
          </div>
          <div className="priority-list">
            {metrics.topOpportunities.slice(0, 5).map((opportunity) => (
              <Link
                href={`/pipeline?selected=${encodeURIComponent(opportunity.opportunityId)}`}
                key={opportunity.opportunityId}
                className="priority-item"
              >
                <ScoreRing opportunity={opportunity} size="sm" />
                <span className="priority-copy">
                  <span className="priority-title">
                    <strong>{opportunity.account ?? "Conta a qualificar"}</strong>
                    <small>{opportunity.product}</small>
                  </span>
                  <span className="priority-reason">{opportunity.reasons[0] ?? opportunity.nextAction}</span>
                </span>
                <span className="priority-value">
                  <strong>{formatCurrency(opportunity.estimatedValue)}</strong>
                  <small>{formatPercent(opportunity.probability)} chance</small>
                </span>
                <ArrowRight className="row-arrow" size={16} aria-hidden="true" />
              </Link>
            ))}
            {metrics.topOpportunities.length === 0 ? (
              <div className="empty-state compact">
                <Info size={18} aria-hidden="true" />
                Nenhum deal está nas filas prioritárias neste recorte.
              </div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="dashboard-grid signal-grid">
        <article className="panel signal-card">
          <div className="signal-icon green"><ShieldCheck size={20} aria-hidden="true" /></div>
          <div>
            <p className="section-kicker">Confiança</p>
            <h3>{highConfidenceShare}% com evidência alta</h3>
            <p>{formatNumber(metrics.confidence.high)} recomendações sustentadas por histórico suficiente.</p>
          </div>
          <Link href="/metodologia#confianca" className="small-link">Como calculamos</Link>
        </article>

        <article className="panel signal-card">
          <div className="signal-icon amber"><DatabaseZap size={20} aria-hidden="true" /></div>
          <div>
            <p className="section-kicker">Qualidade dos dados</p>
            <h3>{formatNumber(metrics.dataIssueDeals)} deals com alertas</h3>
            <p>Flags aparecem junto da recomendação para evitar falsa precisão.</p>
          </div>
          <Link href="/metodologia#qualidade" className="small-link">Ver controles</Link>
        </article>

        <article className="panel signal-card regional-card">
          <div className="signal-icon blue"><MapPinned size={20} aria-hidden="true" /></div>
          <div className="regional-copy">
            <p className="section-kicker">Cobertura regional</p>
            <h3>{metrics.regions.length} escritórios no recorte</h3>
            <div className="region-mini-list">
              {metrics.regions.slice(0, 3).map((region) => (
                <span key={region.name}>
                  <strong>{region.name}</strong>
                  <small>{formatNumber(region.count)} deals</small>
                </span>
              ))}
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof TrendingUp;
  tone: "neutral" | "green" | "lime" | "red";
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-top">
        <span>{label}</span>
        <span className="metric-icon"><Icon size={18} aria-hidden="true" /></span>
      </div>
      <strong className="metric-value">{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
