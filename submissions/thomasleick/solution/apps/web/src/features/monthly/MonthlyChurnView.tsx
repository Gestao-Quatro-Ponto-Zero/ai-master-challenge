import { Bar, CartesianGrid, ComposedChart, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useMemo, useState } from 'react'
import type { KeyMoment, PortfolioPeriod } from '../../contracts'

const count = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const percent = (value: number | null) => value === null ? 'UNDEFINED' : `${value.toFixed(2)}%`

type TooltipRow = { payload?: PortfolioPeriod }
function MonthlyRateTooltip({ active, payload }: { active?: boolean; payload?: TooltipRow[] }) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  const measures = [
    { name: 'Plan proxy · gross opening-cohort loss', value: row.opening_cohort_churn_any_pct, n: row.opening_relations_lost_any_time, d: row.opening_plan_relations },
    { name: 'Plan proxy · still lost at close', value: row.opening_cohort_churn_at_close_pct, n: row.opening_relations_lost_at_close, d: row.opening_plan_relations },
    { name: 'Customer · gross full-coverage loss', value: row.opening_cohort_customer_churn_any_pct, n: row.opening_customers_lost_any_time, d: row.opening_customers },
    { name: 'Customer · still lost at close', value: row.opening_cohort_customer_churn_at_close_pct, n: row.opening_customers_lost_at_close, d: row.opening_customers },
  ]
  return <div className="monthly-churn-tooltip"><strong>{row.period}</strong>{measures.map((measure) => <div className="monthly-churn-tooltip-row" key={measure.name}><b>{measure.name}</b><span>{measure.value === null ? `UNDEFINED · ${measure.n}/${measure.d}` : `${measure.value.toFixed(2)}% · ${measure.n}/${measure.d}`}</span><small>Formula: opening-cohort losses ÷ opening base × 100</small></div>)}<small>Evidence: CONDITIONAL_DATE_RECONSTRUCTION · account × plan-tier proxy</small></div>
}

function RateCell({ numerator, denominator, value, title }: { numerator: number; denominator: number; value: number | null; title: string }) {
  return <span title={`${title}: ${numerator} / ${denominator} × 100. Conditional date reconstruction.`}>{numerator}/{denominator} · {percent(value)}</span>
}

const momentNames: Record<KeyMoment['type'], string> = {
  RATE_PEAK: 'Highest monthly cohort loss rate',
  LOSS_VOLUME_PEAK: 'Highest gross plan-loss volume',
  ACQUISITION_CHANGE: 'Largest month-to-month acquisition change',
  RECOVERY_MOMENT: 'Reactivation high point',
  PORTFOLIO_CONTRACTION: 'Portfolio contraction / possible downgrade',
  RATE_VS_VOLUME_DIVERGENCE: 'Rate and count moved in opposite directions',
  DATA_QUALITY_EVENT: 'Largest event-to-lifecycle discrepancy',
}

function comparisonValue(row: PortfolioPeriod | undefined, metric: string) {
  if (!row) return '—'
  if (metric === 'customer_base') return `${count.format(row.opening_customers)} → ${count.format(row.closing_customers)}`
  if (metric === 'plan_base') return `${count.format(row.opening_plan_relations)} → ${count.format(row.closing_plan_relations)}`
  if (metric === 'customer_gross_rate') return row.opening_customers === 0 ? 'UNDEFINED · 0/0' : `${count.format(row.opening_customers_lost_any_time)}/${count.format(row.opening_customers)} · ${percent(row.opening_cohort_customer_churn_any_pct)}`
  if (metric === 'plan_gross_rate') return row.opening_plan_relations === 0 ? 'UNDEFINED · 0/0' : `${count.format(row.opening_relations_lost_any_time)}/${count.format(row.opening_plan_relations)} · ${percent(row.opening_cohort_churn_any_pct)}`
  if (metric === 'plan_close_rate') return row.opening_plan_relations === 0 ? 'UNDEFINED · 0/0' : `${count.format(row.opening_relations_lost_at_close)}/${count.format(row.opening_plan_relations)} · ${percent(row.opening_cohort_churn_at_close_pct)}`
  const value = row[metric as keyof PortfolioPeriod]
  return typeof value === 'number' ? count.format(value) : '—'
}

