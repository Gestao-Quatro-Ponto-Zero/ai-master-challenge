import Icon from "../ui/icon";
export default function Sidebar({
  data,
  view,
  collapsed,
  ready,
  progress,
  due,
  setView,
  setLimit,
  setPreference,
  showDailyProgress,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brandrow">
        <a href="/" className="brand" aria-label="G4 Sales Priority início">
          <img
            className="official-logo"
            src="/brand/g4-original-white.svg"
            alt="G4"
            width="101"
            height="40"
          />
          <span className="brand-divider" />
          <span>
            SALES<span className="brand-sub">PRIORITY</span>
          </span>
        </a>
        <button
          className="sidebar-toggle"
          aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expandir menu" : "Recolher menu"}
          onClick={() => setPreference("collapsed", !collapsed)}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            aria-hidden="true"
          >
            <rect x="3" y="4" width="18" height="16" rx="3" />
            <path d="M9 4v16" />
            {collapsed ? (
              <path d="m13 9 3 3-3 3" />
            ) : (
              <path d="m16 9-3 3 3 3" />
            )}
          </svg>
          <span>Recolher menu</span>
        </button>
      </div>
      <div className="workspace-label">ESPAÇO COMERCIAL</div>
      <nav aria-label="Navegação principal">
        {[
          ["today", "bolt", "Meu dia"],
          ["pipeline", "funnel", "Meu pipeline"],
          ["results", "chart", "Resultados"],
          ["method", "book", "Entenda as prioridades"],
        ].map(([id, icon, label]) => (
          <button
            key={id}
            aria-current={view === id ? "page" : undefined}
            className={"nav-item " + (view === id ? "active" : "")}
            title={collapsed ? label : undefined}
            onClick={() => {
              setView(id);
              setLimit(20);
            }}
          >
            <span className="nav-icon">
              <Icon name={icon} />
            </span>
            <span className="nav-label">{label}</span>
            {id === "today" && due.length > 0 && (
              <span className="nav-count">{due.length}</span>
            )}
          </button>
        ))}
      </nav>
      <button className="daily-meter" onClick={showDailyProgress}>
        <div className="meter-head">
          <Icon name="target" size={17} />
          <span>SEU PLANO DE HOJE</span>
        </div>
        <div
          className="meter-ring"
          style={{
            "--progress": `${progress.percent}%`,
          }}
        >
          <div>
            <strong>
              {progress.completed}
              <small>/{progress.total}</small>
            </strong>
            <span>concluídas</span>
          </div>
        </div>
        <strong>
          {!ready
            ? "Preparando seu plano"
            : !progress.total
              ? "Nenhuma tarefa para hoje"
              : progress.completed === progress.total
                ? "Plano do dia concluído"
                : `${progress.total - progress.completed} tarefas para avançar`}
        </strong>
        <p>
          {progress.batches.length
            ? `${progress.completedBatches}/${progress.batches.length} rodadas concluídas · até 5 por rodada`
            : "Até 4 lotes de 5, conforme a carteira."}
        </p>
        <span className="meter-link">
          Ver progresso do dia <Icon name="arrow" size={13} />
        </span>
      </button>
      <div className="side-footer">
        <span className="live-dot" />
        {data.source === "supabase"
          ? "Base no Supabase"
          : "Base pública carregada"}
        <small>Atividades salvas neste navegador</small>
        <span className="challenge">Challenge 003 · Projeto demonstrativo</span>
      </div>
    </aside>
  );
}
