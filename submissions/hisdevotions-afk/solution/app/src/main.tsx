import { Component, StrictMode, Suspense, use, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { AppContext, NO_FILTERS, filtersFromUrl, loadModel, sameFilters, store, useApp, useScopedOpen, writeFiltersToUrl, type Decisions, type DecisionKind, type Filters } from "./data";
import type { Agent } from "./types";
import { link, useRoute } from "./router";
import { int, longDate, money, pct } from "./format";
import { BUCKETS, DealName, Score } from "./components";
import { MyDay } from "./pages/MyDay";
import { Pipeline } from "./pages/Pipeline";
import { DealPage } from "./pages/DealPage";
import { Forecast } from "./pages/Forecast";
import { Validation } from "./pages/Validation";
import { AccountPage, Accounts } from "./pages/Accounts";
import { Team } from "./pages/Team";
import logoMark from "./assets/logo-mark.png";
import "./styles.css";

const NAV: [string, string][] = [
  ["", "Overview"],
  ["pipeline", "Pipeline"],
  ["forecast", "Forecast"],
  ["validacao", "Validação"],
  ["contas", "Contas"],
  ["time", "Time"],
];

/** Um traço, um peso: mesmo sistema de ícone das razões do score, agora para a navegação. */
function NavIcon({ slug }: { slug: string }) {
  const s = { fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (slug === "") return <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="3.2" {...s} /><line x1="9" y1="1.6" x2="9" y2="3.8" {...s} /><line x1="9" y1="14.2" x2="9" y2="16.4" {...s} /><line x1="1.6" y1="9" x2="3.8" y2="9" {...s} /><line x1="14.2" y1="9" x2="16.4" y2="9" {...s} /></svg>;
  if (slug === "pipeline") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2.5 3.5h13L10.2 9.8v5.2l-2.4 1v-6.2Z" {...s} /></svg>;
  if (slug === "forecast") return <svg viewBox="0 0 18 18" aria-hidden="true"><polyline points="2.5,14.5 6.8,9 10.5,11.2 15.5,4" {...s} /></svg>;
  if (slug === "validacao") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M9 1.8 15.5 5v4.4c0 3.4-2.6 5.9-6.5 6.8-3.9-.9-6.5-3.4-6.5-6.8V5Z" {...s} /><polyline points="5.8,9.1 8,11.3 12.2,6.8" {...s} /></svg>;
  if (slug === "contas") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2 7 L9 2 L16 7" {...s} /><rect x="3.5" y="7" width="11" height="8.5" {...s} /></svg>;
  if (slug === "time") return <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="6.5" cy="7" r="2.4" {...s} /><circle cx="12.2" cy="7.6" r="2" {...s} /><path d="M1.8 16 a4.7 4.7 0 0 1 9.4 0" {...s} /><path d="M8.6 16 a4.3 4 0 0 1 7.6 -1.4" {...s} /></svg>;
  return <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="7" {...s} /><line x1="9" y1="8.3" x2="9" y2="13" {...s} /><circle cx="9" cy="5.3" r="0.9" fill="currentColor" stroke="none" /></svg>;
}

/** CSV do recorte atual (região/manager/vendedor). */
function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function csvEscape(v: string): string {
  return /[;"\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}

function exportPipelineCsv(deals: import("./types").OpenDeal[]) {
  const header = ["Conta", "Produto", "Vendedor", "Fila", "Score: chance de ganhar em 30 dias (%)", "Faixa", "Idade (dias)", "Chance de ganhar, sem prazo", "Receita esperada 30 dias", "Valor de lista"];
  const rows = deals.map((d) => [
    d.account ?? "Sem conta vinculada",
    d.product,
    d.agent,
    BUCKETS[d.bucket].label,
    d.score == null ? "sem score" : String(d.score),
    d.tier ?? "",
    d.age == null ? "não iniciado" : String(d.age),
    d.win_prob == null ? "sem histórico" : pct(d.win_prob),
    money(d.ev_soon),
    money(d.price),
  ]);
  const csv = [header, ...rows].map((r) => r.map(csvEscape).join(";")).join("\r\n");
  downloadBlob("﻿" + csv, `pipeline-g4-${new Date().toISOString().slice(0, 10)}.csv`, "text/csv;charset=utf-8;");
}

function Loaded() {
  const model = use(loadModel());
  // Um link com filtros vence o que estava guardado neste navegador.
  const [filters, setFiltersState] = useState<Filters>(() => filtersFromUrl() ?? store.read("filters", NO_FILTERS));
  const [decisions, setDecisions] = useState<Decisions>(() => store.read("decisions", {}));
  const current = useRef(filters);
  const setFilters = (f: Filters) => {
    current.current = f;
    setFiltersState(f);
    store.write("filters", f);
    writeFiltersToUrl(f);
  };
  useEffect(() => {
    // A cada troca de rota: se a URL traz filtros (link colado, botão voltar),
    // eles valem; se não traz (link interno), a URL ganha os filtros atuais.
    const sync = () => {
      const fromUrl = filtersFromUrl();
      if (fromUrl && !sameFilters(fromUrl, current.current)) {
        current.current = fromUrl;
        setFiltersState(fromUrl);
        store.write("filters", fromUrl);
      } else if (!fromUrl) writeFiltersToUrl(current.current);
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);
  const decide = (id: string, kind: DecisionKind | null, note?: string) =>
    setDecisions((prev) => {
      const next = { ...prev };
      if (kind) {
        const existing = prev[id];
        // mesma decisão de novo (ex: só editando a nota) preserva o "at" original
        next[id] = { kind, at: existing?.kind === kind ? existing.at : new Date().toISOString(), note: note ?? existing?.note };
      } else {
        delete next[id];
      }
      store.write("decisions", next);
      return next;
    });
  const importDecisions = (data: Decisions) =>
    setDecisions((prev) => {
      const next = { ...prev, ...data };
      store.write("decisions", next);
      return next;
    });
  return (
    <AppContext value={{ model, filters, setFilters, decisions, decide, importDecisions }}>
      <Shell />
    </AppContext>
  );
}

function BrandMark() {
  return <img className="brand-mark" src={logoMark} alt="" width={32} height={32} />;
}

/** Iniciais para o indicador de escopo (vendedor, manager ou região — todos vêm do dataset). */
function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts.at(-1)![0]).toUpperCase();
}

/** Decisão só vive no localStorage deste navegador (ver Limitações no README) —
    baixar/importar é o jeito de levar isso pra outro navegador ou fazer backup
    antes de limpar o cache, sem precisar de servidor nenhum. */
function DecisionsBackup() {
  const { decisions, importDecisions } = useApp();
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const count = Object.keys(decisions).length;

  const exportJson = () => {
    downloadBlob(JSON.stringify(decisions, null, 2), `decisoes-pipeline-em-foco-${new Date().toISOString().slice(0, 10)}.json`, "application/json");
  };

  const importJson = async (file: File) => {
    setError(null);
    try {
      const data = JSON.parse(await file.text());
      const valid = data && typeof data === "object" &&
        Object.values(data).every((v: any) => v && (v.kind === "requalificado" || v.kind === "encerrado"));
      if (!valid) throw new Error("formato inesperado");
      importDecisions(data);
    } catch {
      setError("Não consegui ler esse arquivo. Exporte um novo daqui e tente de novo.");
    }
  };

  return (
    <div className="nav-backup">
      <button type="button" className="btn-link" onClick={exportJson} disabled={count === 0}>
        Baixar decisões ({int(count)})
      </button>
      <button type="button" className="btn-link" onClick={() => fileRef.current?.click()}>Importar decisões</button>
      <input
        ref={fileRef} type="file" accept="application/json" className="sr-only" tabIndex={-1}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) importJson(f); e.target.value = ""; }}
      />
      {error && <p className="nav-backup-error">{error}</p>}
    </div>
  );
}

function Topbar() {
  const { model, setFilters } = useApp();
  const scoped = useScopedOpen();
  const decidir = scoped.filter((d) => d.bucket === "decidir").length;
  const decidirLabel = int(decidir);
  const [q, setQ] = useState("");
  const [resultsOpen, setResultsOpen] = useState(false);

  const goToAll = (text: string) => {
    // busca global vence o recorte: some deal fora do filtro ativo que ela
    // prometeu mostrar não pode virar "nada encontrado" só porque a página
    // seguinte (Pipeline) ainda respeita região/manager/vendedor.
    setFilters(NO_FILTERS);
    window.location.hash = `${link("pipeline")}?busca=${encodeURIComponent(text)}`;
    setResultsOpen(false);
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (q.trim()) goToAll(q.trim());
  };

  const needle = q.trim().toLowerCase();
  // model.open, não scoped: a busca do topo é global de propósito (por isso o
  // ícone e a posição de destaque) — filtrar pelo recorte ativo faria um deal
  // de outro vendedor "sumir" da busca sem aviso nenhum.
  const matches =
    needle.length < 2 ? [] : model.open.filter((d) => [d.account, d.product, d.agent, d.id].some((v) => v?.toLowerCase().includes(needle)));
  const showResults = resultsOpen && needle.length >= 2;
  const resultsStatus = matches.length === 0
    ? `Nada encontrado para ${q.trim()}`
    : `${matches.length} ${matches.length === 1 ? "resultado encontrado" : "resultados encontrados"}`;

  return (
    <header className="topbar">
      <a className="brand" href="#/">
        <BrandMark />
        <span className="brand-word">G4</span>
      </a>
      <span className="topbar-product">Pipeline em Foco</span>
      <form className="topbar-search" onSubmit={submit} role="search" autoComplete="off">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.8" /><line x1="15.3" y1="15.3" x2="21" y2="21" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
        <input
          type="search" placeholder="Buscar conta, produto ou vendedor" aria-label="Busca global"
          value={q}
          onChange={(e) => { setQ(e.target.value); setResultsOpen(true); }}
          onFocus={() => q.trim() && setResultsOpen(true)}
          onBlur={() => setTimeout(() => setResultsOpen(false), 120)}
          onKeyDown={(e) => e.key === "Escape" && setResultsOpen(false)}
          role="combobox" aria-expanded={showResults} aria-controls="topbar-search-results" aria-autocomplete="list"
        />
        {showResults && (
          <div className="topbar-search-results" id="topbar-search-results" role="listbox">
            <span role="status" aria-live="polite" className="sr-only">{resultsStatus}</span>
            {matches.length === 0 ? (
              <p className="topbar-search-empty">Nada encontrado para "{q.trim()}".</p>
            ) : (
              <>
                <ul>
                  {matches.slice(0, 6).map((d) => (
                    <li key={d.id}>
                      <a href={link("deal", d.id)} role="option" onMouseDown={() => setResultsOpen(false)}>
                        <Score deal={d} />
                        <span className="topbar-search-result-name"><DealName deal={d} /></span>
                        <span className="topbar-search-result-agent">{d.agent}</span>
                      </a>
                    </li>
                  ))}
                </ul>
                {matches.length > 6 && (
                  <button type="button" className="topbar-search-all" onMouseDown={() => goToAll(q.trim())}>
                    Ver todos os {int(matches.length)} resultados
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </form>
      <div className="topbar-actions">
        <a className="topbar-queue-chip" href={`${link("pipeline")}?fila=decidir`} title="Deals parados além do maior ciclo já fechado, para requalificar ou encerrar" aria-label={`${int(decidir)} deals parados para decidir`}>
          <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" strokeWidth="1.6" /><path d="M9 5.2V9l3 2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
          <span className="topbar-queue-chip-label" aria-hidden="true">{decidirLabel} parados para decidir</span>
        </a>
        <button className="topbar-export" onClick={() => exportPipelineCsv(scoped)} title="Exportar o recorte atual em CSV">
          <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M9 2.5v8.2M5.6 7.4 9 10.8l3.4-3.4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /><path d="M2.5 13v1.8a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V13" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
          <span>Exportar</span>
        </button>
      </div>
    </header>
  );
}

function Shell() {
  const { model, filters, setFilters } = useApp();
  const { parts, query } = useRoute();
  const [page = "", arg] = parts;
  const hasFilter = Boolean(filters.agent || filters.manager || filters.region);
  const scope = filters.agent || filters.manager || filters.region || "Toda a equipe";
  return (
    <div className="shell">
      <Topbar />
      <aside className="nav">
        <p className="nav-section">Workspace</p>
        <nav aria-label="Seções">
          {NAV.map(([slug, label]) => (
            <a key={slug} href={link(slug)} aria-current={page === slug || (slug === "pipeline" && page === "deal") ? "page" : undefined}>
              <NavIcon slug={slug} />
              {label}
            </a>
          ))}
        </nav>
        <div className="nav-foot">
          {hasFilter ? (
            <button
              type="button" className="nav-operator" onClick={() => setFilters(NO_FILTERS)}
              title={`${scope}: limpar filtro`} aria-label={`Escopo: ${scope}. Limpar filtro.`}
            >
              <span className="nav-operator-avatar">{initialsOf(scope)}</span>
              <span className="nav-operator-name">{scope}</span>
            </button>
          ) : (
            <div className="nav-operator" title={scope} aria-label={`Escopo: ${scope}`}>
              <span className="nav-operator-avatar">G4</span>
              <span className="nav-operator-name">{scope}</span>
            </div>
          )}
          <p className="nav-foot-date">Dados até {longDate(model.meta.reference_date)}</p>
          <DecisionsBackup />
        </div>
      </aside>
      <div className="main">
        <FilterBar />
        <main>
          {page === "" && <MyDay />}
          {page === "pipeline" && <Pipeline query={query} />}
          {page === "deal" && <DealPage id={arg} />}
          {page === "forecast" && <Forecast query={query} />}
          {page === "validacao" && <Validation />}
          {page === "contas" && (arg ? <AccountPage name={arg} /> : <Accounts />)}
          {page === "time" && <Team />}
          {!NAV.some(([slug]) => slug === page) && page !== "deal" && (
            <p className="empty">Essa página não existe. <a href="#/">Voltar para Overview</a></p>
          )}
        </main>
      </div>
    </div>
  );
}

/** Um select com rótulo, estado ativo visível e um "×" para limpar só esse campo. */
function FilterField({
  label, placeholder, value, onChange, onClear, children,
}: {
  label: string; placeholder: string; value: string;
  onChange: (value: string) => void; onClear: () => void; children: ReactNode;
}) {
  return (
    <label className={`filter-field${value ? " is-active" : ""}`}>
      {label}
      <span className="filter-control">
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">{placeholder}</option>
          {children}
        </select>
        {value && (
          <button type="button" className="filter-clear" onClick={onClear} title={`Limpar filtro de ${label.toLowerCase()}`}>
            ×<span className="sr-only">Limpar filtro de {label.toLowerCase()}</span>
          </button>
        )}
      </span>
    </label>
  );
}

/** Vendedores agrupados por manager (só quando o recorte ainda não escolheu um): 35 nomes soltos não se leem, 6 grupos sim. */
function agentOptions(agents: Agent[], groupByManager: boolean) {
  if (!groupByManager) return agents.map((a) => a.name).sort().map((n) => <option key={n}>{n}</option>);
  const byManager = new Map<string, string[]>();
  for (const a of agents) {
    const list = byManager.get(a.manager);
    if (list) list.push(a.name);
    else byManager.set(a.manager, [a.name]);
  }
  return [...byManager.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([manager, names]) => (
      <optgroup key={manager} label={manager}>
        {names.sort().map((n) => <option key={n}>{n}</option>)}
      </optgroup>
    ));
}

function FilterBar() {
  const { model, filters, setFilters } = useApp();
  const regions = [...new Set(model.agents.map((a) => a.region))].sort();
  const inRegion = model.agents.filter((a) => !filters.region || a.region === filters.region);
  const managers = [...new Set(inRegion.map((a) => a.manager))].sort();
  const inManager = inRegion.filter((a) => !filters.manager || a.manager === filters.manager);
  const activeCount = [filters.region, filters.manager, filters.agent].filter(Boolean).length;

  return (
    <div className="filters" role="search">
      <FilterField
        label="Região" placeholder="Todas" value={filters.region}
        onChange={(v) => setFilters({ region: v, manager: "", agent: "" })}
        onClear={() => setFilters({ region: "", manager: "", agent: "" })}
      >
        {regions.map((r) => <option key={r}>{r}</option>)}
      </FilterField>
      <FilterField
        label="Manager" placeholder="Todos" value={filters.manager}
        onChange={(v) => setFilters({ ...filters, manager: v, agent: "" })}
        onClear={() => setFilters({ ...filters, manager: "", agent: "" })}
      >
        {managers.map((m) => <option key={m}>{m}</option>)}
      </FilterField>
      <FilterField
        label="Vendedor" placeholder="Todos" value={filters.agent}
        onChange={(v) => setFilters({ ...filters, agent: v })}
        onClear={() => setFilters({ ...filters, agent: "" })}
      >
        {agentOptions(inManager, !filters.manager)}
      </FilterField>
      {activeCount > 0 && (
        <div className="filters-summary">
          <span className="filters-count">{activeCount} {activeCount === 1 ? "filtro ativo" : "filtros ativos"}</span>
          <button className="btn-link" onClick={() => setFilters(NO_FILTERS)}>Limpar tudo</button>
        </div>
      )}
    </div>
  );
}

class LoadError extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    return this.state.error ? <p className="empty boot">{this.state.error.message}</p> : this.props.children;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LoadError>
      <Suspense fallback={<p className="boot">Carregando o pipeline…</p>}>
        <Loaded />
      </Suspense>
    </LoadError>
  </StrictMode>,
);
