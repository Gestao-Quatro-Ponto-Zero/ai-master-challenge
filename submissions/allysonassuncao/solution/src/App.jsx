import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle, ArrowDown, ArrowLeft, ArrowRight, ArrowUp, ArrowUpRight, BriefcaseBusiness, Check,
  ChevronRight, CircleDollarSign, Clock3, DollarSign, FileWarning,
  LayoutDashboard, ListFilter, LoaderCircle, Menu, RefreshCw, RotateCcw, Search,
  Target, Users, X,
} from 'lucide-react';

const navItems = [
  ['today', 'Foco de hoje', LayoutDashboard],
  ['pipeline', 'Pipeline', ListFilter],
  ['team', 'Equipe', Users],
  ['recovery', 'Repescagem', RotateCcw],
];

const roleLabels = { seller: 'Vendedor', manager: 'Manager', revops: 'RevOps' };
const toneByAction = { 'Avançar agora': 'advance', 'Definir próximo passo': 'qualify', 'Reengajar hoje': 'reengage', 'Requalificar ou encerrar': 'decide', 'Completar dados': 'data' };
const toneByScore = { Alto: 'high', Médio: 'medium', Baixo: 'low' };
const usd = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

async function requestJson(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error ?? 'Não foi possível carregar os dados.');
  return payload;
}

