import { HealthPill } from "../opportunities/health-summary";
import Icon from "../../components/ui/icon";
import { SectionTitle, Score, Empty } from "../../components/ui/primitives";
import { usd, initials } from "../../lib/format.mjs";
import { reasonFor } from "../../lib/workflow.mjs";
import DailyCheckpoints from "./daily-checkpoints";
export default function FocusQueue({ top, progress, onOpenDeal }) {
  return (
    <section className="focus-section">
      <SectionTitle
        eyebrow="A PRÓXIMA CONVERSA IMPORTA"
        title="Seu foco agora"
        subtitle="Poucas oportunidades. Um motivo claro para agir."
      />
      {top[0] ? (
        <article className="hero-deal">
          <div className="hero-top">
            <span className="hero-flag">
              <Icon name="bolt" size={14} />
              {top[0].priority?.label || "PRIORIDADE DA CARTEIRA"}
            </span>
            <Score deal={top[0]} large />
          </div>
          <div className="hero-client">
            <div className="company-avatar">{initials(top[0].account)}</div>
            <div>
              <h2>{top[0].account || "Conta a identificar"}</h2>
              <p>
                {top[0].sector || "Setor não informado"} <span>·</span>{" "}
                {top[0].location || "Localização não informada"}
              </p>
            </div>
          </div>
          <HealthPill deal={top[0]} />
          <div className="hero-product">
            <span>{top[0].product}</span>
            <strong>
              {usd.format(top[0].quote?.amount || top[0].sales_price)}{" "}
              <small>
                {top[0].quote ? "/ proposta informada" : "/ preço de catálogo"}
              </small>
            </strong>
          </div>
          <div className="hero-reason">
            <Icon name="info" size={17} />
            <div>
              <strong>Por que agir agora?</strong>
              <p>{reasonFor(top[0])}</p>
            </div>
          </div>
          <div className="hero-bottom">
            <span>
              <span className="live-dot" />
              {top[0].qualification
                ? "SQL confirmado"
                : "Qualificação ainda não confirmada"}
            </span>
            <button
              className="button primary"
              onClick={() => onOpenDeal(top[0].opportunity_id)}
            >
              Trabalhar oportunidade <Icon name="arrow" size={16} />
            </button>
          </div>
        </article>
      ) : (
        <Empty
          title="Sua fila está em dia"
          text="Confira os retornos ou abra a carteira para qualificar novas contas."
        />
      )}
      <div className="next-list">
        {top.slice(1).map((d, i) => (
          <button
            className="next-card"
            key={d.opportunity_id}
            onClick={() => onOpenDeal(d.opportunity_id)}
          >
            <span className="rank">0{i + 2}</span>
            <div className="next-client">
              <strong>{d.account || "Conta a identificar"}</strong>
              <span>
                {d.product} · {usd.format(d.sales_price)} catálogo · #
                {d.opportunity_id}
              </span>
              <p>
                {d.overdue
                  ? "Retorno vencido"
                  : d.review
                    ? "Validar continuidade da negociação"
                    : d.deal_stage === "Prospecting"
                      ? "Descobrir necessidade e decisor"
                      : "Confirmar decisão e próximo passo"}
              </p>
            </div>
            <Score deal={d} />
            <Icon name="arrow" size={17} />
          </button>
        ))}
      </div>
      <DailyCheckpoints progress={progress} />
    </section>
  );
}
