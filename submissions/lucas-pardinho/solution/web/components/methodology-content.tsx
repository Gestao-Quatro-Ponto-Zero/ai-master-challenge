import {
  AlertTriangle,
  ArrowRight,
  Braces,
  CheckCircle2,
  Clock3,
  Database,
  FlaskConical,
  GitCompareArrows,
  Scale,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { summarizeOpportunities } from "@/lib/analytics";
import { formatNumber } from "@/lib/format";
import { QUEUES, type DataQualityReport, type DataStatus, type ModelReport, type Opportunity } from "@/lib/types";
import { DataSourcePill } from "@/components/data-source-pill";
import { PageHeader } from "@/components/page-header";
import { QueueBadge } from "@/components/queue-badge";

export function MethodologyContent({
  opportunities,
  modelReport,
  dataQuality,
  status,
}: {
  opportunities: Opportunity[];
  modelReport: ModelReport;
  dataQuality: DataQualityReport;
  status: DataStatus;
}) {
  const metrics = summarizeOpportunities(opportunities);
  const reportFacts = flattenPrimitiveFacts(modelReport).slice(0, 8);

  return (
    <div className="page methodology-page">
      <PageHeader
        eyebrow="Metodologia e governança"
        title="Um score que explica antes de recomendar"
        description="O G4 Focus organiza evidência histórica em decisões simples — com limites, confiança e qualidade visíveis."
        icon={FlaskConical}
        action={<DataSourcePill status={status} />}
      />

      <section className="method-hero">
        <div>
          <p className="section-kicker">Princípio de produto</p>
          <h2>Probabilidade sem ação é só um número.</h2>
          <p>O score combina chance de conversão, urgência comercial e valor. Depois traduz o resultado em uma fila e em um próximo passo que o vendedor consegue executar.</p>
        </div>
        <div className="method-flow" aria-label="Fluxo do score">
          <span><Database size={18} /> CRM real</span><ArrowRight size={15} />
          <span><Clock3 size={18} /> Snapshots</span><ArrowRight size={15} />
          <span><Braces size={18} /> Score</span><ArrowRight size={15} />
          <span><Sparkles size={18} /> Ação</span>
        </div>
      </section>

      <section className="method-grid formula-section">
        <article className="panel formula-card">
          <div className="panel-heading">
            <div><p className="section-kicker">Score de prioridade</p><h2>65 + 20 + 15</h2></div>
            <span className="formula-total">100 pontos</span>
          </div>
          <div className="formula-bar" aria-label="65% conversão, 20% momento de ação, 15% valor">
            <span className="conversion" style={{ width: "65%" }}>65%</span>
            <span className="actionability" style={{ width: "20%" }}>20%</span>
            <span className="value" style={{ width: "15%" }}>15%</span>
          </div>
          <div className="formula-legend">
            <div><span className="legend-dot conversion" /><strong>Conversão · 65%</strong><p>Chance histórica de avançar para Won dentro da janela de decisão.</p></div>
            <div><span className="legend-dot actionability" /><strong>Momento de ação · 20%</strong><p>Recência e posição do deal em relação ao ciclo comercial saudável.</p></div>
            <div><span className="legend-dot value" /><strong>Valor · 15%</strong><p>Potencial econômico normalizado, sem deixar ticket dominar o ranking.</p></div>
          </div>
        </article>

        <article className="panel two-track-card">
          <div className="panel-heading"><div><p className="section-kicker">Dois problemas, dois scores</p><h2>Engajar ≠ qualificar</h2></div></div>
          <div className="track-list">
            <div className="track-item">
              <span className="track-number">01</span>
              <div><strong>Deals em Engaging</strong><p>Recebem probabilidade e score de prioridade porque já têm tempo de pipeline e sinais comparáveis; conta ausente reduz a confiança e vira alerta.</p></div>
              <Target size={22} />
            </div>
            <div className="track-item">
              <span className="track-number">02</span>
              <div><strong>Leads em Prospecting</strong><p>Recebem score de qualificação separado. A ausência de engajamento não vira uma falsa probabilidade de fechamento.</p></div>
              <GitCompareArrows size={22} />
            </div>
          </div>
        </article>
      </section>

      <section className="panel queue-method-section">
        <div className="panel-heading">
          <div><p className="section-kicker">Camada de decisão</p><h2>Do score para a rotina comercial</h2></div>
          <span className="ranking-caption">5 filas mutuamente exclusivas</span>
        </div>
        <div className="queue-method-grid">
          {QUEUES.map((queue) => {
            const summary = metrics.queues.find((item) => item.queue === queue);
            return (
              <article key={queue}>
                <QueueBadge queue={queue} />
                <strong>{formatNumber(summary?.count ?? 0)} deals</strong>
                <p>{queueExplanation(queue)}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="method-grid governance-grid">
        <article className="panel governance-card" id="confianca">
          <div className="governance-icon green"><ShieldCheck size={22} /></div>
          <p className="section-kicker">Confiança</p>
          <h2>A recomendação mostra o quanto sabe</h2>
          <p>Alta, média ou baixa confiança acompanha cada score. Volume de histórico, completude dos campos e estabilidade dos sinais entram nessa leitura.</p>
          <div className="confidence-stack">
            <span><i className="high" /><strong>Alta</strong><small>{formatNumber(metrics.confidence.high)} deals</small></span>
            <span><i className="medium" /><strong>Média</strong><small>{formatNumber(metrics.confidence.medium)} deals</small></span>
            <span><i className="low" /><strong>Baixa</strong><small>{formatNumber(metrics.confidence.low)} deals</small></span>
          </div>
        </article>

        <article className="panel governance-card" id="qualidade">
          <div className="governance-icon amber"><AlertTriangle size={22} /></div>
          <p className="section-kicker">Qualidade e transparência</p>
          <h2>Sem esconder a incerteza do CRM</h2>
          <p>{formatNumber(metrics.dataIssueDeals)} oportunidades carregam ao menos um alerta. Essas flags permanecem visíveis no detalhe, em vez de serem silenciosamente imputadas.</p>
          <ul className="governance-list">
            <li><CheckCircle2 size={15} /> Normalização explícita de <code>GTXPro</code> para <code>GTX Pro</code></li>
            <li><CheckCircle2 size={15} /> Conta ou data ausente vira flag de qualidade</li>
            <li><CheckCircle2 size={15} /> Prospecting não recebe probabilidade artificial</li>
          </ul>
        </article>

        <article className="panel governance-card">
          <div className="governance-icon blue"><Scale size={22} /></div>
          <p className="section-kicker">Validação honesta</p>
          <h2>O futuro não treina o passado</h2>
          <p>Quando há modelagem preditiva, o corte é temporal e a mesma oportunidade não aparece nos dois lados da avaliação. Features pós-fechamento ficam fora do score.</p>
          <ul className="governance-list">
            <li><CheckCircle2 size={15} /> Split temporal por snapshot</li>
            <li><CheckCircle2 size={15} /> Agrupamento por oportunidade</li>
            <li><CheckCircle2 size={15} /> Sem close date, close value ou stage final como feature</li>
          </ul>
        </article>
      </section>

      <section className="method-grid evidence-grid">
        <article className="panel evidence-card">
          <div className="panel-heading"><div><p className="section-kicker">Evidências da execução</p><h2>Relatório do motor</h2></div></div>
          {reportFacts.length ? (
            <dl className="report-facts">
              {reportFacts.map(([key, value]) => <div key={key}><dt>{humanize(key)}</dt><dd>{String(value)}</dd></div>)}
            </dl>
          ) : (
            <p className="muted-copy">Execute a pipeline para preencher as métricas do modelo.</p>
          )}
        </article>
        <article className="panel limits-card">
          <div className="panel-heading"><div><p className="section-kicker">Limites conscientes</p><h2>O que este MVP ainda não faz</h2></div></div>
          <ol className="limits-list">
            <li><span>01</span><p><strong>Não substitui o CRM</strong>Consome um snapshot. Em produção, precisaria de sincronização incremental e monitoramento.</p></li>
            <li><span>02</span><p><strong>Não mede causalidade</strong>O score prioriza correlação histórica; não promete que uma ação específica causará o fechamento.</p></li>
            <li><span>03</span><p><strong>Não automatiza decisão humana</strong>O vendedor mantém o contexto da conta e pode contrariar a recomendação com justificativa.</p></li>
          </ol>
        </article>
      </section>

      <details className="technical-details">
        <summary>Ver artefatos técnicos carregados</summary>
        <div>
          <section><h3>Model report</h3><pre>{JSON.stringify(modelReport, null, 2)}</pre></section>
          <section><h3>Data quality</h3><pre>{JSON.stringify(dataQuality, null, 2)}</pre></section>
        </div>
      </details>
    </div>
  );
}

function queueExplanation(queue: (typeof QUEUES)[number]): string {
  return {
    "Foco agora": "Alta chance e bom timing. Ação direta no próximo bloco comercial.",
    Acelerar: "Sinais promissores que pedem remoção de objeção e data de decisão.",
    Nutrir: "Potencial moderado. Cadência leve até surgir um sinal de urgência.",
    "Resgatar ou desqualificar": "Ciclo excedido. Última tentativa com prazo ou encerramento limpo.",
    Qualificar: "Lead ainda sem evidência comparável. Primeiro descobrir conta, dor e potencial.",
  }[queue];
}

function flattenPrimitiveFacts(value: unknown, prefix = ""): Array<[string, string | number | boolean]> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  const facts: Array<[string, string | number | boolean]> = [];
  for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") facts.push([path, item]);
    else if (item && typeof item === "object" && !Array.isArray(item)) facts.push(...flattenPrimitiveFacts(item, path));
  }
  return facts;
}

function humanize(value: string): string {
  return value
    .split(".")
    .at(-1)!
    .replaceAll("_", " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^./, (letter) => letter.toUpperCase());
}
