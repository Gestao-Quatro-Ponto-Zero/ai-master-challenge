import Icon from "../../components/ui/icon";
import { Kpi, SectionTitle } from "../../components/ui/primitives";
import { fmt, usd, dateLabel } from "../../lib/format.mjs";
import { eventNames } from "../../lib/activity.mjs";
import { STAGES, funnelCounts } from "../../lib/workflow.mjs";
import SalesFunnel from "./sales-funnel";
export default function ResultsReport({ deals, historical, events }) {
  const counts = funnelCounts(deals),
    ids = new Set(deals.map((d) => d.opportunity_id)),
    cohort = deals.filter((d) =>
      d.activities.some((e) => e.type !== "profile" && e.type !== "note"),
    );
  const everQualified = cohort.filter((d) => d.qualification).length,
    won = cohort.filter((d) => d.status === "won"),
    lost = cohort.filter((d) => d.status === "lost"),
    contacted = deals.filter((d) =>
      d.activities.some((e) => e.type === "contact"),
    ).length;
  const hWon = historical.reduce((n, h) => n + h.won, 0),
    hLost = historical.reduce((n, h) => n + h.lost, 0),
    hRevenue = historical.reduce((n, h) => n + h.revenue, 0),
    total = deals.length + hWon + hLost;
  const stageHistory = [
    {
      label: "Prospecção",
      count: deals.filter((d) => d.deal_stage === "Prospecting").length,
    },
    {
      label: "Em negociação",
      count: deals.filter((d) => d.deal_stage === "Engaging").length,
    },
    {
      label: "Ganhas",
      count: hWon,
    },
    {
      label: "Perdidas",
      count: hLost,
    },
  ];
  const ratio = (n, d) =>
    d ? `${((n / d) * 100).toFixed(1).replace(".", ",")}%` : "—";
  return (
    <>
      <section className="panel results-panel">
        <SectionTitle
          eyebrow="EXECUÇÃO REGISTRADA NESTA DEMONSTRAÇÃO"
          title="O que avançou depois da priorização?"
          subtitle="Mesma carteira inicial. Ações que você registrar aqui, sem misturar com os fechamentos de 2017."
          right={<span className="small-tag">Neste navegador</span>}
        />
        <div className="kpi-grid results-kpis">
          <Kpi
            icon="phone"
            label="Oportunidades contatadas"
            value={contacted}
            note="IDs únicos com contato registrado"
          />
          <Kpi
            icon="target"
            label="SQLs confirmados"
            value={everQualified}
            note="Inclui os que avançaram ou fecharam"
          />
          <Kpi
            icon="trophy"
            label="Vendas registradas"
            value={won.length}
            note={`${usd.format(won.reduce((n, d) => n + d.actualValue, 0))} em receita informada`}
          />
          <article className="kpi">
            <div className="kpi-top">
              <span>Ganho entre os encerrados</span>
              <Icon name="chart" size={17} />
            </div>
            <strong>{ratio(won.length, won.length + lost.length)}</strong>
            <small>
              {won.length} ganhas / {won.length + lost.length} encerradas na
              demo
            </small>
          </article>
        </div>
        <div className="results-funnel-layout">
          <SalesFunnel
            steps={[
              {
                label: "Trabalhadas",
                n: cohort.length,
                tone: "contacted",
              },
              {
                label: "SQLs confirmados",
                n: everQualified,
                tone: "qualified",
              },
              {
                label: "Com proposta",
                n: cohort.filter((d) =>
                  d.activities.some((e) => e.type === "proposal"),
                ).length,
                tone: "proposal",
              },
              {
                label: "Vendas ganhas",
                n: won.length,
                tone: "won",
              },
            ]}
          />
          <div className="conversion-track">
            {[
              {
                label: "Trabalhadas",
                n: cohort.length,
              },
              {
                label: "Qualificadas em algum momento",
                n: everQualified,
              },
              {
                label: "Proposta em algum momento",
                n: cohort.filter((d) =>
                  d.activities.some((e) => e.type === "proposal"),
                ).length,
              },
              {
                label: "Vendas ganhas",
                n: won.length,
              },
            ].map((s, i) => (
              <div className={`conversion-step funnel-step-${i}`} key={s.label}>
                <span>0{i + 1}</span>
                <strong>{s.n}</strong>
                <p>{s.label}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="measurement-note">
          Contagens cumulativas da mesma carteira, não taxas entre etapas: há
          caminhos que podem pular contato ou proposta. SQL → venda:{" "}
          {ratio(won.length, everQualified)} ({won.length}/{everQualified}).
          Isso acompanha execução; não comprova aumento de vendas causado pelo
          score.
        </p>
        <div className="status-strip">
          {STAGES.map((s) => (
            <span key={s.id}>
              <i className={"stage-dot " + s.id} />
              {s.label}
              <strong>{counts[s.id]}</strong>
            </span>
          ))}
        </div>
      </section>
      <section className="panel results-panel historical-panel">
        <SectionTitle
          eyebrow="BASE ORIGINAL · RETRATO EM 31 DEZ 2017"
          title="Como estava a carteira no CRM?"
          subtitle="Distribuição por estágio, sem inferir transições que o dataset não registra."
        />
        <div className="historical-layout">
          <div className="historical-bars">
            {stageHistory.map((s, i) => (
              <div key={s.label}>
                <div>
                  <span>{s.label}</span>
                  <strong>{fmt.format(s.count)}</strong>
                </div>
                <div className="history-track">
                  <span
                    className={"history-bar h" + i}
                    style={{
                      width: `${total ? (s.count / total) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="historical-numbers">
            <article>
              <span>Taxa de ganho histórica</span>
              <strong>{ratio(hWon, hWon + hLost)}</strong>
              <small>
                {fmt.format(hWon)} ganhas / {fmt.format(hWon + hLost)}{" "}
                encerradas
              </small>
            </article>
            <article>
              <span>Receita histórica realizada</span>
              <strong>{usd.format(hRevenue)}</strong>
              <small>Valor de fechamento; usado apenas em resultados.</small>
            </article>
          </div>
        </div>
        <p className="measurement-note">
          Não há histórico de contatos ou SQL na base original. Não podemos
          afirmar quantos leads viraram SQLs em 2017. Os novos registros
          constroem essa evidência a partir de agora.
        </p>
      </section>
      <section className="panel results-panel">
        <SectionTitle title="Últimos movimentos da carteira" />
        <div className="activity-feed">
          {events
            .filter((e) => ids.has(e.opportunityId))
            .slice(-8)
            .reverse()
            .map((e) => (
              <div key={e.id}>
                <span className="feed-icon">
                  <Icon
                    name={e.type === "won" ? "trophy" : "check"}
                    size={17}
                  />
                </span>
                <div>
                  <strong>{eventNames[e.type]}</strong>
                  <p>
                    {deals.find((d) => d.opportunity_id === e.opportunityId)
                      ?.account || "Conta a identificar"}{" "}
                    · {e.agent}
                  </p>
                </div>
                <small>{dateLabel(e.at)}</small>
              </div>
            ))}
          {!events.some((e) => ids.has(e.opportunityId)) && (
            <p className="muted">
              Nenhum movimento nesta seleção. Comece por “Meu dia”.
            </p>
          )}
        </div>
      </section>
    </>
  );
}
