'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import type { Deal, Summary } from '@/lib/lead-scorer';

// ─── Score Badge ────────────────────────────────────────────────────────────

function ScoreBadge({ score, size = 'md' }: { score: number; size?: 'sm' | 'md' | 'lg' }) {
  const color =
    score >= 70
      ? { ring: '#22d3ee', glow: 'rgba(34,211,238,0.4)', text: '#22d3ee' }
      : score >= 40
        ? { ring: '#f59e0b', glow: 'rgba(245,158,11,0.4)', text: '#f59e0b' }
        : { ring: '#f43f5e', glow: 'rgba(244,63,94,0.4)', text: '#f43f5e' };

  const dim = size === 'lg' ? 80 : size === 'sm' ? 36 : 48;
  const r = size === 'lg' ? 34 : size === 'sm' ? 14 : 20;
  const sw = size === 'lg' ? 5 : 3;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const fontSize = size === 'lg' ? 22 : size === 'sm' ? 10 : 13;

  return (
    <div className="relative flex items-center justify-center" style={{ width: dim, height: dim }}>
      <svg width={dim} height={dim} style={{ position: 'absolute', top: 0, left: 0 }}>
        <circle cx={dim / 2} cy={dim / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={sw} />
        <circle
          cx={dim / 2} cy={dim / 2} r={r} fill="none" stroke={color.ring} strokeWidth={sw}
          strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset}
          transform={`rotate(-90 ${dim / 2} ${dim / 2})`}
          style={{ filter: `drop-shadow(0 0 4px ${color.glow})`, transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span style={{ color: color.text, fontSize, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
        {score}
      </span>
    </div>
  );
}

// ─── Stage Pill ──────────────────────────────────────────────────────────────

function StagePill({ stage }: { stage: string }) {
  const style =
    stage === 'Engaging'
      ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-500/30'
      : 'bg-violet-950/60 text-violet-300 border border-violet-500/30';
  const label = stage === 'Engaging' ? 'Engajando' : 'Prospecção';
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style}`}>{label}</span>;
}

// ─── Custom Dropdown ─────────────────────────────────────────────────────────

function Dropdown({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { label: string; value: string }[];
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selected = options.find((o) => o.value === value);
  const label = selected ? selected.label : placeholder;

  return (
    <div ref={ref} style={{ position: 'relative', userSelect: 'none' }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 10px 6px 12px',
          background: open ? 'rgba(34,211,238,0.06)' : 'rgba(255,255,255,0.04)',
          border: open ? '1px solid rgba(34,211,238,0.3)' : '1px solid rgba(255,255,255,0.1)',
          borderRadius: 8,
          color: value ? '#e2e8f0' : '#64748b',
          fontSize: 13,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
          transition: 'all 0.15s',
        }}
      >
        {label}
        <svg
          width={14} height={14} viewBox="0 0 24 24" fill="none"
          stroke={open ? '#22d3ee' : '#64748b'} strokeWidth={2}
          style={{ transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div
          style={{
            position: 'fixed',
            top: 56,
            minWidth: 200,
            background: '#0d1424',
            border: '1px solid rgba(34,211,238,0.2)',
            borderRadius: 10,
            boxShadow: '0 8px 32px rgba(0,0,0,0.6), 0 0 20px rgba(34,211,238,0.06)',
            zIndex: 9999,
            maxHeight: 340,
            overflowY: 'auto',
            overflowX: 'hidden',
          }}
        >
          {[{ label: placeholder, value: '' }, ...options].map((opt) => (
            <button
              key={opt.value}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                padding: '8px 14px',
                fontSize: 13,
                background: opt.value === value ? 'rgba(34,211,238,0.1)' : 'transparent',
                color: opt.value === value ? '#22d3ee' : opt.value === '' ? '#475569' : '#cbd5e1',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'background 0.1s',
              }}
              onMouseEnter={(e) => {
                if (opt.value !== value)
                  (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.05)';
              }}
              onMouseLeave={(e) => {
                if (opt.value !== value)
                  (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Breakdown Panel ─────────────────────────────────────────────────────────

function BreakdownPanel({ deal, onClose }: { deal: Deal; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div
        className="relative h-full w-full max-w-md overflow-y-auto"
        style={{
          background: 'linear-gradient(135deg, #0d1424 0%, #0a0e1a 100%)',
          borderLeft: '1px solid rgba(34,211,238,0.2)',
          boxShadow: '-8px 0 40px rgba(0,0,0,0.6)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/5">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-widest mb-1">Detalhes do Deal</div>
            <h2 className="text-white font-semibold text-lg leading-tight">{deal.account}</h2>
            <div className="text-slate-400 text-sm mt-0.5">{deal.opportunity_id}</div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors mt-1">
            <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Score gauge */}
        <div className="flex flex-col items-center py-8 border-b border-white/5">
          <ScoreBadge score={deal.score} size="lg" />
          <div className="text-slate-400 text-sm mt-3">Pontuação de 100</div>
          <div className="flex gap-2 mt-3">
            <StagePill stage={deal.deal_stage} />
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-white/10">
              {deal.days_in_pipeline}d no pipeline
            </span>
          </div>
        </div>

        {/* Score factors */}
        <div className="p-6 border-b border-white/5">
          <div className="text-xs text-slate-400 uppercase tracking-widest mb-4">Fatores do Score</div>
          <div className="flex flex-col gap-3">
            {deal.score_breakdown.map((factor) => (
              <div key={factor.label} className="flex items-start gap-3">
                <div
                  className="flex-shrink-0 px-2 py-0.5 rounded text-xs font-bold mt-0.5"
                  style={{
                    background: factor.positive ? 'rgba(34,197,94,0.15)' : 'rgba(244,63,94,0.15)',
                    color: factor.positive ? '#4ade80' : '#f87171',
                    border: `1px solid ${factor.positive ? 'rgba(34,197,94,0.3)' : 'rgba(244,63,94,0.3)'}`,
                  }}
                >
                  {factor.points > 0 ? '+' : ''}{factor.points}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium">{factor.label}</div>
                  <div className="text-slate-400 text-xs mt-0.5 leading-relaxed">{factor.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Deal info */}
        <div className="p-6 border-b border-white/5">
          <div className="text-xs text-slate-400 uppercase tracking-widest mb-4">Informações do Deal</div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Produto', deal.product || '—'],
              ['Setor', deal.sector],
              ['Vendedor', deal.sales_agent],
              ['Manager', deal.manager],
              ['Região', deal.regional_office],
              ['Engajamento', deal.engage_date],
            ].map(([label, value]) => (
              <div key={label}>
                <div className="text-slate-500 text-xs">{label}</div>
                <div className="text-slate-200 font-medium truncate">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendation */}
        <div className="p-6 border-b border-white/5">
          <div className="text-xs text-slate-400 uppercase tracking-widest mb-3">Ação Recomendada</div>
          <div className="rounded-lg p-4" style={{ background: 'rgba(34,211,238,0.06)', border: '1px solid rgba(34,211,238,0.2)' }}>
            <p className="text-cyan-200 text-sm leading-relaxed">{deal.recommendation}</p>
          </div>
        </div>

        {/* AI Agent Advice */}
        <div className="p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-indigo-500 to-violet-500 opacity-60"></div>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth={2}>
                <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div className="text-xs text-indigo-300 font-bold uppercase tracking-widest">Estratégia do Agente de IA</div>
          </div>
          <div 
            className="rounded-xl p-5 relative group"
            style={{ 
              background: 'linear-gradient(135deg, rgba(129,140,248,0.08) 0%, rgba(167,139,250,0.08) 100%)',
              border: '1px solid rgba(129,140,248,0.2)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
          >
            <div className="absolute -top-3 -right-3 px-2 py-0.5 rounded-full bg-indigo-500 text-[10px] font-black text-white uppercase tracking-tighter shadow-lg">AI Beta</div>
            <p className="text-slate-200 text-sm leading-relaxed italic pr-2 border-l-2 border-indigo-500/50 pl-4">
              "{deal.strategic_advice}"
            </p>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-[10px] text-indigo-400/60 font-medium">Análise em tempo real concluída</span>
              <div className="flex gap-1">
                {[1,2,3].map(i => <div key={i} className="w-1 h-1 rounded-full bg-indigo-400/40 animate-pulse" style={{ animationDelay: `${i * 0.2}s` }} />)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Manager View ─────────────────────────────────────────────────────────────

function ManagerView({ deals }: { deals: Deal[] }) {
  const [expandedManager, setExpandedManager] = useState<string | null>(null);

  const managerStats = useMemo(() => {
    const map: Record<string, { deals: Deal[]; avgScore: number }> = {};
    for (const deal of deals) {
      if (!map[deal.manager]) map[deal.manager] = { deals: [], avgScore: 0 };
      map[deal.manager].deals.push(deal);
    }
    for (const m of Object.values(map)) {
      m.avgScore = Math.round(m.deals.reduce((s, d) => s + d.score, 0) / m.deals.length);
      m.deals.sort((a, b) => b.score - a.score);
    }
    return Object.entries(map)
      .map(([manager, data]) => ({ manager, ...data }))
      .sort((a, b) => b.avgScore - a.avgScore);
  }, [deals]);

  return (
    <div>
      <div className="text-xs text-slate-400 uppercase tracking-widest mb-4">Visão por Manager</div>
      <div className="flex flex-col gap-2">
        {managerStats.map(({ manager, deals: mDeals, avgScore }, i) => (
          <div key={manager} className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.07)' }}>
            <button
              className="w-full flex items-center justify-between px-5 py-4 hover:bg-white/3 transition-colors text-left"
              onClick={() => setExpandedManager(expandedManager === manager ? null : manager)}
            >
              <div className="flex items-center gap-4">
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{
                    background: i === 0 ? 'rgba(34,211,238,0.2)' : 'rgba(255,255,255,0.05)',
                    color: i === 0 ? '#22d3ee' : '#94a3b8',
                  }}
                >
                  {i + 1}
                </div>
                <div>
                  <div className="text-white font-medium text-sm">{manager}</div>
                  <div className="text-slate-400 text-xs">{mDeals.length} deals ativos</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ScoreBadge score={avgScore} size="sm" />
                <svg
                  width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth={2}
                  style={{ transform: expandedManager === manager ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </div>
            </button>

            {expandedManager === manager && (
              <div className="border-t border-white/5">
                {mDeals.slice(0, 8).map((deal) => (
                  <div
                    key={deal.opportunity_id}
                    className="flex items-center gap-4 px-5 py-3 border-b border-white/3 last:border-0 hover:bg-white/2 transition-colors"
                  >
                    <ScoreBadge score={deal.score} size="sm" />
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-200 text-sm font-medium truncate">{deal.account}</div>
                      <div className="text-slate-500 text-xs">{deal.sales_agent}</div>
                    </div>
                    <StagePill stage={deal.deal_stage} />
                    <div className="text-slate-400 text-xs w-16 text-right">{deal.days_in_pipeline}d</div>
                  </div>
                ))}
                {mDeals.length > 8 && (
                  <div className="px-5 py-3 text-slate-500 text-xs">
                    +{mDeals.length - 8} deals adicionais...
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function LeadScorerDashboard({ deals, summary }: { deals: Deal[]; summary: Summary }) {
  const [search, setSearch] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [filterManager, setFilterManager] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [filterStage, setFilterStage] = useState('');
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [view, setView] = useState<'deals' | 'manager'>('deals');
  const [sortOrder, setSortOrder] = useState<'score-desc' | 'score-asc' | 'date-desc' | 'date-asc'>('score-desc');

  const filtered = useMemo(() => {
    const res = deals.filter((d) => {
      if (filterRegion && d.regional_office !== filterRegion) return false;
      if (filterManager && d.manager !== filterManager) return false;
      if (filterAgent && d.sales_agent !== filterAgent) return false;
      if (filterStage && d.deal_stage !== filterStage) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          d.account.toLowerCase().includes(q) ||
          d.opportunity_id.toLowerCase().includes(q) ||
          d.sales_agent.toLowerCase().includes(q) ||
          d.product.toLowerCase().includes(q)
        );
      }
      return true;
    });

    return res.sort((a, b) => {
      if (sortOrder === 'score-desc') return b.score - a.score;
      if (sortOrder === 'score-asc') return a.score - b.score;
      if (sortOrder === 'date-desc') return new Date(b.engage_date).getTime() - new Date(a.engage_date).getTime();
      if (sortOrder === 'date-asc') return new Date(a.engage_date).getTime() - new Date(b.engage_date).getTime();
      return 0;
    });
  }, [deals, filterRegion, filterManager, filterAgent, filterStage, search, sortOrder]);

  const hasFilters = filterRegion || filterManager || filterAgent || filterStage || search;

  return (
    <div style={{ minHeight: '100vh', background: '#070b14', color: '#e2e8f0', fontFamily: 'Inter, system-ui, sans-serif' }}>

      {/* Top nav */}
      <nav style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(7,11,20,0.9)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 40 }}>
        <div className="max-w-screen-2xl mx-auto px-6 h-14 flex items-center justify-between gap-4">

          {/* Logo */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg, #22d3ee, #818cf8)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.5}>
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span style={{ fontWeight: 700, fontSize: 16, color: 'white', letterSpacing: '-0.02em' }}>Pontuador de Leads</span>
          </div>

          {/* Search */}
          <div className="flex-1 max-w-sm mx-4">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '6px 12px' }}>
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth={2}>
                <circle cx={11} cy={11} r={8} /><path d="M21 21l-4.35-4.35" />
              </svg>
              <input
                type="text"
                placeholder="Buscar deals, contas, vendedores..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ background: 'none', border: 'none', outline: 'none', color: '#e2e8f0', fontSize: 13, width: '100%' }}
              />
            </div>
          </div>

          {/* Dropdowns */}
          <div className="flex items-center gap-2">
            <Dropdown
              value={filterRegion}
              onChange={setFilterRegion}
              placeholder="Todas as Regiões"
              options={summary.regions.map((r) => ({
                label: r === 'East' ? 'Leste' : r === 'West' ? 'Oeste' : r,
                value: r,
              }))}
            />
            <Dropdown
              value={filterManager}
              onChange={setFilterManager}
              placeholder="Todos os Managers"
              options={summary.managers.map((m) => ({ label: m, value: m }))}
            />
            <Dropdown
              value={filterAgent}
              onChange={setFilterAgent}
              placeholder="Todos os Vendedores"
              options={summary.agents.map((a) => ({ label: a, value: a }))}
            />
            <div className="h-6 w-px bg-white/10 mx-1"></div>
            <Dropdown
              value={sortOrder}
              onChange={(v) => setSortOrder(v as any)}
              placeholder="Ordenar"
              options={[
                { label: 'Maior Score', value: 'score-desc' },
                { label: 'Menor Score', value: 'score-asc' },
                { label: 'Mais Recentes', value: 'date-desc' },
                { label: 'Mais Antigos', value: 'date-asc' },
              ]}
            />
          </div>
        </div>
      </nav>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 flex gap-6">

        {/* Sidebar */}
        <aside className="w-56 flex-shrink-0">
          <div className="rounded-2xl p-5 mb-4" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(34,211,238,0.15)', boxShadow: '0 0 30px rgba(34,211,238,0.05)' }}>
            <div className="text-slate-400 text-xs uppercase tracking-widest mb-1">Deals Ativos</div>
            <div style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-0.04em', background: 'linear-gradient(135deg, #22d3ee, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              {filtered.length.toLocaleString('pt-BR')}
            </div>
            {hasFilters && (
              <div className="text-slate-500 text-xs mt-1">de {summary.total_active.toLocaleString('pt-BR')} no total</div>
            )}
            <div className="border-t border-white/5 mt-4 pt-4">
              <div className="text-slate-400 text-xs uppercase tracking-widest mb-1">Score Médio</div>
              <div className="text-3xl font-bold text-amber-400">
                {filtered.length > 0 ? Math.round(filtered.reduce((s, d) => s + d.score, 0) / filtered.length) : '—'}
              </div>
            </div>
          </div>

          <div className="rounded-2xl p-5" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="text-slate-400 text-xs uppercase tracking-widest mb-3">Filtro Rápido</div>
            <div className="flex flex-col gap-1.5">
              {[
                { label: 'Todos Ativos', value: '', count: summary.total_active },
                { label: 'Engajando', value: 'Engaging', count: summary.by_stage.Engaging },
                { label: 'Prospecção', value: 'Prospecting', count: summary.by_stage.Prospecting },
              ].map((opt) => (
                <button
                  key={opt.label}
                  onClick={() => setFilterStage(opt.value)}
                  className="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
                  style={{
                    background: filterStage === opt.value ? 'rgba(34,211,238,0.1)' : 'transparent',
                    color: filterStage === opt.value ? '#22d3ee' : '#94a3b8',
                    border: filterStage === opt.value ? '1px solid rgba(34,211,238,0.2)' : '1px solid transparent',
                  }}
                >
                  <span>{opt.label}</span>
                  <span className="text-xs opacity-60">{opt.count}</span>
                </button>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/5">
              <button
                onClick={() => setView(view === 'deals' ? 'manager' : 'deals')}
                className="w-full px-3 py-2 rounded-lg text-sm transition-colors"
                style={{
                  background: view === 'manager' ? 'rgba(129,140,248,0.1)' : 'rgba(255,255,255,0.04)',
                  color: view === 'manager' ? '#818cf8' : '#64748b',
                  border: view === 'manager' ? '1px solid rgba(129,140,248,0.2)' : '1px solid rgba(255,255,255,0.06)',
                }}
              >
                {view === 'deals' ? '👥 Visão Manager' : '📋 Tabela de Deals'}
              </button>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {view === 'manager' ? (
            <ManagerView deals={filtered} />
          ) : filtered.length === 0 ? (
            /* Empty state */
            <div className="rounded-2xl flex flex-col items-center justify-center py-24" style={{ border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.01)' }}>
              <div style={{ width: 64, height: 64, borderRadius: 16, background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <svg width={28} height={28} viewBox="0 0 24 24" fill="none" stroke="#f43f5e" strokeWidth={1.5}>
                  <circle cx={11} cy={11} r={8} /><path d="M21 21l-4.35-4.35M8 11h6" />
                </svg>
              </div>
              <div className="text-white font-semibold text-lg mb-1">Nenhum deal encontrado</div>
              <div className="text-slate-400 text-sm mb-6">Tente ajustar os filtros ou o termo de busca</div>
              <button
                onClick={() => { setSearch(''); setFilterRegion(''); setFilterManager(''); setFilterAgent(''); setFilterStage(''); }}
                className="px-5 py-2 rounded-lg text-sm font-medium transition-colors"
                style={{ background: 'rgba(34,211,238,0.1)', border: '1px solid rgba(34,211,238,0.3)', color: '#22d3ee' }}
              >
                Limpar filtros
              </button>
            </div>
          ) : (
            /* Deal table */
            <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    {['Pontuação', 'Conta', 'Produto', 'Estágio', 'Dias', 'Vendedor', 'Região'].map((h) => (
                      <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', background: 'rgba(255,255,255,0.01)', whiteSpace: 'nowrap' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 100).map((deal, i) => (
                    <tr
                      key={deal.opportunity_id}
                      onClick={() => setSelectedDeal(deal)}
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', background: i % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent', cursor: 'pointer', transition: 'background 0.15s' }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = 'rgba(34,211,238,0.04)'; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = i % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent'; }}
                    >
                      <td style={{ padding: '10px 16px' }}><ScoreBadge score={deal.score} size="sm" /></td>
                      <td style={{ padding: '10px 16px' }}>
                        <div style={{ color: '#e2e8f0', fontWeight: 500, fontSize: 14 }}>{deal.account}</div>
                        <div style={{ color: '#475569', fontSize: 11, marginTop: 1 }}>{deal.sector}</div>
                      </td>
                      <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{deal.product || '—'}</td>
                      <td style={{ padding: '10px 16px' }}><StagePill stage={deal.deal_stage} /></td>
                      <td style={{ padding: '10px 16px', color: '#64748b', fontSize: 13, textAlign: 'center' }}>{deal.days_in_pipeline}</td>
                      <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 13 }}>{deal.sales_agent}</td>
                      <td style={{ padding: '10px 16px', color: '#64748b', fontSize: 13 }}>{deal.regional_office}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length > 100 && (
                <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.04)', color: '#475569', fontSize: 13, textAlign: 'center' }}>
                  Exibindo os top 100 de {filtered.length} deals — use os filtros para refinar
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Breakdown panel */}
      {selectedDeal && <BreakdownPanel deal={selectedDeal} onClose={() => setSelectedDeal(null)} />}
    </div>
  );
}