export default function App() {
  const [bootstrap, setBootstrap] = useState(null);
  const [role, setRole] = useState('seller');
  const [profile, setProfile] = useState('Darcel Schlecht');
  const [view, setView] = useState('today');
  const [dashboard, setDashboard] = useState(null);
  const [pipeline, setPipeline] = useState({ rows: [], total: 0, page: 1, pageSize: 25 });
  const [team, setTeam] = useState({ sellers: [], products: [], regions: [], losses: { count: 0, potentialValue: 0 } });
  const [recovery, setRecovery] = useState([]);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [actionDeal, setActionDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [filters, setFilters] = useState({ search: '', action: '', scoreBand: '', stage: '', product: '', region: '', page: 1 });

  const scopeQuery = useMemo(() => new URLSearchParams({ role, profile }).toString(), [role, profile]);
  const profiles = bootstrap?.profiles?.[role === 'seller' ? 'sellers' : role === 'manager' ? 'managers' : 'revops'] ?? [];

  const loadBootstrap = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const base = await requestJson('/api/bootstrap');
      setBootstrap(base);
      if (!base.profiles.sellers.includes(profile)) setProfile(base.profiles.sellers[0]);
    } catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }, [profile]);

  const loadDashboard = useCallback(async () => {
    try { setDashboard(await requestJson(`/api/dashboard?${scopeQuery}`)); }
    catch (reason) { setError(reason.message); }
  }, [scopeQuery]);

  const loadPipeline = useCallback(async () => {
    const query = new URLSearchParams({ role, profile, page: String(filters.page), pageSize: '25' });
    Object.entries(filters).forEach(([key, value]) => { if (value && key !== 'page') query.set(key, value); });
    try { setPipeline(await requestJson(`/api/pipeline?${query}`)); }
    catch (reason) { setError(reason.message); }
  }, [role, profile, filters]);

  useEffect(() => { loadBootstrap(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (bootstrap) loadDashboard(); }, [bootstrap, loadDashboard]);
  useEffect(() => {
    if (!bootstrap) return;
    if (view === 'pipeline') loadPipeline();
    if (view === 'team') requestJson(`/api/team?${scopeQuery}`).then(setTeam).catch((reason) => setError(reason.message));
    if (view === 'recovery') requestJson(`/api/recovery?${scopeQuery}`).then(setRecovery).catch((reason) => setError(reason.message));
  }, [bootstrap, view, scopeQuery, loadPipeline]);

  function changeRole(nextRole) {
    setRole(nextRole);
    const key = nextRole === 'seller' ? 'sellers' : nextRole === 'manager' ? 'managers' : 'revops';
    setProfile(bootstrap?.profiles?.[key]?.[0] ?? '');
    setFilters((current) => ({ ...current, page: 1 }));
  }

  async function openDeal(id) {
    try { setSelectedDeal(await requestJson(`/api/deals/${id}`)); }
    catch (reason) { setError(reason.message); }
  }

  async function saveAction(deal, action) {
    try {
      await requestJson('/api/actions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ opportunityId: deal.opportunity_id, actorProfile: profile, ...action }) });
      setNotice(action.status === 'completed' ? 'Ação concluída e removida do foco de hoje.' : action.status === 'snoozed' ? 'Ação adiada com sucesso.' : 'Nota e próximo passo salvos.');
      setActionDeal(null); setSelectedDeal(null);
      await loadDashboard();
      if (view === 'pipeline') await loadPipeline();
      window.setTimeout(() => setNotice(''), 3500);
    } catch (reason) { setError(reason.message); }
  }

  if (loading) return <LoadingState />;
  if (error && !bootstrap) return <ErrorState message={error} onRetry={loadBootstrap} />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <button className="icon-button mobile-only" aria-label="Abrir menu"><Menu size={18} /></button>
          <span className="brand-mark"><Target size={17} /></span>
          <div><strong>Foco de Hoje</strong><small>Revenue intelligence</small></div>
        </div>
        <div className="topbar-actions">
          <span className="snapshot"><i /> Offline · Snapshot 31 dez 2017</span>
          <select value={role} onChange={(event) => changeRole(event.target.value)} aria-label="Selecionar tipo de perfil">
            <option value="seller">Vendedor</option><option value="manager">Manager</option><option value="revops">RevOps</option>
          </select>
          <select value={profile} onChange={(event) => setProfile(event.target.value)} aria-label="Selecionar perfil">
            {profiles.map((name) => <option key={name}>{name}</option>)}
          </select>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <p className="nav-label">Espaço de trabalho</p>
          <nav aria-label="Navegação principal">
            {navItems.map(([id, label, Icon]) => <button className={view === id ? 'active' : ''} key={id} onClick={() => setView(id)}><Icon size={17} /><span>{label}</span></button>)}
          </nav>
          <div className="offline-card"><strong><i /> Banco local ativo</strong><p>Dados e ações ficam armazenados neste computador.</p></div>
        </aside>

        <main>
          <section className="content">
            {error && <div className="inline-alert"><AlertTriangle size={17} /><span>{error}</span><button onClick={() => setError('')} aria-label="Fechar alerta"><X size={15} /></button></div>}
            {notice && <div className="toast-notice"><Check size={16} />{notice}</div>}
            {view === 'today' && <TodayView profile={profile} role={role} dashboard={dashboard} onNavigate={setView} onDeal={openDeal} onComplete={(deal) => saveAction(deal, { status: 'completed' })} />}
            {view === 'pipeline' && <PipelineView data={pipeline} filters={filters} setFilters={setFilters} bootstrap={bootstrap} onDeal={openDeal} />}
            {view === 'team' && <TeamView data={team} role={role} profile={profile} />}
            {view === 'recovery' && <RecoveryView rows={recovery} />}
          </section>
        </main>
      </div>

      {selectedDeal && <DealDrawer deal={selectedDeal} onClose={() => setSelectedDeal(null)} onComplete={() => saveAction(selectedDeal, { status: 'completed' })} onAction={() => { setActionDeal(selectedDeal); setSelectedDeal(null); }} />}
      {actionDeal && <ActionDialog deal={actionDeal} profile={profile} onClose={() => setActionDeal(null)} onSave={(action) => saveAction(actionDeal, action)} />}
    </div>
  );
}

