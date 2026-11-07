import Icon from "../../components/ui/icon";
import Results from "./results-report";
export default function ResultsView({
  data,
  agent,
  all,
  scoped,
  scope,
  manager,
  region,
  events,
  setScope,
  setManager,
  setRegion,
  exportActivities,
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ATIVIDADE PRECISA VIRAR RESULTADO</div>
          <h1>
            Da oportunidade à venda<span className="gold">.</span>
          </h1>
          <p>
            Acompanhe sua execução e compare com o retrato histórico da empresa.
          </p>
        </div>
        <button className="button secondary" onClick={exportActivities}>
          <Icon name="download" size={16} />
          Exportar atividades
        </button>
      </div>
      <div className="results-filters">
        <div className="segmented">
          <button
            className={scope === "mine" ? "active" : ""}
            onClick={() => setScope("mine")}
          >
            Minha carteira
          </button>
          <button
            className={scope === "company" ? "active" : ""}
            onClick={() => setScope("company")}
          >
            Empresa · 35 vendedores
          </button>
        </div>
        <label>
          Gestor
          <select
            aria-label="Filtrar resultados por gestor"
            value={manager}
            onChange={(e) => setManager(e.target.value)}
          >
            <option value="">Todos</option>
            {[...new Set(all.map((d) => d.manager))].sort().map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Região
          <select
            aria-label="Filtrar resultados por região"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            <option value="">Todas</option>
            {[...new Set(all.map((d) => d.regional_office))].sort().map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
      </div>
      <Results
        deals={scoped}
        historical={(data.historicalByAgent || []).filter(
          (h) =>
            (scope === "company" || h.sales_agent === agent) &&
            (!manager || h.manager === manager) &&
            (!region || h.regional_office === region),
        )}
        events={events}
      />
    </>
  );
}
