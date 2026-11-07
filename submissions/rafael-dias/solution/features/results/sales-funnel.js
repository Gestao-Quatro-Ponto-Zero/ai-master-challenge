export default function SalesFunnel({ steps }) {
  return (
    <section
      className="funnel-visual"
      aria-label="Funil da execução registrada"
    >
      <div className="funnel-caption">
        <span>DA CONVERSA AO FECHAMENTO</span>
        <h3>Avanço das oportunidades</h3>
      </div>
      <div className="funnel-contents">
        <div className="funnel-shapes" aria-hidden="true">
          {steps.map((s, i) => (
            <i
              key={s.tone}
              className={`shape-${s.tone}`}
              style={{
                width: `${100 - i * 17}%`,
              }}
            />
          ))}
        </div>
        <ol className="funnel-legend">
          {steps.map((s, i) => (
            <li key={s.tone} className={`legend-${s.tone}`}>
              <span className="funnel-marker">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="funnel-label">{s.label}</span>
              <strong>{s.n}</strong>
            </li>
          ))}
        </ol>
      </div>
      <p>
        Esquema ilustrativo · números reais dos registros. Etapas podem ser
        puladas.
      </p>
    </section>
  );
}