function TodayView({ profile, role, dashboard, onNavigate, onDeal, onComplete }) {
  if (!dashboard) return <LoadingPanel />;
  const firstName = role === 'seller' ? profile.split(' ')[0] : roleLabels[role];
  return <>
    <PageHeading eyebrow="Segunda-feira, 31 de dezembro" title={`Bom dia, ${firstName}.`} actions={<button className="button secondary" onClick={() => onNavigate('pipeline')}><ListFilter size={16} /> Abrir pipeline</button>} />
    <div className="metrics five">
      <Metric label="Valor potencial da pipeline" value={usd.format(dashboard.totalExpectedRevenue)} detail="Todas as oportunidades abertas" icon={CircleDollarSign} tone="mint" />
      <Metric label="Merecem seu foco imediato" value={dashboard.scoreCounts.Alto ?? 0} detail="Oportunidades com 70 pontos ou mais de lead score" icon={Target} tone="navy" />
      <Metric label="Avançar agora" value={dashboard.counts['Avançar agora'] ?? 0} detail="Oportunidades em Engaging" icon={ArrowUpRight} tone="mint" />
      <Metric label="Definir próximo passo" value={dashboard.counts['Definir próximo passo'] ?? 0} detail="Oportunidades em Prospecting" icon={BriefcaseBusiness} tone="amber" />
      <Metric label="Recuperar ou decidir" value={(dashboard.counts['Reengajar hoje'] ?? 0) + (dashboard.counts['Requalificar ou encerrar'] ?? 0)} detail="Fora do ciclo" icon={Clock3} tone="coral" />
    </div>
    <div className="section-heading"><div><h2>Foco de hoje</h2><p>Top 5 oportunidades da sua pipeline</p></div><button className="text-button" onClick={() => onNavigate('pipeline')}>Ver pipeline completo <ChevronRight size={16} /></button></div>
    {dashboard.top.length ? <div className="deal-grid">{dashboard.top.map((deal, index) => <DealCard key={deal.opportunity_id} deal={deal} rank={index + 1} onDeal={onDeal} onComplete={onComplete} />)}</div> : <EmptyState icon={Check} title="Tudo em dia" description="Não há ações disponíveis para este perfil hoje." />}
  </>;
}

function PipelineView({ data, filters, setFilters, bootstrap, onDeal }) {
  const pageCount = Math.max(1, Math.ceil(data.total / data.pageSize));
  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value, page: key === 'page' ? value : 1 }));
  return <>
    <PageHeading eyebrow="Visão operacional" title="Pipeline priorizado" description={<>Quanto maior o Score de foco, mais cedo a oportunidade aparece. A soma está visível em cada linha.</>} />
    <div className="filter-bar">
      <label className="search wide"><Search size={17} /><input value={filters.search} onChange={(event) => update('search', event.target.value)} placeholder="Buscar conta, produto, vendedor ou ID" /></label>
      <FilterSelect value={filters.action} onChange={(value) => update('action', value)} options={bootstrap.filters.actions} label="Todas as ações" />
      <FilterSelect value={filters.scoreBand} onChange={(value) => update('scoreBand', value)} options={bootstrap.filters.scoreBands} label="Todos os scores" />
      <FilterSelect value={filters.stage} onChange={(value) => update('stage', value)} options={['Prospecting', 'Engaging']} label="Todos os estágios" />
      <FilterSelect value={filters.product} onChange={(value) => update('product', value)} options={bootstrap.filters.products} label="Todos os produtos" />
      <FilterSelect value={filters.region} onChange={(value) => update('region', value)} options={bootstrap.filters.regions} label="Todas as regiões" />
    </div>
    <div className="table-card">
      <div className="table-meta"><strong>{data.total.toLocaleString('pt-BR')} oportunidades</strong><span>Score calculado contra 31/12/2017</span></div>
      <div className="table-scroll"><table><thead><tr><th>Lead score</th><th>Oportunidade</th><th>Como chegou ao score</th><th>Nível</th><th>Estágio</th><th>Vendedor</th><th>Detalhes</th></tr></thead><tbody>
        {data.rows.map((deal) => <tr key={deal.opportunity_id} onClick={() => onDeal(deal.opportunity_id)} tabIndex="0"><td><span className="table-score">{deal.focus_score}</span></td><td><strong>{deal.account ?? 'Conta não informada'}</strong><small>{deal.product} · {deal.opportunity_id}</small></td><td><PipelineScoreBreakdown deal={deal} /></td><td><FocusBadge value={deal.focus_band} /></td><td><strong>{deal.deal_stage}</strong><small>{deal.timing_status}</small></td><td><strong>{deal.sales_agent}</strong><small>{deal.regional_office}</small></td><td><span className="row-action">Ver por quê <ChevronRight size={15} /></span></td></tr>)}
      </tbody></table></div>
      {!data.rows.length && <EmptyState icon={Search} title="Nenhum resultado" description="Ajuste os filtros para ampliar a busca." compact />}
      <div className="pagination"><span>Página {data.page} de {pageCount}</span><div><button disabled={data.page <= 1} onClick={() => update('page', data.page - 1)}><ArrowLeft size={15} /> Anterior</button><button disabled={data.page >= pageCount} onClick={() => update('page', data.page + 1)}>Próxima <ArrowRight size={15} /></button></div></div>
    </div>
  </>;
}

