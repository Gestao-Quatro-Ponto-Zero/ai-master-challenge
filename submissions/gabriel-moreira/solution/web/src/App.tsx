import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, type DealsQuery, triggerBlobDownload } from "./api";
import { AgeRangeSlider } from "./components/AgeRangeSlider";
import { DealDetailPanel } from "./components/DealDetailPanel";
import { DealTable } from "./components/DealTable";
import { EstadoChips } from "./components/EstadoChips";
import { FilterBar } from "./components/FilterBar";
import { KpiTiles } from "./components/KpiTiles";
import { ManagementView } from "./components/ManagementView";
import { PaginationControls } from "./components/PaginationControls";
import { SobrecargaView } from "./components/SobrecargaView";
import { ViewTabs, type Aba } from "./components/ViewTabs";
import { useAsync } from "./hooks/useAsync";
import { useUrlState } from "./hooks/useUrlState";
import type { DealsEnvelope, Estado, Filtros, Rollup, SortKey, SortOrder } from "./types";
import { ESTADOS_TRABALHAVEIS } from "./types";

const PAGE_SIZE = 100;

const URL_DEFAULTS = {
  aba: "oportunidades",
  estados: undefined as string | undefined,
  revisao_lote: undefined as string | undefined,
  sales_agent: undefined as string | undefined,
  manager: undefined as string | undefined,
  regional_office: undefined as string | undefined,
  product: undefined as string | undefined,
  confianca_min: undefined as string | undefined,
  confianca_max: undefined as string | undefined,
  idade_min: undefined as string | undefined,
  idade_max: undefined as string | undefined,
  sobrecarga: undefined as string | undefined,
  page: "1",
  sort: "score",
  order: "desc",
  deal: undefined as string | undefined,
};

function parseEstados(raw: string | undefined): Estado[] {
  if (!raw) return [];
  return raw.split(",").filter((e): e is Estado => (ESTADOS_TRABALHAVEIS as string[]).includes(e));
}

function describeFiltros(filtros: Filtros, estados: Estado[], emRevisaoLote: boolean): string {
  const partes: string[] = [];
  if (emRevisaoLote) partes.push("Revisão em lote");
  else if (estados.length > 0) partes.push(`Estado: ${estados.join(", ")}`);
  if (filtros.sales_agent) partes.push(`Vendedor: ${filtros.sales_agent}`);
  if (filtros.manager) partes.push(`Gerente: ${filtros.manager}`);
  if (filtros.regional_office) partes.push(`Escritório: ${filtros.regional_office}`);
  if (filtros.product) partes.push(`Produto: ${filtros.product}`);
  if (filtros.confianca_min || filtros.confianca_max) {
    partes.push(`Confiança: ${filtros.confianca_min ?? "0"}–${filtros.confianca_max ?? "100"}`);
  }
  if (filtros.idade_min || filtros.idade_max) {
    partes.push(`Idade: ${filtros.idade_min ?? "0"}–${filtros.idade_max ?? "∞"}d`);
  }
  if (filtros.sobrecarga === "1") partes.push("Só sobrecarregadas");
  return partes.length > 0 ? partes.join(" · ") : "Fila trabalhável";
}

