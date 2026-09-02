"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  ChevronRight,
  CircleDollarSign,
  Crosshair,
  MapPin,
  Search,
  ShieldCheck,
  UserRound,
  UsersRound,
} from "lucide-react";
import { scoreOf, weightedValue } from "@/lib/analytics";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import { QUEUES, type Opportunity, type Queue } from "@/lib/types";
import type { DataStatus } from "@/lib/types";
import { DataSourcePill } from "@/components/data-source-pill";
import { PageHeader } from "@/components/page-header";
import { QueueBadge } from "@/components/queue-badge";
import { ScoreRing } from "@/components/score-ring";

interface AgentSummary {
  name: string;
  manager: string;
  region: string;
  opportunities: Opportunity[];
  focus: number;
  total: number;
  estimatedValue: number;
  weightedValue: number;
  averageScore: number | null;
}

export function PortfolioView({ opportunities, status }: { opportunities: Opportunity[]; status: DataStatus }) {
  const summaries = useMemo(() => buildAgentSummaries(opportunities), [opportunities]);
  const managers = useMemo(() => [...new Set(summaries.map((item) => item.manager))].sort(), [summaries]);
  const regions = useMemo(() => [...new Set(summaries.map((item) => item.region))].sort(), [summaries]);
  const [manager, setManager] = useState("");
  const [region, setRegion] = useState("");
  const [search, setSearch] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("");

  const visibleAgents = useMemo(() => summaries.filter((item) => {
    if (manager && item.manager !== manager) return false;
    if (region && item.region !== region) return false;
    if (search && !item.name.toLocaleLowerCase("pt-BR").includes(search.toLocaleLowerCase("pt-BR"))) return false;
    return true;
  }), [summaries, manager, region, search]);

  const selected =
    summaries.find((item) => item.name === selectedAgent) ?? visibleAgents[0] ?? summaries[0] ?? null;
  const totalFocus = visibleAgents.reduce((sum, item) => sum + item.focus, 0);
  const totalValue = visibleAgents.reduce((sum, item) => sum + item.estimatedValue, 0);
  const totalWeighted = visibleAgents.reduce((sum, item) => sum + item.weightedValue, 0);

  return (
    <div className="page portfolio-page">
      <PageHeader
        eyebrow="Gestão de carteira"
        title="Do time inteiro ao plano de cada vendedor"
        description="Compare carga, potencial e foco. Depois, transforme o ranking em uma agenda comercial objetiva."
        icon={BriefcaseBusiness}
        action={<DataSourcePill status={status} />}
      />

      <section className="portfolio-filters" aria-label="Filtros da carteira">
        <label className="search-field small">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Buscar vendedor</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar vendedor" />
        </label>
        <label className="select-field">
          <span className="sr-only">Filtrar por manager</span>
          <select value={manager} onChange={(event) => { setManager(event.target.value); setSelectedAgent(""); }}>
            <option value="">Todos os managers</option>
            {managers.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="select-field compact-select">
          <span className="sr-only">Filtrar por regional</span>
          <select value={region} onChange={(event) => { setRegion(event.target.value); setSelectedAgent(""); }}>
            <option value="">Todas as regionais</option>
            {regions.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <span className="filter-result">{formatNumber(visibleAgents.length)} vendedores</span>
      </section>

      <section className="portfolio-kpis" aria-label="Resumo do time">
        <div><span className="kpi-icon lime"><Crosshair size={18} /></span><p><small>Foco agora</small><strong>{formatNumber(totalFocus)} deals</strong></p></div>
        <div><span className="kpi-icon green"><CircleDollarSign size={18} /></span><p><small>Valor estimado</small><strong>{formatCurrency(totalValue)}</strong></p></div>
        <div><span className="kpi-icon blue"><ShieldCheck size={18} /></span><p><small>Pipeline ponderado</small><strong>{formatCurrency(totalWeighted)}</strong></p></div>
        <div><span className="kpi-icon neutral"><UsersRound size={18} /></span><p><small>Carteira média</small><strong>{visibleAgents.length ? formatNumber(Math.round(visibleAgents.reduce((sum, item) => sum + item.total, 0) / visibleAgents.length)) : "0"} deals</strong></p></div>
      </section>

      <section className="portfolio-workspace">
        <article className="panel agent-ranking-panel">
          <div className="panel-heading">
            <div><p className="section-kicker">Capacidade e foco</p><h2>Carteiras do time</h2></div>
            <span className="ranking-caption">por foco e potencial</span>
          </div>
          <div className="agent-ranking-head" aria-hidden="true">
            <span>Vendedor</span><span>Carteira</span><span>Foco</span><span>Potencial</span><span />
          </div>
          <div className="agent-ranking-list">
            {visibleAgents.map((agent) => (
              <button
                key={agent.name}
                className={`agent-ranking-row${selected?.name === agent.name ? " selected" : ""}`}
                onClick={() => setSelectedAgent(agent.name)}
              >
                <span className="agent-identity"><span className="avatar">{initials(agent.name)}</span><span><strong>{agent.name}</strong><small>{agent.region} · {agent.manager}</small></span></span>
                <span><strong>{formatNumber(agent.total)}</strong><small>deals</small></span>
                <span><strong>{formatNumber(agent.focus)}</strong><small>agora</small></span>
                <span><strong>{formatCurrency(agent.weightedValue)}</strong><small>ponderado</small></span>
                <ChevronRight size={17} aria-hidden="true" />
              </button>
            ))}
            {visibleAgents.length === 0 ? <div className="empty-state compact">Nenhum vendedor neste recorte.</div> : null}
          </div>
        </article>

        <aside className="agent-plan-panel">
          {selected ? <AgentPlan agent={selected} /> : null}
        </aside>
      </section>
    </div>
  );
}

function AgentPlan({ agent }: { agent: AgentSummary }) {
  const byQueue = new Map<Queue, Opportunity[]>(QUEUES.map((queue) => [queue, []]));
  for (const item of [...agent.opportunities].sort((a, b) => (scoreOf(b) ?? -1) - (scoreOf(a) ?? -1))) {
    byQueue.get(item.queue)?.push(item);
  }

  return (
    <div className="agent-plan-content">
      <div className="agent-plan-head">
        <span className="avatar large">{initials(agent.name)}</span>
        <div><span>Plano de foco</span><h2>{agent.name}</h2><p><MapPin size={13} /> {agent.region} · manager {agent.manager}</p></div>
      </div>
      <div className="agent-plan-stats">
        <span><small>Carteira</small><strong>{formatNumber(agent.total)}</strong></span>
        <span><small>Foco agora</small><strong>{formatNumber(agent.focus)}</strong></span>
        <span><small>Score médio</small><strong>{agent.averageScore === null ? "—" : Math.round(agent.averageScore)}</strong></span>
      </div>
      <p className="plan-instruction"><UserRound size={15} /> Sequência sugerida para a próxima sessão comercial.</p>
      <div className="agent-queue-groups">
        {QUEUES.map((queue) => {
          const queueItems = byQueue.get(queue) ?? [];
          if (!queueItems.length) return null;
          return (
            <section key={queue} className="agent-queue-group">
              <div><QueueBadge queue={queue} compact /><span>{queueItems.length}</span></div>
              {queueItems.slice(0, queue === "Foco agora" ? 4 : 2).map((item) => (
                <a href={`/pipeline?selected=${encodeURIComponent(item.opportunityId)}`} key={item.opportunityId} className="agent-deal-row">
                  <ScoreRing opportunity={item} size="sm" />
                  <span><strong>{item.account ?? "Conta a qualificar"}</strong><small>{item.nextAction}</small></span>
                  <span className="agent-deal-value"><strong>{formatCurrency(item.estimatedValue)}</strong><small>{formatPercent(item.probability)}</small></span>
                  <ArrowRight size={14} />
                </a>
              ))}
            </section>
          );
        })}
      </div>
    </div>
  );
}

function buildAgentSummaries(opportunities: Opportunity[]): AgentSummary[] {
  const grouped = new Map<string, Opportunity[]>();
  for (const opportunity of opportunities) {
    grouped.set(opportunity.salesAgent, [...(grouped.get(opportunity.salesAgent) ?? []), opportunity]);
  }

  return [...grouped.entries()].map(([name, items]) => {
    const scored = items.map(scoreOf).filter((score): score is number => score !== null);
    return {
      name,
      manager: items[0]?.manager ?? "—",
      region: items[0]?.regionalOffice ?? "—",
      opportunities: items,
      focus: items.filter((item) => item.queue === "Foco agora").length,
      total: items.length,
      estimatedValue: items.reduce((sum, item) => sum + item.estimatedValue, 0),
      weightedValue: items.reduce((sum, item) => sum + weightedValue(item), 0),
      averageScore: scored.length ? scored.reduce((sum, score) => sum + score, 0) / scored.length : null,
    };
  }).sort((a, b) => b.focus - a.focus || b.weightedValue - a.weightedValue);
}

function initials(name: string): string {
  return name.split(" ").slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}
