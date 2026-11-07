import { HEALTH_POLICY } from "../../lib/health.mjs";
export function HealthPill({ deal }) {
  const health = deal.healthDetails;
  if (!health) return null;
  return (
    <span className={`health-pill health-pill-${health.tone}`}>
      {health.score === null
        ? health.label
        : `${health.score}/100 · ${health.label}`}
    </span>
  );
}

export default function HealthSummary({ deal }) {
  const health = deal.healthDetails;
  if (!health) return null;
  return (
    <section className="health-summary" aria-label="Saúde comercial explicada">
      <div className={`health-line health-${health.tone}`}>
        <span>Saúde comercial</span>
        <strong>
          {health.score === null
            ? health.label
            : `${health.score}/100 · ${health.label}`}
        </strong>
      </div>
      <p className="health-description">{health.summary}</p>
      {!["won", "lost"].includes(deal.status) && (
        <>
          <small>
            {health.coverage}% dos critérios informados · {health.unknownPoints}{" "}
            pontos ainda desconhecidos
          </small>
          <ul className="health-factors">
            {health.factors.map((f) => (
              <li key={f.key}>
                <div>
                  <strong>{f.label}</strong>
                  <span>
                    {f.known ? `${f.points}/${f.max}` : "A confirmar"}
                  </span>
                </div>
                <small>{f.explanation}</small>
              </li>
            ))}
          </ul>
          <p className="health-disclosure">
            Informações declaradas pelo vendedor. Regras de piloto, não
            probabilidade de venda. Janela de conversa: 7 dias; reconfirmação:
            30 dias.
          </p>
        </>
      )}
    </section>
  );
}