export default function App() {
  const [urlState, updateUrlState] = useUrlState(URL_DEFAULTS);

  const aba = (urlState.aba as Aba) ?? "oportunidades";
  const estados = useMemo(() => parseEstados(urlState.estados), [urlState.estados]);
  const emRevisaoLote = urlState.revisao_lote === "1";
  const page = Number(urlState.page) || 1;
  const sort = (urlState.sort as SortKey) || "score";
  const order = (urlState.order as SortOrder) || "desc";

  const filtros: Filtros = {
    sales_agent: urlState.sales_agent,
    manager: urlState.manager,
    regional_office: urlState.regional_office,
    product: urlState.product,
    confianca_min: urlState.confianca_min,
    confianca_max: urlState.confianca_max,
    idade_min: urlState.idade_min,
    idade_max: urlState.idade_max,
    sobrecarga: urlState.sobrecarga,
  };

  const { data: filterOptions } = useAsync(() => api.getFilterOptions(), []);

  // `revisao_lote` nunca compõe com os três estados trabalháveis — é uma
  // visão própria (Requirement "Revisão em lote fora da fila ordenada").
  // Sem seleção explícita, a fila padrão é sempre os três trabalháveis,
  // nunca "todos os quatro" (o que reintroduziria revisao_lote por omissão).
  const estadoFiltro = emRevisaoLote
    ? (["revisao_lote"] as Estado[])
    : estados.length > 0
      ? estados
      : ESTADOS_TRABALHAVEIS;

  const dealsQuery: DealsQuery = useMemo(
    () => ({
      estado: estadoFiltro,
      sales_agent: filtros.sales_agent,
      manager: filtros.manager,
      regional_office: filtros.regional_office,
      product: filtros.product,
      confianca_min: filtros.confianca_min,
      confianca_max: filtros.confianca_max,
      idade_min: filtros.idade_min,
      idade_max: filtros.idade_max,
      sobrecarga: filtros.sobrecarga,
      page,
      page_size: PAGE_SIZE,
      sort,
      order,
    }),
    [estadoFiltro, filtros.sales_agent, filtros.manager, filtros.regional_office, filtros.product, filtros.confianca_min, filtros.confianca_max, filtros.idade_min, filtros.idade_max, filtros.sobrecarga, page, sort, order]
  );

  // Indicadores refletem só os filtros de organização/produto/confiança/
  // idade — nunca a visão de revisão em lote, que é uma navegação, não um
  // recorte que o usuário escolheu para os tiles.
  const kpisQuery: DealsQuery = useMemo(
    () => ({
      estado: estados.length > 0 ? estados : undefined,
      sales_agent: filtros.sales_agent,
      manager: filtros.manager,
      regional_office: filtros.regional_office,
      product: filtros.product,
      confianca_min: filtros.confianca_min,
      confianca_max: filtros.confianca_max,
      idade_min: filtros.idade_min,
      idade_max: filtros.idade_max,
    }),
    [estados, filtros.sales_agent, filtros.manager, filtros.regional_office, filtros.product, filtros.confianca_min, filtros.confianca_max, filtros.idade_min, filtros.idade_max]
  );

  const [envelope, setEnvelope] = useState<DealsEnvelope | null>(null);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [dealsError, setDealsError] = useState<string | null>(null);
  const dealsControllerRef = useRef<AbortController | null>(null);
  const dealsQueryKey = JSON.stringify(dealsQuery);

  useEffect(() => {
    if (aba !== "oportunidades") return;
    dealsControllerRef.current?.abort();
    const controller = new AbortController();
    dealsControllerRef.current = controller;
    setDealsLoading(true);
    api
      .getDeals(dealsQuery, controller.signal)
      .then((data) => {
        setEnvelope(data);
        setDealsError(null);
        setDealsLoading(false);
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setDealsError(err instanceof ApiError ? err.message : "erro desconhecido");
        setDealsLoading(false);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dealsQueryKey, aba]);

  const [sobrecarregadasCount, setSobrecarregadasCount] = useState<number | undefined>(undefined);
  useEffect(() => {
    let cancelado = false;
    api
      .getSobrecarregados({ page_size: 1 })
      .then((data) => {
        if (!cancelado) setSobrecarregadasCount(data.total);
      })
      .catch(() => undefined);
    return () => {
      cancelado = true;
    };
  }, []);

  const [rollup, setRollup] = useState<Rollup | null>(null);
  useEffect(() => {
    if (aba !== "gestao") return;
    let cancelado = false;
    api
      .getRollup({
        sales_agent: filtros.sales_agent,
        manager: filtros.manager,
        regional_office: filtros.regional_office,
        product: filtros.product,
      })
      .then((data) => {
        if (!cancelado) setRollup(data);
      });
    return () => {
      cancelado = true;
    };
  }, [aba, filtros.sales_agent, filtros.manager, filtros.regional_office, filtros.product]);

  const onFilterChange = useCallback(
    (patch: Partial<Filtros>) => {
      updateUrlState({ ...(patch as Partial<typeof URL_DEFAULTS>), page: "1" });
    },
    [updateUrlState]
  );

  const onEstadoChange = useCallback(
    (next: Estado[]) => {
      updateUrlState({ estados: next.length > 0 ? next.join(",") : undefined, page: "1" });
    },
    [updateUrlState]
  );

  const abrirRevisaoLote = useCallback(() => {
    updateUrlState({ revisao_lote: "1", estados: undefined, page: "1" });
  }, [updateUrlState]);

  const fecharRevisaoLote = useCallback(() => {
    updateUrlState({ revisao_lote: undefined, page: "1" });
  }, [updateUrlState]);

  const onIdadeCommit = useCallback(
    (min: number, max: number) => {
      const bounds = filterOptions
        ? [filterOptions.idade_min, filterOptions.idade_max]
        : [null, null];
      const minIsDefault = bounds[0] !== null && min === bounds[0];
      const maxIsDefault = bounds[1] !== null && max === bounds[1];
      updateUrlState({
        idade_min: minIsDefault ? undefined : String(min),
        idade_max: maxIsDefault ? undefined : String(max),
        page: "1",
      });
    },
    [filterOptions, updateUrlState]
  );

  const onSortChange = useCallback(
    (key: SortKey) => {
      if (key === sort) {
        updateUrlState({ order: order === "desc" ? "asc" : "desc", page: "1" });
      } else {
        updateUrlState({ sort: key, order: "desc", page: "1" });
      }
    },
    [sort, order, updateUrlState]
  );

  const onClearAll = useCallback(() => {
    updateUrlState({
      estados: undefined,
      sales_agent: undefined,
      manager: undefined,
      regional_office: undefined,
      product: undefined,
      confianca_min: undefined,
      confianca_max: undefined,
      idade_min: undefined,
      idade_max: undefined,
      sobrecarga: undefined,
      page: "1",
    });
  }, [updateUrlState]);

  const activeCount =
    [
      filtros.sales_agent,
      filtros.manager,
      filtros.regional_office,
      filtros.product,
      filtros.confianca_min,
      filtros.confianca_max,
    ].filter(Boolean).length +
    (estados.length > 0 ? 1 : 0) +
    (filtros.idade_min || filtros.idade_max ? 1 : 0) +
    (filtros.sobrecarga === "1" ? 1 : 0);

  async function exportarIdsFiltrados() {
    const blob = await api.exportDealIds(dealsQuery);
    triggerBlobDownload(blob, "oportunidades_filtradas.csv");
  }

  // Painel: montado a partir de `openDeal`, não diretamente de
  // `urlState.deal`. Um identificador inexistente limpa o parâmetro da
  // URL imediatamente (para que recarregar/compartilhar não repita o
  // estado quebrado), mas o painel continua montado exibindo o erro até
  // o usuário fechar — se ele desmontasse junto com o parâmetro, a
  // mensagem nunca chegaria a ser vista (design.md, decisão 7).
  const [openDeal, setOpenDeal] = useState<string | undefined>(urlState.deal);
  useEffect(() => {
    if (urlState.deal) setOpenDeal(urlState.deal);
  }, [urlState.deal]);

  function openDetail(opportunityId: string) {
    updateUrlState({ deal: opportunityId });
  }

  function closeDetail() {
    updateUrlState({ deal: undefined });
    setOpenDeal(undefined);
  }

  function handleDetailNotFound() {
    updateUrlState({ deal: undefined });
  }

  async function navigateDetail(direction: "prev" | "next") {
    if (!envelope || !openDeal) return;
    const idx = envelope.items.findIndex((o) => o.opportunity_id === openDeal);
    if (idx === -1) return;

    if (direction === "prev") {
      if (idx > 0) {
        updateUrlState({ deal: envelope.items[idx - 1].opportunity_id });
        return;
      }
      if (page <= 1) return;
      const anterior = await api.getDeals({ ...dealsQuery, page: page - 1 });
      const ultimo = anterior.items[anterior.items.length - 1];
      if (ultimo) updateUrlState({ page: String(page - 1), deal: ultimo.opportunity_id });
    } else {
      if (idx < envelope.items.length - 1) {
        updateUrlState({ deal: envelope.items[idx + 1].opportunity_id });
        return;
      }
      if (page >= envelope.total_pages) return;
      const proxima = await api.getDeals({ ...dealsQuery, page: page + 1 });
      const primeiro = proxima.items[0];
      if (primeiro) updateUrlState({ page: String(page + 1), deal: primeiro.opportunity_id });
    }
  }

  const idxAtual = envelope && openDeal ? envelope.items.findIndex((o) => o.opportunity_id === openDeal) : -1;
  const prevDisabled = idxAtual <= 0 && page <= 1;
  const nextDisabled = !envelope || (idxAtual === envelope.items.length - 1 && page >= envelope.total_pages);

  const idadeBounds: [number, number] | null =
    filterOptions && filterOptions.idade_min !== null && filterOptions.idade_max !== null
      ? [filterOptions.idade_min, filterOptions.idade_max]
      : null;
  const idadeValue: [number, number] = idadeBounds
    ? [
        filtros.idade_min ? Number(filtros.idade_min) : idadeBounds[0],
        filtros.idade_max ? Number(filtros.idade_max) : idadeBounds[1],
      ]
    : [0, 0];

  return (
    <div className="min-h-screen bg-bg">
      <header className="bg-white border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <h1 className="text-lg font-bold text-navy">Lead Scorer | G4 For Sales</h1>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
        <KpiTiles query={kpisQuery} descricaoRecorte={describeFiltros(filtros, estados, emRevisaoLote)} />

        <ViewTabs
          aba={aba}
          onChange={(next) => updateUrlState({ aba: next })}
          sobrecarregadas={sobrecarregadasCount}
        />

        {aba === "gestao" ? (
          <>
            {filterOptions && (
              <FilterBar
                options={filterOptions}
                filtros={filtros}
                activeCount={activeCount}
                onChange={onFilterChange}
                onClearAll={onClearAll}
              />
            )}
            {rollup ? <ManagementView rollup={rollup} /> : <p className="text-muted">Carregando rollup…</p>}
          </>
        ) : aba === "sobrecarga" ? (
          <SobrecargaView onCarregado={setSobrecarregadasCount} />
        ) : (
          <>
            {filterOptions && (
              <FilterBar
                options={filterOptions}
                filtros={filtros}
                activeCount={activeCount}
                onChange={onFilterChange}
                onClearAll={onClearAll}
              />
            )}

            {idadeBounds && (
              <AgeRangeSlider
                bounds={idadeBounds}
                value={idadeValue}
                excluidasSemIdade={envelope?.excluidas_idade_desconhecida ?? 0}
                onCommit={onIdadeCommit}
              />
            )}

            {emRevisaoLote ? (
              <div className="flex items-center justify-between bg-alert/5 border border-alert rounded-sm px-3 py-2">
                <p className="text-sm text-alert">
                  Revisão em lote — passivo de higiene de dados (sem precedente histórico de
                  fechamento), não uma fila de trabalho individual.
                </p>
                <button
                  type="button"
                  onClick={fecharRevisaoLote}
                  className="text-xs font-semibold text-navy border border-border rounded-xs px-3 py-1.5 hover:border-gold whitespace-nowrap ml-3"
                >
                  ← Voltar à fila
                </button>
              </div>
            ) : (
              <>
                {envelope && (
                  <EstadoChips
                    estados={ESTADOS_TRABALHAVEIS}
                    selecionados={estados}
                    counts={envelope.contagem_por_estado}
                    onChange={onEstadoChange}
                  />
                )}

                {envelope && envelope.contagem_por_estado.revisao_lote > 0 && (
                  <button
                    type="button"
                    onClick={abrirRevisaoLote}
                    className="text-left text-xs text-muted hover:text-navy underline"
                  >
                    {envelope.contagem_por_estado.revisao_lote} oportunidade
                    {envelope.contagem_por_estado.revisao_lote === 1 ? "" : "s"} em revisão em lote
                  </button>
                )}
              </>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={exportarIdsFiltrados}
                className="text-xs font-semibold text-navy border border-border rounded-xs px-3 py-1.5 hover:border-gold"
              >
                Exportar {envelope?.total ?? 0} oportunidade{envelope?.total === 1 ? "" : "s"} filtrada
                {envelope?.total === 1 ? "" : "s"} (CSV)
              </button>
            </div>

            {dealsError && (
              <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
                Não foi possível carregar o pipeline: {dealsError}
              </p>
            )}

            {dealsLoading && !envelope ? (
              <p className="text-muted">Carregando oportunidades…</p>
            ) : (
              envelope && (
                <>
                  <DealTable
                    oportunidades={envelope.items}
                    sort={sort}
                    order={order}
                    total={envelope.total}
                    page={envelope.page}
                    totalPages={envelope.total_pages}
                    onSortChange={onSortChange}
                    onOpenDetail={openDetail}
                    onNavigateToSobrecarga={() => updateUrlState({ aba: "sobrecarga" })}
                  />
                  <PaginationControls
                    page={envelope.page}
                    totalPages={envelope.total_pages}
                    onChange={(next) => updateUrlState({ page: String(next) })}
                  />
                </>
              )
            )}
          </>
        )}
      </main>

      {openDeal && (
        <DealDetailPanel
          opportunityId={openDeal}
          onClose={closeDetail}
          onNotFound={handleDetailNotFound}
          onPrev={() => navigateDetail("prev")}
          onNext={() => navigateDetail("next")}
          prevDisabled={prevDisabled}
          nextDisabled={nextDisabled}
        />
      )}
    </div>
  );
}
