import Icon from "./icon";
import { fmt } from "../../lib/format.mjs";
import { scoreBand } from "../../lib/presentation.mjs";
export function Kpi({ icon, label, value, note, tone = "" }) {
  return (
    <article className={"kpi " + tone}>
      <div className="kpi-top">
        <span>{label}</span>
        <Icon name={icon} size={17} />
      </div>
      <strong>{fmt.format(value)}</strong>
      <small>{note}</small>
    </article>
  );
}
export function SectionTitle({ eyebrow, title, subtitle, right }) {
  return (
    <div className="section-title">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}
export function Score({ deal, large = false }) {
  const band = scoreBand(deal.score);
  return (
    <div
      className={`score-badge score-${band.tone} ${large ? "large" : ""}`}
      title="Índice de prioridade; não probabilidade de fechamento."
    >
      <strong>{deal.score}</strong>
      <span>{large ? band.label : "/100"}</span>
    </div>
  );
}
export function Empty({ title, text }) {
  return (
    <div className="empty-state">
      <Icon name="target" size={30} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