function TeamView({ data, role, profile }) {
  const rows = data.sellers ?? [];
  const totalRevenue = rows.reduce((sum, row) => sum + row.expectedRevenue, 0);
  const totalPotentialValue = rows.reduce((sum, row) => sum + row.potentialValue, 0);
  return <>
    <PageHeading eyebrow="Gestão comercial" title="Visão da equipe" description={<>Compare carga, receita esperada, valor potencial e concentração de oportunidades por vendedor no escopo de <strong>{role === 'revops' ? 'RevOps' : profile}</strong>.</>} />
    <div className="metrics"><Metric label="Vendedores no escopo" value={rows.length} detail="Com pipeline aberto" icon={Users} tone="navy" /><Metric label="Receita esperada" value={usd.format(totalRevenue)} detail="Valor ponderado pelo histórico de vendas" icon={CircleDollarSign} tone="mint" /><Metric label="Valor potencial" value={usd.format(totalPotentialValue)} detail="Valor integral dos produtos na pipeline" icon={BriefcaseBusiness} tone="amber" /><Metric label="Pendências de decisão" value={rows.reduce((sum, row) => sum + row.pending, 0)} detail="Requalificar ou completar" icon={FileWarning} tone="coral" /></div>
    <SellerReading rows={rows} />
    <div className="loss-reading"><div><p>Oportunidades perdidas</p><strong>{data.losses?.count ?? 0}</strong><span>Negócios encerrados sem venda no escopo selecionado</span></div><div><p>Valor potencial perdido</p><strong>{usd.format(data.losses?.potentialValue ?? 0)}</strong><span>Soma dos valores de catálogo associados às perdas</span></div></div>
    <div className="commercial-readings">
      <CommercialReading title="Leitura por produto" description="Identifique produtos com maior volume de perdas ou melhor conversão." rows={data.products ?? []} label="Produto" />
      <CommercialReading title="Leitura por região" description="Compare desempenho e perdas entre os escritórios regionais." rows={data.regions ?? []} label="Região" />
    </div>
  </>;
}

