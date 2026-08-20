import { useEffect, useRef, useState } from "react";
import { api, ApiError, type DealsQuery } from "../api";
import { formatData, formatIdade, formatUsd } from "../format";
import type { Kpis } from "../types";
import { Tooltip } from "./Tooltip";

const DEBOUNCE_MS = 250;

/** Indicadores do recorte corrente, buscados em `/kpis` com *debounce* de
 * 250ms e cancelamento da requisição anterior a cada mudança de filtro
 * (Requirement "Tiles de indicadores", design.md decisão 2). Os dois
 * tiles históricos são rotulados a partir da marcação vinda da API. */
export function KpiTiles({
  query,
  descricaoRecorte,
}: {
  query: DealsQuery;
  descricaoRecorte: string;
}) {
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const queryKey = JSON.stringify(query);

  useEffect(() => {
    const timer = setTimeout(() => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      api
        .getKpis(query, controller.signal)
        .then((data) => {
          setKpis(data);
          setErro(null);
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === "AbortError") return;
          setErro(err instanceof ApiError ? err.message : "falha ao carregar indicadores");
        });
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      controllerRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryKey]);

  if (erro) {
    return (
      <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
        Não foi possível carregar os indicadores: {erro}
      </p>
    );
  }

  if (!kpis) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 animate-pulse">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-sm border border-border bg-white h-20" />
        ))}
      </div>
    );
  }

  const historicos = new Set(kpis.indicadores_historicos);
  const tiles: { key: string; label: string; value: string; alert?: boolean }[] = [
    { key: "total_oportunidades", label: "Oportunidades", value: kpis.total_oportunidades.toLocaleString("pt-BR") },
    { key: "receita_ganha", label: "Receita ganha", value: formatUsd(kpis.receita_ganha) },
    { key: "valor_esperado_aberto", label: "Valor esperado em aberto", value: formatUsd(kpis.valor_esperado_aberto) },
    { key: "total_desistir", label: "Em Desistir", value: kpis.total_desistir.toLocaleString("pt-BR"), alert: true },
    { key: "maior_negocio_fechado", label: "Maior negócio fechado", value: formatUsd(kpis.maior_negocio_fechado) },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {tiles.map((tile) => (
          <div
            key={tile.key}
            className={
              "rounded-sm border p-4 " +
              (tile.alert ? "border-alert bg-alert/5 text-alert" : "border-border bg-white text-navy")
            }
          >
            <div className="text-xs uppercase tracking-wide text-muted mb-1 flex items-center gap-1">
              {tile.label}
              {historicos.has(tile.key) && (
                <Tooltip content="Indicador histórico: reflete apenas os filtros de organização e produto — não segue estado, confiança ou idade, que só existem para o funil aberto.">
                  <button
                    type="button"
                    aria-label="Por que este número não segue o filtro de estado"
                    className="inline-flex items-center justify-center text-[9px] font-bold border border-current rounded-full w-3.5 h-3.5 leading-none bg-transparent p-0 cursor-help"
                  >
                    i
                  </button>
                </Tooltip>
              )}
            </div>
            <div className="text-xl font-bold">{tile.value}</div>
          </div>
        ))}
      </div>
      <div className="text-xs text-muted mt-2">
        {formatData(kpis.data_inicio)} → {formatData(kpis.data_fim)}
        {kpis.idade_maxima_aberta !== null && (
          <> · {formatIdade(kpis.idade_maxima_aberta)} no negócio aberto mais antigo do recorte</>
        )}
        {" · "}
        {descricaoRecorte}
      </div>
    </div>
  );
}
