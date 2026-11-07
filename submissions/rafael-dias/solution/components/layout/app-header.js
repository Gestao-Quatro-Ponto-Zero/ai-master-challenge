import AgentPicker from "../../features/workspace/agent-picker";
export default function AppHeader({
  titles,
  view,
  dark,
  setPreference,
  agents,
  agent,
  changeAgent,
  data,
  openCounts,
}) {
  return (
    <header className="topbar">
      <div className="breadcrumb">
        Comercial <span>/</span>
        <strong>{titles[view]}</strong>
      </div>
      <div className="top-controls">
        <span className="demo-label">DEMO · SEM LOGIN</span>
        <button
          className="theme-switch"
          role="switch"
          aria-checked={dark}
          aria-label="Modo escuro"
          title={dark ? "Mudar para modo claro" : "Mudar para modo escuro"}
          onClick={() => setPreference("dark", !dark)}
        >
          <svg
            viewBox="0 0 24 24"
            width="15"
            height="15"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2" />
          </svg>
          <svg
            viewBox="0 0 24 24"
            width="15"
            height="15"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            aria-hidden="true"
          >
            <path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11z" />
          </svg>
          <span className="theme-thumb" />
        </button>
        <AgentPicker
          agents={agents}
          agent={agent}
          onChange={changeAgent}
          data={data}
          openCounts={openCounts}
        />
      </div>
    </header>
  );
}
