import { useCallback, useEffect, useMemo } from "react";
import { api } from "./api";
import { DealTable } from "./components/DealTable";
import { FilterBar } from "./components/FilterBar";
import { IdentityPicker } from "./components/IdentityPicker";
import { KpiTiles } from "./components/KpiTiles";
import { ManagementView } from "./components/ManagementView";
import { StateTabs, type Aba } from "./components/StateTabs";
import { triggerBlobDownload } from "./api";
import { useAsync } from "./hooks/useAsync";
import { useSession } from "./hooks/useSession";
import { useUrlState } from "./hooks/useUrlState";
import type { Estado, Filtros, Session } from "./types";

const URL_DEFAULTS: Filtros & { aba: string } = {
  aba: "foco_urgente",
  sales_agent: undefined,
  manager: undefined,
  regional_office: undefined,
  product: undefined,
  confianca: undefined,
  idade_min: undefined,
  idade_max: undefined,
};

export default function App() {
  const { session, setSession, clearSession } = useSession();

  const trocarIdentidade = useCallback(() => {
    // Filtros e aba são específicos da identidade anterior — não fazem
    // sentido sobreviver à troca (Requirement "Seleção de identidade").
    window.history.replaceState({}, "", window.location.pathname);
    clearSession();
  }, [clearSession]);

  if (!session) {
    return <IdentityPicker onIdentified={setSession} />;
  }

  return <Painel session={session} onTrocarIdentidade={trocarIdentidade} />;
}

function Painel({
  session,
  onTrocarIdentidade,
}: {
  session: Session;
  onTrocarIdentidade: () => void;
}) {
  const token = session.token;
  const [urlState, updateUrlState] = useUrlState(URL_DEFAULTS);
  // "Gestão" não existe para Sales Agent — uma URL herdada de outra
  // identidade (ou de trás/frente do navegador) não pode deixar a aba
  // presa numa aba que não existe para o papel corrente.
  const aba: Aba =
    urlState.aba === "gestao" && session.role === "sales_agent"
      ? "foco_urgente"
      : (urlState.aba as Aba);

  const {
    data: todasOportunidades,
    loading: carregandoDeals,
    error: erroDeals,
    status: statusDeals,
  } = useAsync(() => api.getDeals(token, {}), [token]);
  const { data: kpis, status: statusKpis } = useAsync(() => api.getKpis(token), [token]);
  const { data: rollup, status: statusRollup } = useAsync(
    () => (session.role !== "sales_agent" ? api.getRollup(token) : Promise.resolve(null)),
    [token, session.role]
  );

  // Token inválido ou expirado em qualquer chamada -> volta ao seletor de
  // identidade (Requirement "Token expirado": 401 exige nova identificação).
  const sessaoInvalida = [statusDeals, statusKpis, statusRollup].includes(401);
  useEffect(() => {
    if (sessaoInvalida) onTrocarIdentidade();
  }, [sessaoInvalida, onTrocarIdentidade]);

  const filtros: Filtros = {
    sales_agent: urlState.sales_agent,
    manager: urlState.manager,
    regional_office: urlState.regional_office,
    product: urlState.product,
    confianca: urlState.confianca as Filtros["confianca"],
    idade_min: urlState.idade_min,
    idade_max: urlState.idade_max,
  };

  const filtradas = useMemo(() => {
    if (!todasOportunidades) return [];
    return todasOportunidades.filter((o) => {
      if (aba !== "gestao" && o.estado !== aba) return false;
      if (filtros.sales_agent && o.sales_agent !== filtros.sales_agent) return false;
      if (filtros.manager && o.manager !== filtros.manager) return false;
      if (filtros.regional_office && o.regional_office !== filtros.regional_office) return false;
      if (filtros.product && o.product !== filtros.product) return false;
      if (filtros.confianca && o.confianca !== filtros.confianca) return false;
      if (filtros.idade_min && (o.age_days ?? -Infinity) < Number(filtros.idade_min)) return false;
      if (filtros.idade_max && (o.age_days ?? Infinity) > Number(filtros.idade_max)) return false;
      return true;
    });
  }, [todasOportunidades, aba, filtros]);

  const contagensPorEstado = useMemo(() => {
    const counts: Record<Estado, number> = {
      foco_urgente: 0,
      acompanhar: 0,
      engajar: 0,
      qualificar: 0,
      desistir: 0,
    };
    for (const o of todasOportunidades ?? []) {
      counts[o.estado] += 1;
    }
    return counts;
  }, [todasOportunidades]);

  function exportarIdsFiltrados() {
    const linhas = ["opportunity_id", ...filtradas.map((o) => o.opportunity_id)];
    const blob = new Blob([linhas.join("\n")], { type: "text/csv;charset=utf-8" });
    triggerBlobDownload(blob, "desistir_filtrado.csv");
  }

  return (
    <div className="min-h-screen bg-bg">
      <header className="bg-white border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-lg font-bold text-navy">Pipeline Priorizado</h1>
          <button
            type="button"
            onClick={onTrocarIdentidade}
            className="text-xs text-muted hover:text-navy underline"
          >
            Trocar identidade
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
        {erroDeals && statusDeals !== 401 && (
          <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
            Não foi possível carregar o pipeline: {erroDeals}
          </p>
        )}

        {kpis && <KpiTiles kpis={kpis} session={session} />}

        <StateTabs
          aba={aba}
          role={session.role}
          counts={contagensPorEstado}
          onChange={(next) => updateUrlState({ aba: next })}
        />

        {aba === "gestao" ? (
          rollup ? (
            <ManagementView rollup={rollup} session={session} />
          ) : (
            <p className="text-muted">Carregando rollup…</p>
          )
        ) : (
          <>
            {todasOportunidades && (
              <FilterBar
                todasOportunidades={todasOportunidades}
                role={session.role}
                filtros={filtros}
                onChange={(patch) => updateUrlState(patch as Partial<typeof URL_DEFAULTS>)}
              />
            )}

            {aba === "desistir" && (
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={exportarIdsFiltrados}
                  className="text-xs font-semibold text-alert border border-alert rounded-xs px-3 py-1.5 hover:bg-alert/5"
                >
                  Exportar IDs filtrados (CSV)
                </button>
              </div>
            )}

            {carregandoDeals ? (
              <p className="text-muted">Carregando oportunidades…</p>
            ) : (
              <DealTable oportunidades={filtradas} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
