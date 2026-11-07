import { HealthPill } from "./health-summary";
import { isClosed } from "../../lib/workflow.mjs";
import Icon from "../../components/ui/icon";
import { Score } from "../../components/ui/primitives";
import { usd, dateLabel } from "../../lib/format.mjs";
export default function DealCard({ deal: d, onClick, onDragStart, onDragEnd }) {
  return (
    <button
      className={`deal-card stage-${d.status}`}
      onClick={onClick}
      draggable={!!onDragStart && !isClosed(d)}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      aria-label={`${d.account || "Conta a identificar"} · ${d.opportunity_id} · abrir ou arrastar para avançar`}
    >
      <div className="deal-card-top">
        <span className="tiny-label">
          {d.qualification
            ? "SQL CONFIRMADO"
            : d.review
              ? "REVISAR CONTEXTO"
              : "A QUALIFICAR"}
        </span>
        <Score deal={d} />
      </div>
      <h3>{d.account || "Conta a identificar"}</h3>
      <HealthPill deal={d} />
      <p>
        {d.product} · {usd.format(d.quote?.amount || d.sales_price)}{" "}
        {d.quote ? "proposta informada" : "catálogo"}
      </p>
      <div className="deal-card-next">
        <Icon name={d.nextTask ? "clock" : "arrow"} size={13} />
        <span>
          {d.nextTask
            ? d.nextTask.label
            : !d.account
              ? "Completar cadastro"
              : d.review
                ? "Validar continuidade"
                : "Confirmar próximo passo"}
        </span>
      </div>
      {d.nextTask && (
        <small className={d.overdue ? "overdue-text" : ""}>
          {d.overdue ? "Vencido · " : ""}
          {dateLabel(d.nextTask.dueAt)}
        </small>
      )}
      <div className="deal-card-footer">
        <span>
          #{d.opportunity_id} ·{" "}
          {d.age === null
            ? "Sem data de negociação"
            : `${d.age} dias no snapshot`}
        </span>
        <Icon name="arrow" size={14} />
      </div>
    </button>
  );
}
