"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowUpDown,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Info,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
  Target,
  UserRound,
} from "lucide-react";
import { filterOpportunities, scoreOf } from "@/lib/analytics";
import { confidenceLabel, formatCurrency, formatFullCurrency, formatNumber, formatPercent } from "@/lib/format";
import { QUEUES, type Opportunity } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { QueueBadge } from "@/components/queue-badge";
import { ScoreRing } from "@/components/score-ring";
import { DataSourcePill } from "@/components/data-source-pill";
import type { DataStatus } from "@/lib/types";

const PAGE_SIZE = 25;

export function PipelineExplorer({
  opportunities,
  status,
  initialQueue = "",
  initialSelected = "",
}: {
  opportunities: Opportunity[];
  status: DataStatus;
  initialQueue?: string;
  initialSelected?: string;
}) {
  const [search, setSearch] = useState("");
  const [queue, setQueue] = useState(initialQueue);
  const [agent, setAgent] = useState("");
  const [region, setRegion] = useState("");
  const [sort, setSort] = useState<"score" | "value" | "age" | "probability">("score");
  const [selectedId, setSelectedId] = useState(initialSelected);
  const [page, setPage] = useState(1);

  const agents = useMemo(
    () => [...new Set(opportunities.map((item) => item.salesAgent))].sort((a, b) => a.localeCompare(b)),
    [opportunities],
  );
  const regions = useMemo(
    () => [...new Set(opportunities.map((item) => item.regionalOffice))].sort((a, b) => a.localeCompare(b)),
    [opportunities],
  );

  const filtered = useMemo(
    () => filterOpportunities(opportunities, { search, queue, salesAgent: agent, regionalOffice: region, sort }),
    [opportunities, search, queue, agent, region, sort],
  );
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const selected =
    opportunities.find((item) => item.opportunityId === selectedId) ?? visible[0] ?? null;
  const activeFilterCount = [search, queue, agent, region].filter(Boolean).length;

  function updateFilter(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  function clearFilters() {
    setSearch("");
    setQueue("");
    setAgent("");
    setRegion("");
    setSort("score");
    setPage(1);
  }

  return (
    <div className="page pipeline-page">
      <PageHeader
        eyebrow="Pipeline acionável"
        title="Uma fila clara para cada oportunidade"
        description="Filtre o contexto do time, compare prioridades e entenda o próximo passo recomendado."
        icon={SlidersHorizontal}
        action={<DataSourcePill status={status} />}
      />

      <section className="filter-bar" aria-label="Filtros do pipeline">
        <label className="search-field">
          <Search size={17} aria-hidden="true" />
          <span className="sr-only">Buscar oportunidade</span>
          <input
            value={search}
            onChange={(event) => updateFilter(setSearch, event.target.value)}
            placeholder="Buscar conta, ID, produto ou vendedor"
          />
        </label>
        <label className="select-field">
          <span className="sr-only">Filtrar por fila</span>
          <select value={queue} onChange={(event) => updateFilter(setQueue, event.target.value)}>
            <option value="">Todas as filas</option>
            {QUEUES.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="select-field">
          <span className="sr-only">Filtrar por vendedor</span>
          <select value={agent} onChange={(event) => updateFilter(setAgent, event.target.value)}>
            <option value="">Todos os vendedores</option>
            {agents.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="select-field compact-select">
          <span className="sr-only">Filtrar por regional</span>
          <select value={region} onChange={(event) => updateFilter(setRegion, event.target.value)}>
            <option value="">Regionais</option>
            {regions.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <button className="icon-button" onClick={clearFilters} title="Limpar filtros" disabled={activeFilterCount === 0}>
          <RotateCcw size={17} aria-hidden="true" />
          <span className="sr-only">Limpar filtros</span>
        </button>
      </section>

      <section className="pipeline-summary" aria-label="Resumo do recorte">
        <div><strong>{formatNumber(filtered.length)}</strong><span>oportunidades no recorte</span></div>
        <div><strong>{formatCurrency(filtered.reduce((sum, item) => sum + item.estimatedValue, 0))}</strong><span>valor estimado</span></div>
        <div><strong>{formatNumber(filtered.filter((item) => item.queue === "Foco agora").length)}</strong><span>em foco agora</span></div>
        <label className="sort-control">
          <ArrowUpDown size={15} aria-hidden="true" />
          <span>Ordenar por</span>
          <select value={sort} onChange={(event) => { setSort(event.target.value as typeof sort); setPage(1); }}>
            <option value="score">Maior score</option>
            <option value="value">Maior valor</option>
            <option value="probability">Maior probabilidade</option>
            <option value="age">Mais antigo</option>
          </select>
        </label>
      </section>

      <section className="pipeline-workspace">
        <div className="pipeline-list-panel">
          <div className="table-wrap">
            <table className="opportunity-table">
              <thead>
                <tr>
                  <th scope="col">Prioridade</th>
                  <th scope="col">Oportunidade</th>
                  <th scope="col">Fila</th>
                  <th scope="col">Vendedor</th>
                  <th scope="col">Valor</th>
                  <th scope="col">Chance</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((opportunity) => {
                  const isSelected = selected?.opportunityId === opportunity.opportunityId;
                  return (
                    <tr key={opportunity.opportunityId} className={isSelected ? "selected" : ""}>
                      <td>
                        <button
                          className="row-select score-select"
                          onClick={() => setSelectedId(opportunity.opportunityId)}
                          aria-label={`Ver detalhes de ${opportunity.account ?? opportunity.opportunityId}`}
                        >
                          <ScoreRing opportunity={opportunity} size="sm" />
                        </button>
                      </td>
                      <td>
                        <button className="row-select opportunity-cell" onClick={() => setSelectedId(opportunity.opportunityId)}>
                          <strong>{opportunity.account ?? "Conta a qualificar"}</strong>
                          <span>{opportunity.product} · {opportunity.opportunityId}</span>
                        </button>
                      </td>
                      <td><QueueBadge queue={opportunity.queue} compact /></td>
                      <td>
                        <span className="agent-cell"><strong>{opportunity.salesAgent}</strong><small>{opportunity.regionalOffice}</small></span>
                      </td>
                      <td><strong className="money-cell">{formatFullCurrency(opportunity.estimatedValue)}</strong></td>
                      <td><span className="probability-cell">{formatPercent(opportunity.probability)}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {visible.length === 0 ? (
              <div className="empty-state">
                <Search size={24} aria-hidden="true" />
                <strong>Nenhuma oportunidade encontrada</strong>
                <p>Ajuste os filtros para ampliar o recorte.</p>
                <button className="button secondary" onClick={clearFilters}>Limpar filtros</button>
              </div>
            ) : null}
          </div>

          {filtered.length > PAGE_SIZE ? (
            <div className="pagination" aria-label="Paginação">
              <span>{(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} de {formatNumber(filtered.length)}</span>
              <div>
                <button disabled={safePage === 1} onClick={() => setPage((value) => Math.max(1, value - 1))} aria-label="Página anterior"><ChevronLeft size={17} /></button>
                <span>Página {safePage} de {totalPages}</span>
                <button disabled={safePage === totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))} aria-label="Próxima página"><ChevronRight size={17} /></button>
              </div>
            </div>
          ) : null}
        </div>

        <aside className="opportunity-detail" aria-live="polite">
          {selected ? <OpportunityDetail opportunity={selected} /> : (
            <div className="empty-state compact"><Info size={20} />Selecione uma oportunidade para ver a explicação.</div>
          )}
        </aside>
      </section>
    </div>
  );
}

function OpportunityDetail({ opportunity }: { opportunity: Opportunity }) {
  const score = scoreOf(opportunity);
  const breakdown = Object.entries(
    opportunity.scoreBreakdown?.weightedContribution ?? {},
  ).filter((entry): entry is [string, number] => typeof entry[1] === "number");

  return (
    <div className="detail-content">
      <div className="detail-topline">
        <QueueBadge queue={opportunity.queue} />
        <span className={`confidence ${opportunity.confidence}`}>{confidenceLabel(opportunity.confidence)} confiança</span>
      </div>
      <div className="detail-score-head">
        <ScoreRing opportunity={opportunity} size="lg" />
        <div>
          <span className="detail-id">{opportunity.opportunityId}</span>
          <h2>{opportunity.account ?? "Conta a qualificar"}</h2>
          <p>{opportunity.product}</p>
        </div>
      </div>

      <div className="detail-facts">
        <span><CircleDollarSign size={16} /><small>Valor estimado</small><strong>{formatFullCurrency(opportunity.estimatedValue)}</strong></span>
        <span><Target size={16} /><small>Chance de ganho</small><strong>{formatPercent(opportunity.probability)}</strong></span>
        <span><CalendarDays size={16} /><small>Tempo aberto</small><strong>{opportunity.ageDays === null ? "Não iniciado" : `${opportunity.ageDays} dias`}</strong></span>
        <span><UserRound size={16} /><small>Responsável</small><strong>{opportunity.salesAgent}</strong></span>
      </div>

      <section className="next-action-card">
        <span><Sparkles size={16} aria-hidden="true" /> Próxima melhor ação</span>
        <p>{opportunity.nextAction}</p>
      </section>

      <section className="detail-section">
        <h3>Por que esta recomendação?</h3>
        <ul className="reason-list">
          {opportunity.reasons.map((reason) => (
            <li key={reason}><CheckCircle2 size={16} aria-hidden="true" />{reason}</li>
          ))}
        </ul>
      </section>

      {breakdown.length > 0 && score !== null ? (
        <section className="detail-section">
          <div className="detail-section-title"><h3>Composição do score</h3><span>{Math.round(score)}/100</span></div>
          <div className="breakdown-list">
            {breakdown.map(([key, value]) => {
              const max = key.toLowerCase().includes("conversion") ? 65 : key.toLowerCase().includes("action") ? 20 : 15;
              return (
                <div className="breakdown-row" key={key}>
                  <span><small>{breakdownLabel(key)}</small><strong>{Math.round(value)}/{max}</strong></span>
                  <span className="bar-track"><span className="bar-fill score" style={{ width: `${Math.min(100, (value / max) * 100)}%` }} /></span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="detail-section context-section">
        <h3>Contexto</h3>
        <dl>
          <div><dt>Manager</dt><dd>{opportunity.manager}</dd></div>
          <div><dt>Regional</dt><dd>{opportunity.regionalOffice}</dd></div>
          <div><dt>Etapa CRM</dt><dd>{opportunity.dealStage}</dd></div>
          <div><dt>Produto original</dt><dd>{opportunity.productRaw}</dd></div>
        </dl>
      </section>

      {opportunity.dataQualityFlags.length > 0 ? (
        <section className="quality-alert">
          <span><AlertTriangle size={16} aria-hidden="true" /> Atenção aos dados</span>
          <ul>{opportunity.dataQualityFlags.map((flag) => <li key={flag}>{flag}</li>)}</ul>
        </section>
      ) : (
        <p className="quality-ok"><CheckCircle2 size={15} aria-hidden="true" /> Sem alertas de qualidade neste deal.</p>
      )}
    </div>
  );
}

function breakdownLabel(key: string): string {
  const normalized = key.toLowerCase();
  if (normalized.includes("conversion")) return "Conversão";
  if (normalized.includes("action")) return "Momento de ação";
  if (normalized.includes("value")) return "Valor";
  return key.replaceAll("_", " ");
}