export function MonthlyChurnView({ periods, moments = [], movements = [], onOpenLab }: { periods: PortfolioPeriod[]; moments?: KeyMoment[]; movements?: Array<{ date: string; type: string; account_id: string; plan_tier?: string; from_plan?: string; to_plan?: string }>; onOpenLab?: (month: string) => void }) {
  const rows = periods.filter((row) => row.period_type === 'MONTHLY')
  const defaultMoment = moments.find((item) => item.type === 'RATE_PEAK') ?? moments[0]
  const [selectedMonth, setSelectedMonth] = useState(defaultMoment?.month ?? rows.at(-1)?.period ?? '')
  const [selectedMomentId, setSelectedMomentId] = useState(defaultMoment?.id ?? '')
  const selectedRow = rows.find((row) => row.period === selectedMonth)
  const selectedIndex = rows.findIndex((row) => row.period === selectedMonth)
  const previous = selectedIndex > 0 ? rows[selectedIndex - 1] : undefined
  const yearAgo = rows.find((row) => row.period === `${Number(selectedMonth.slice(0, 4)) - 1}${selectedMonth.slice(4)}`)
  const selectedMoment = moments.find((item) => item.id === selectedMomentId) ?? moments.find((item) => item.month === selectedMonth)
  const monthMovementAccounts = useMemo(() => {
    const grouped = new Map<string, { types: Set<string>; plans: Set<string> }>()
    for (const item of movements.filter((entry) => entry.date.startsWith(`${selectedMonth}-`) && /LOSS|CHURN|REACTIVATION|UPGRADE|DOWNGRADE|CONTRACTION/.test(entry.type))) {
      const row = grouped.get(item.account_id) ?? { types: new Set<string>(), plans: new Set<string>() }
      row.types.add(item.type)
      for (const plan of [item.plan_tier, item.from_plan, item.to_plan]) if (plan) row.plans.add(plan)
      grouped.set(item.account_id, row)
    }
    return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b)).slice(0, 12).map(([account_id, data]) => ({ account_id, types: [...data.types].sort(), plans: [...data.plans].sort() }))
  }, [movements, selectedMonth])
  const classification = 'CONDITIONAL_DATE_RECONSTRUCTION · PLAN-LEVEL PROXY'
  return <section className="monthly-churn-view" aria-labelledby="monthly-churn-heading" data-testid="monthly-churn-view">
    <div className="panel-head"><div><span className="panel-index">PRIMARY BUSINESS VIEW · 24 MONTHS</span><h3 id="monthly-churn-heading">Monthly customer and plan coverage churn</h3><p>January 2023–December 2024. Gross loss during the month and still lost at month close are separate measures. Every rate uses that unit’s opening cohort.</p></div><span className="evidence-pill alert">CONDITIONAL DATE RECONSTRUCTION</span></div>
    <div className="monthly-churn-definition"><b>Plan-level proxy</b><span>Unique account × plan-tier relations. A plan is not a verified product.</span><b>Customer coverage</b><span>Unique accounts that lose all date-reconstructed plan coverage.</span><b>Rate</b><span>Opening-cohort losses ÷ opening base × 100. Zero denominator = UNDEFINED.</span></div>

    <article className="chart-panel monthly-inspector" data-testid="monthly-inspector">
      <div className="month-inspector-heading"><div><span className="panel-index">MONTH SELECTOR · OBSERVED LEDGER</span><h4>Inspect a month and its comparison periods</h4><p>Monthly is the executive default. Every count and rate retains its own unit and denominator.</p></div><label>Selected month<select aria-label="Select monthly inspection period" value={selectedMonth} onChange={(event) => { setSelectedMonth(event.target.value); const match = moments.find((item) => item.month === event.target.value); setSelectedMomentId(match?.id ?? '') }}>{rows.map((row) => <option value={row.period} key={row.period}>{row.period}</option>)}</select></label></div>
      {selectedRow && <><div className="segment-table-wrap"><table className="month-comparison-table"><caption>Selected month compared with the previous month and same month one year earlier</caption><thead><tr><th scope="col">Measure</th><th scope="col">Selected · {selectedRow.period}</th><th scope="col">Previous · {previous?.period ?? 'not available'}</th><th scope="col">Year ago · {yearAgo?.period ?? 'not available'}</th></tr></thead><tbody>
        <tr><th scope="row">Customer base · opening → closing</th><td>{comparisonValue(selectedRow, 'customer_base')}</td><td>{comparisonValue(previous, 'customer_base')}</td><td>{comparisonValue(yearAgo, 'customer_base')}</td></tr>
        <tr><th scope="row">New customers</th><td>{comparisonValue(selectedRow, 'new_customers')}</td><td>{comparisonValue(previous, 'new_customers')}</td><td>{comparisonValue(yearAgo, 'new_customers')}</td></tr>
        <tr><th scope="row">Customer opening-cohort losses · any time / rate</th><td>{comparisonValue(selectedRow, 'customer_gross_rate')}</td><td>{comparisonValue(previous, 'customer_gross_rate')}</td><td>{comparisonValue(yearAgo, 'customer_gross_rate')}</td></tr>
        <tr><th scope="row">Customer reactivations / gross full-coverage loss events</th><td>{comparisonValue(selectedRow, 'customer_reactivations')} / {comparisonValue(selectedRow, 'gross_customer_churn_events')}</td><td>{previous ? `${comparisonValue(previous, 'customer_reactivations')} / ${comparisonValue(previous, 'gross_customer_churn_events')}` : '—'}</td><td>{yearAgo ? `${comparisonValue(yearAgo, 'customer_reactivations')} / ${comparisonValue(yearAgo, 'gross_customer_churn_events')}` : '—'}</td></tr>
        <tr><th scope="row">Plan-proxy base · opening → closing</th><td>{comparisonValue(selectedRow, 'plan_base')}</td><td>{comparisonValue(previous, 'plan_base')}</td><td>{comparisonValue(yearAgo, 'plan_base')}</td></tr>
        <tr><th scope="row">New plan relations / plan reactivations</th><td>{comparisonValue(selectedRow, 'new_plan_relationships')} / {comparisonValue(selectedRow, 'plan_reactivations')}</td><td>{previous ? `${comparisonValue(previous, 'new_plan_relationships')} / ${comparisonValue(previous, 'plan_reactivations')}` : '—'}</td><td>{yearAgo ? `${comparisonValue(yearAgo, 'new_plan_relationships')} / ${comparisonValue(yearAgo, 'plan_reactivations')}` : '—'}</td></tr>
        <tr><th scope="row">Gross plan loss events · all relation episodes</th><td>{comparisonValue(selectedRow, 'gross_plan_relation_loss_events')}</td><td>{comparisonValue(previous, 'gross_plan_relation_loss_events')}</td><td>{comparisonValue(yearAgo, 'gross_plan_relation_loss_events')}</td></tr>
        <tr><th scope="row">Opening plan cohort lost any time / rate</th><td>{comparisonValue(selectedRow, 'plan_gross_rate')}</td><td>{comparisonValue(previous, 'plan_gross_rate')}</td><td>{comparisonValue(yearAgo, 'plan_gross_rate')}</td></tr>
        <tr><th scope="row">Opening plan cohort still lost at close / rate</th><td>{comparisonValue(selectedRow, 'plan_close_rate')}</td><td>{comparisonValue(previous, 'plan_close_rate')}</td><td>{comparisonValue(yearAgo, 'plan_close_rate')}</td></tr>
        <tr><th scope="row">Portfolio contractions / possible downgrade candidates</th><td>{comparisonValue(selectedRow, 'portfolio_contraction_events')} / {comparisonValue(selectedRow, 'possible_downgrade_candidates')}</td><td>{previous ? `${comparisonValue(previous, 'portfolio_contraction_events')} / ${comparisonValue(previous, 'possible_downgrade_candidates')}` : '—'}</td><td>{yearAgo ? `${comparisonValue(yearAgo, 'portfolio_contraction_events')} / ${comparisonValue(yearAgo, 'possible_downgrade_candidates')}` : '—'}</td></tr>
      </tbody></table></div><div className="selected-month-accounts"><b>Selected-month account movements</b>{monthMovementAccounts.length ? <div>{monthMovementAccounts.map((item) => <span key={item.account_id}><strong>{item.account_id}</strong> · {item.types.join(', ')}{item.plans.length ? ` · ${item.plans.join(' / ')}` : ''}</span>)}</div> : <p>No customer or plan loss, return, contraction or candidate transition was recorded in this month.</p>}</div></>}
      <div className="monthly-inspector-footnote">A customer loss is complete loss of all plan-tier coverage; a plan-proxy loss can occur while the account remains active. Gross loss events may include relations acquired during the selected month. January 2023 zero-base rates remain UNDEFINED.</div>
    </article>

    <article className="chart-panel monthly-churn-panel">
      <div className="panel-head"><div><span className="panel-index">MONTHLY RATES · 24 PERIODS</span><h4>Gross loss versus persistent loss</h4><p>Solid lines show opening-cohort relations/customers that lost coverage at any point. Dashed lines show those still without coverage at month-end.</p></div></div>
      <div className="chart-legend monthly-churn-legend"><span><i className="legend-line plan-gross" /> Plan proxy · gross</span><span><i className="legend-line plan-close" /> Plan proxy · lost at close</span><span><i className="legend-line customer-gross" /> Customer · gross</span><span><i className="legend-line customer-close" /> Customer · lost at close</span></div>
      <div className="monthly-chart-scroll"><div className="monthly-chart-canvas">
        <figure className="monthly-chart-figure" data-testid="monthly-churn-rate-chart" data-month-points={rows.length} aria-label={`${rows.length} monthly plan-proxy and customer coverage loss rate points with gross and month-close series`}>
          <ResponsiveContainer width="100%" height={300}><ComposedChart data={rows} margin={{ top: 12, right: 20, left: 0, bottom: 34 }}>
            <CartesianGrid stroke="#d7d3c9" vertical={false} />
            <XAxis dataKey="period" interval={0} angle={-40} textAnchor="end" height={50} tick={{ fill: '#5e655e', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 'auto']} tickFormatter={(value) => `${Number(value).toFixed(1)}%`} tick={{ fill: '#5e655e', fontSize: 10 }} axisLine={false} tickLine={false} width={52} />
            <Tooltip content={<MonthlyRateTooltip />} filterNull={false} />
            <ReferenceArea x1={selectedMonth} x2={selectedMonth} fill="#b2945f" fillOpacity={0.12} strokeOpacity={0} />
            <Line type="linear" dataKey="opening_cohort_churn_any_pct" name="Plan proxy · gross loss" stroke="#a78345" strokeWidth={2} dot={{ r: 2.5 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} />
            <Line type="linear" dataKey="opening_cohort_churn_at_close_pct" name="Plan proxy · lost at close" stroke="#c3a56e" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 2 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} />
            <Line type="linear" dataKey="opening_cohort_customer_churn_any_pct" name="Customer · gross full-coverage loss" stroke="#4b7961" strokeWidth={2} dot={{ r: 2.5 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} />
            <Line type="linear" dataKey="opening_cohort_customer_churn_at_close_pct" name="Customer · lost at close" stroke="#8eaa97" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 2 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} />
          </ComposedChart></ResponsiveContainer>
        </figure>
      </div></div>
      <p className="small-note">For each month, hover or focus a point to see its numerator, denominator, formula and evidence status. January 2023 has a zero opening population; all four rates are UNDEFINED, not 0%.</p>
    </article>

    <article className="chart-panel monthly-churn-panel">
      <div className="panel-head"><div><span className="panel-index">MONTHLY MOVEMENTS · COUNTS</span><h4>Acquisitions, returns and coverage losses</h4><p>Counts remain separate by unit. Gross plan losses and opening-cohort relations still lost at close are distinct series.</p></div></div>
      <div className="chart-legend monthly-movement-legend"><span><i className="legend-square plan-loss" /> Plan gross losses</span><span><i className="legend-square persistent-loss" /> Plan still lost at close</span><span><i className="legend-square customer-loss" /> Customer full-coverage losses</span><span><i className="legend-square new-plan" /> New plan relations</span><span><i className="legend-square new-customer" /> New customers</span><span><i className="legend-square plan-return" /> Plan reactivations</span><span><i className="legend-square customer-return" /> Customer reactivations</span></div>
      <div className="monthly-chart-scroll"><div className="monthly-chart-canvas">
        <figure className="monthly-chart-figure" data-testid="monthly-churn-movement-chart" data-month-points={rows.length} aria-label={`${rows.length} monthly counts of plan losses, persistent closing losses, new relations, customers and reactivations`}>
          <ResponsiveContainer width="100%" height={300}><ComposedChart data={rows} margin={{ top: 12, right: 20, left: 0, bottom: 34 }}>
            <CartesianGrid stroke="#d7d3c9" vertical={false} />
            <XAxis dataKey="period" interval={0} angle={-40} textAnchor="end" height={50} tick={{ fill: '#5e655e', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fill: '#5e655e', fontSize: 10 }} axisLine={false} tickLine={false} width={42} />
            <Tooltip labelFormatter={(label) => `${label} · monthly movement counts`} formatter={(value, name) => [count.format(Number(value)), name]} />
            <ReferenceArea x1={selectedMonth} x2={selectedMonth} fill="#b2945f" fillOpacity={0.12} strokeOpacity={0} />
            <Bar dataKey="gross_plan_relation_loss_events" name="Plan-proxy gross loss events (relations)" fill="#a78345" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="opening_relations_lost_at_close" name="Opening plan relations still lost at close" fill="#d6bf91" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="gross_customer_churn_events" name="Customer full-coverage loss events" fill="#4b7961" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="new_plan_relationships" name="New plan relations" fill="#789181" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="new_customers" name="New customers" fill="#3f6852" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="plan_reactivations" name="Plan reactivations" fill="#90a9a0" maxBarSize={12} isAnimationActive={false} />
            <Bar dataKey="customer_reactivations" name="Customer reactivations" fill="#b6c9bf" maxBarSize={12} isAnimationActive={false} />
          </ComposedChart></ResponsiveContainer>
        </figure>
      </div></div>
      <p className="small-note">The rate chart’s customer lines count complete account coverage loss, while plan lines count account–plan proxy coverage loss. A single account can lose a plan and remain a customer.</p>
    </article>

    <section className="key-moments" aria-labelledby="key-moments-heading" data-testid="key-moments">
      <div className="panel-head"><div><span className="panel-index">DETERMINISTIC MONTHLY HIGHLIGHTS</span><h4 id="key-moments-heading">Key moments to investigate</h4><p>Rule-based selectors over the same ledger. Peaks are descriptive maxima, not tests of statistical significance.</p></div><span className="evidence-pill alert">{moments.length} MOMENTS</span></div>
      {moments.length === 0 ? <p role="status">Key-moment evidence is unavailable.</p> : <>
        <div className="key-moment-grid">{moments.map((moment) => <button type="button" key={moment.id} className={`key-moment-card${selectedMoment?.id === moment.id ? ' selected' : ''}`} aria-pressed={selectedMoment?.id === moment.id} onClick={() => { setSelectedMonth(moment.month); setSelectedMomentId(moment.id) }}>
          <span>{moment.month} · {moment.type.replaceAll('_', ' ')}</span><strong>{momentNames[moment.type]}</strong><small>{moment.metric === 'opening_cohort_churn_any_pct' ? `${moment.value.toFixed(2)}% · ${moment.numerator}/${moment.denominator}` : `${count.format(moment.value)} · ${moment.metric.replaceAll('_', ' ')}`}</small>
        </button>)}</div>
        {selectedMoment && <article className="key-moment-detail" data-testid="selected-key-moment"><div className="key-moment-detail-head"><div><span className="panel-index">{selectedMoment.month} · {selectedMoment.type}</span><h5>{momentNames[selectedMoment.type]}</h5></div><span className="evidence-pill alert">CONDITIONAL</span></div><p>{selectedMoment.executive_explanation}</p><dl><dt>Observed value</dt><dd>{selectedMoment.value}{selectedMoment.metric === 'opening_cohort_churn_any_pct' ? '%' : ''}{selectedMoment.numerator !== null && selectedMoment.denominator !== null ? ` · ${selectedMoment.numerator}/${selectedMoment.denominator}` : ''}</dd><dt>Reference</dt><dd>{Object.entries(selectedMoment.comparison).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${value ?? 'not available'}`).join(' · ')}</dd><dt>Detection criterion</dt><dd>{selectedMoment.criterion}</dd><dt>Evidence</dt><dd>{selectedMoment.evidence_classification}</dd></dl>
          {selectedMoment.segments.length > 0 && <div className="key-moment-linked"><b>Related segments</b><div>{selectedMoment.segments.map((item) => <span key={`${item.dimension}-${item.segment}`}>{item.dimension}: {item.segment} · {item.numerator ?? item.affected_accounts ?? 0}{item.denominator !== undefined && item.denominator !== null ? `/${item.denominator}` : ''}</span>)}</div></div>}
          <div className="key-moment-linked"><b>Related accounts</b><div>{selectedMoment.accounts.length ? selectedMoment.accounts.map((item) => <span key={item.account_id} title={`${item.dates.join(', ')} · ${item.movement_types.join(', ')} · ${item.plans.join(', ')}`}>{item.account_id} · {item.movement_types.join(', ')}</span>) : <span>No account-level movements matched this selection.</span>}</div>{selectedMoment.accounts_truncated && <small>Showing 20 of {selectedMoment.account_count} linked accounts.</small>}</div>
          <div className="key-moment-action"><b>Suggested investigation:</b> {selectedMoment.investigation_action}</div><button type="button" className="text-action" onClick={() => onOpenLab?.(selectedMoment.month)}>Open {selectedMoment.month} in the Monthly Business Lab →</button>
        </article>}
      </>}
    </section>

    <div className="segment-table-wrap monthly-results-table"><table data-testid="monthly-churn-table"><caption>All {rows.length} monthly results from the daily ledger · {classification}</caption><thead><tr><th scope="col">Month</th><th scope="col">Opening customers</th><th scope="col">Customer loss events</th><th scope="col">Opening customers lost at any time / rate</th><th scope="col">Opening customers still lost at close / rate</th><th scope="col">New customers</th><th scope="col">Customer reactivations</th><th scope="col">Closing customers</th><th scope="col">Opening plan relations</th><th scope="col">Plan loss events</th><th scope="col">Opening relations lost at any time / rate</th><th scope="col">Opening relations still lost at close / rate</th><th scope="col">New plan relations</th><th scope="col">Plan reactivations</th><th scope="col">Closing plan relations</th><th scope="col">Evidence</th></tr></thead><tbody>{rows.map((row) => <tr key={row.period}><th scope="row">{row.period}</th><td>{count.format(row.opening_customers)}</td><td>{count.format(row.gross_customer_churn_events)}</td><td><RateCell numerator={row.opening_customers_lost_any_time} denominator={row.opening_customers} value={row.opening_cohort_customer_churn_any_pct} title="Customer gross opening-cohort loss rate" /></td><td><RateCell numerator={row.opening_customers_lost_at_close} denominator={row.opening_customers} value={row.opening_cohort_customer_churn_at_close_pct} title="Customer closing loss rate" /></td><td>{count.format(row.new_customers)}</td><td>{count.format(row.customer_reactivations)}</td><td>{count.format(row.closing_customers)}</td><td>{count.format(row.opening_plan_relations)}</td><td>{count.format(row.gross_plan_relation_loss_events)}</td><td><RateCell numerator={row.opening_relations_lost_any_time} denominator={row.opening_plan_relations} value={row.opening_cohort_churn_any_pct} title="Plan-proxy gross opening-cohort loss rate" /></td><td><RateCell numerator={row.opening_relations_lost_at_close} denominator={row.opening_plan_relations} value={row.opening_cohort_churn_at_close_pct} title="Plan-proxy closing loss rate" /></td><td>{count.format(row.new_plan_relationships)}</td><td>{count.format(row.plan_reactivations)}</td><td>{count.format(row.closing_plan_relations)}</td><td>CONDITIONAL DATE RECONSTRUCTION</td></tr>)}</tbody></table></div>
    <p className="table-warning"><b>Interpretation:</b> all account × plan-tier values are a proxy, not verified product churn. Monthly rates are cohort losses ÷ opening base; do not sum daily rates or substitute annual events-per-100-account-months.</p>
  </section>
}