function useSortableRows(rows, initialKey, initialDirection = 'desc') {
  const [sort, setSort] = useState({ key: initialKey, direction: initialDirection });
  const sortedRows = useMemo(() => [...rows].sort((left, right) => {
    const leftValue = left[sort.key] ?? '';
    const rightValue = right[sort.key] ?? '';
    const comparison = typeof leftValue === 'number' && typeof rightValue === 'number'
      ? leftValue - rightValue
      : String(leftValue).localeCompare(String(rightValue), 'pt-BR', { numeric: true, sensitivity: 'base' });
    return sort.direction === 'asc' ? comparison : -comparison;
  }), [rows, sort]);
  const toggleSort = (key) => setSort((current) => ({ key, direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc' }));
  return { sortedRows, sort, toggleSort };
}

function SortHeader({ label, sortKey, sort, onSort }) {
  const active = sort.key === sortKey;
  return <th aria-sort={active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}><button className={`sort-button ${active ? 'active' : ''}`} onClick={() => onSort(sortKey)}>{label}{active ? (sort.direction === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />) : <span className="sort-placeholder">↕</span>}</button></th>;
}

function SellerReading({ rows }) {
  const { sortedRows, sort, toggleSort } = useSortableRows(rows, 'expectedRevenue');
  const columns = [
    ['Vendedor', 'sales_agent'], ['Região', 'regional_office'], ['Abertas', 'open'], ['Score médio', 'averageScore'],
    ['Avançar / definir passo', 'advance'], ['Reengajar', 'reengage'], ['Pendências', 'pending'], ['Score alto', 'highFocus'],
    ['Valor potencial', 'potentialValue'], ['Receita esperada', 'expectedRevenue'], ['Potencial perdido', 'lostPotential'],
  ];
  return <div className="table-card"><div className="table-scroll"><table><thead><tr>{columns.map(([label, key]) => <SortHeader key={key} label={label} sortKey={key} sort={sort} onSort={toggleSort} />)}</tr></thead><tbody>{sortedRows.map((row) => <tr key={row.sales_agent}><td><strong>{row.sales_agent}</strong><small>{row.manager}</small></td><td>{row.regional_office}</td><td>{row.open}</td><td><span className="table-score small">{row.averageScore}</span></td><td>{row.advance}</td><td>{row.reengage}</td><td>{row.pending}</td><td>{row.highFocus}</td><td><strong>{usd.format(row.potentialValue)}</strong></td><td><strong>{usd.format(row.expectedRevenue)}</strong></td><td><strong>{usd.format(row.lostPotential)}</strong></td></tr>)}</tbody></table></div></div>;
}

function CommercialReading({ title, description, rows, label }) {
  const { sortedRows, sort, toggleSort } = useSortableRows(rows, 'lostPotential');
  const columns = [[label, 'label'], ['Abertas', 'open'], ['Vendas', 'won'], ['Perdidas', 'lost'], ['Conversão', 'winRate'], ['Valor potencial', 'openPotential'], ['Receita esperada', 'expectedRevenue'], ['Potencial perdido', 'lostPotential']];
  return <section className="reading-card"><header><h2>{title}</h2><p>{description}</p></header><div className="table-scroll"><table className="compact-table"><thead><tr>{columns.map(([columnLabel, key]) => <SortHeader key={key} label={columnLabel} sortKey={key} sort={sort} onSort={toggleSort} />)}</tr></thead><tbody>{sortedRows.map((row) => <tr key={row.label}><td><strong>{row.label}</strong></td><td>{row.open}</td><td>{row.won}</td><td>{row.lost}</td><td>{Math.round(row.winRate)}%</td><td>{usd.format(row.openPotential)}</td><td>{usd.format(row.expectedRevenue)}</td><td>{usd.format(row.lostPotential)}</td></tr>)}</tbody></table></div></section>;
}

function RecoveryView({ rows }) {
  return <>
    <PageHeading eyebrow="Receita recuperável" title="Repescagem" description={<>Prioridade de recuperação baseada em <strong>Valor + Recência + Histórico do produto</strong>. Quando existe evidência suficiente, o sistema sugere outro vendedor da mesma região.</>} />
    <div className="method-note"><AlertTriangle size={18} /><div><strong>O dataset não informa o motivo da perda</strong><p>Antes de abordar, revise o contexto e registre o motivo real no CRM.</p></div></div>
    <div className="recovery-guide"><span><b>40 pts</b> valor do produto</span><span><b>40 pts</b> perda recente</span><span><b>20 pts</b> histórico do produto</span></div>
    {rows.length ? <div className="recovery-grid">{rows.slice(0, 24).map((deal) => <article className="recovery-card" key={deal.opportunity_id}><header><span className="recovery-score">{deal.recovery_score}<small>pontos</small></span><div><h3>{deal.account}</h3><p>{deal.product} · {deal.opportunity_id}</p></div></header><div className="recovery-details"><span><Clock3 size={15} /> Perdido há {deal.days_since_loss} dias</span><span><DollarSign size={15} /> {usd.format(deal.sales_price)}</span><span><Users size={15} /> Origem: {deal.sales_agent} · {deal.regional_office}</span></div><div className="recovery-breakdown">{deal.recovery_explanation.map((part) => <span key={part.key}><b>{part.label}</b><strong>{part.points}/{part.max}</strong></span>)}</div><section className={`redistribution ${deal.redistribution.recommended ? 'recommended' : ''}`}><small>{deal.redistribution.recommended ? 'Redistribuição sugerida' : 'Ação sugerida'}</small><strong>{deal.redistribution.action}</strong>{deal.redistribution.recommended && <span>{deal.redistribution.manager} · {deal.redistribution.region}</span>}<p>{deal.redistribution.reason}</p></section><footer><p>{deal.recommended_action}</p></footer></article>)}</div> : <EmptyState icon={RotateCcw} title="Sem candidatos no escopo" description="Não encontramos perdas que atendam simultaneamente aos critérios de repescagem." />}
  </>;
}

function PageHeading({ eyebrow, title, description, actions }) {
  return <div className="page-heading"><div><p className="eyebrow"><i />{eyebrow}</p><h1>{title}</h1>{description && <p className="lead">{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>;
}

function Metric({ label, value, detail, icon: Icon, tone }) {
  return <article className="metric"><div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div><span className={`metric-icon ${tone}`}><Icon size={21} /></span></article>;
}

function DealCard({ deal, rank, onDeal, onComplete }) {
  return <div className={`ranked-deal rank-${rank}`}><div className="deal-rank" aria-label={`${rank}º lugar no foco de hoje`}><strong>{rank}º</strong><span>prioridade</span></div><article className="deal-card simplified"><header><div className="score-total"><strong>{deal.focus_score}</strong><span>pontos</span></div><div className="deal-title"><h3>{deal.account ?? 'Conta não informada'}</h3><p>{deal.product} · {deal.opportunity_id}</p><span className="deal-expected-revenue">Valor potencial: <strong>{usd.format(Number(deal.sales_price ?? 0))}</strong></span></div><FocusBadge value={deal.focus_band} /></header><div className="deal-body"><section className="todo-block"><small>To-do</small><strong>{deal.recommended_action}</strong></section><section className="calculation-block"><h4>Cálculo do score</h4><ol>{deal.score_explanation.map((part) => <li key={part.key}><span>{part.label}</span><p>{part.detail}</p><strong>{part.points} pontos</strong></li>)}</ol></section></div><footer><button className="button secondary details-button" onClick={() => onDeal(deal.opportunity_id)}>Mais detalhes do score <ChevronRight size={15} /></button><button className="button primary" onClick={() => onComplete(deal)}><Check size={15} /> Concluir</button></footer></article></div>;
}

function ActionBadge({ value }) { return <span className={`action-badge ${toneByAction[value] ?? 'reengage'}`}>{value}</span>; }
function FocusBadge({ value }) { return <span className={`potential-badge ${toneByScore[value]}`}>Foco {value.toLowerCase()}</span>; }
function ScoreEquation({ deal, compact = false }) {
  return <div className={`score-equation ${compact ? 'compact' : ''}`}>{deal.score_explanation.map((part, index) => <div key={part.key}><span>{part.label}</span><strong>{part.points}<small>/{part.max}</small></strong>{!compact && <p>{part.detail}</p>}{index < deal.score_explanation.length - 1 && <i>+</i>}</div>)}</div>;
}

function PipelineScoreBreakdown({ deal }) {
  return <div className="pipeline-score-breakdown">{deal.score_explanation.map((part) => <div key={part.key}><span>{part.label}</span><i><b style={{ width: `${(part.points / part.max) * 100}%` }} /></i><strong>{part.points}<small>/{part.max}</small></strong></div>)}</div>;
}

function FilterSelect({ value, onChange, options, label }) { return <select value={value} onChange={(event) => onChange(event.target.value)}><option value="">{label}</option>{options.map((option) => <option key={option}>{option}</option>)}</select>; }

function DealDrawer({ deal, onClose, onComplete, onAction }) {
  return <div className="overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="drawer" role="dialog" aria-modal="true" aria-label="Detalhes da oportunidade"><header className="drawer-header"><div><p>Oportunidade {deal.opportunity_id}</p><h2>{deal.account ?? 'Conta não informada'}</h2><span>{deal.product} · {deal.sales_agent}</span></div><button className="icon-button" onClick={onClose} aria-label="Fechar"><X /></button></header><div className="drawer-body"><section className="drawer-section action-callout first"><Target size={18} /><div><small>Faça agora</small><ActionBadge value={deal.action_label} /><strong>{deal.recommended_action}</strong></div></section><section className="drawer-section score-proof"><div className="score-proof-title"><div><small>Score de foco</small><strong>{deal.focus_score}<span>/100</span></strong></div><FocusBadge value={deal.focus_band} /></div><ScoreEquation deal={deal} /></section><section className="drawer-section"><h3>Em português claro</h3><ul className="reasons-list">{deal.reasons.map((reason, index) => <li className={reason.tone} key={`${reason.text}-${index}`}><span>{reason.tone === 'positive' ? '+' : '!'}</span>{reason.text}</li>)}</ul></section></div><footer className="drawer-footer"><button className="button secondary" onClick={onAction}><Clock3 size={15} /> Adiar ou anotar</button><button className="button primary" onClick={onComplete}><Check size={15} /> Concluir ação</button></footer></aside></div>;
}

function ActionDialog({ deal, onClose, onSave }) {
  const [status, setStatus] = useState('pending'); const [note, setNote] = useState(''); const [nextStep, setNextStep] = useState(deal.recommended_action); const [dueDate, setDueDate] = useState('');
  return <div className="overlay centered"><form className="action-dialog" onSubmit={(event) => { event.preventDefault(); onSave({ status, note, nextStep, dueDate: status === 'snoozed' ? dueDate : null }); }}><header><div><p>{deal.account ?? 'Conta não informada'} · {deal.opportunity_id}</p><h2>Registrar ação</h2></div><button type="button" className="icon-button" onClick={onClose}><X /></button></header><label>Resultado<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="pending">Salvar nota e manter pendente</option><option value="snoozed">Adiar para outra data</option><option value="completed">Marcar como concluída</option></select></label>{status === 'snoozed' && <label>Retornar em<input type="date" required value={dueDate} onChange={(event) => setDueDate(event.target.value)} /></label>}<label>Próximo passo<input value={nextStep} onChange={(event) => setNextStep(event.target.value)} /></label><label>Nota<textarea rows="4" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Contexto comercial, objeções ou compromisso assumido" /></label><footer><button type="button" className="button secondary" onClick={onClose}>Cancelar</button><button className="button primary"><Check size={15} /> Salvar ação</button></footer></form></div>;
}

function EmptyState({ icon: Icon, title, description, compact = false }) { return <div className={`empty-state ${compact ? 'compact' : ''}`}><Icon /><h3>{title}</h3><p>{description}</p></div>; }
function LoadingPanel() { return <div className="loading-panel"><LoaderCircle className="spin" /><span>Organizando as prioridades…</span></div>; }
function LoadingState() { return <main className="full-state"><span className="brand-mark"><Target /></span><LoaderCircle className="spin" /><h1>Preparando o Foco de Hoje</h1><p>Importando e pontuando o pipeline local.</p></main>; }
function ErrorState({ message, onRetry }) { return <main className="full-state error"><AlertTriangle /><h1>Não conseguimos abrir o banco local</h1><p>{message}</p><button className="button primary" onClick={onRetry}><RefreshCw size={16} /> Tentar novamente</button></main>; }
