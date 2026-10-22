import { useEffect, useMemo, useState, type FormEvent } from 'react'
import type { MonthlyLabScenario, MonthlyLabScenarioInput, PortfolioPeriod } from '../../contracts'
import { runMonthlyLabScenario } from '../../lib/api'

type Mode = 'OBSERVED' | 'SCENARIO'
const count = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })
const money = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })

function fromObserved(row: PortfolioPeriod): MonthlyLabScenarioInput {
  return {
    month: row.period,
    plans: row.plan_segments.map((plan) => ({
      plan_tier: plan.plan_tier,
      opening_relations: plan.opening_relations,
      new_relations: plan.new_relations,
      loss_events: plan.gross_loss_events,
      reactivations: plan.reactivations,
      opening_cohort_loss_any: plan.opening_relations_lost_any_time,
      opening_cohort_loss_at_close: plan.opening_relations_lost_at_close,
      assumed_monthly_value: 0,
    })),
    opening_customers: row.opening_customers,
    new_customers: row.new_customers,
    customer_loss_events: row.gross_customer_churn_events,
    customer_reactivations: row.customer_reactivations,
    opening_customer_loss_any: row.opening_customers_lost_any_time,
    opening_customer_loss_at_close: row.opening_customers_lost_at_close,
    portfolio_expansions: row.portfolio_expansion_events,
    portfolio_contractions: row.portfolio_contraction_events,
    possible_upgrades: row.possible_upgrade_candidates,
    possible_downgrades: row.possible_downgrade_candidates,
    assumed_customer_monthly_value: 0,
    assumed_acquisition_cost_per_customer: 0,
    assumed_retention_cost_per_account: 0,
    assumed_uptake_pct: 0.5,
    assumed_incremental_retention_lift_pct: 0.05,
    horizon_months: 6,
  }
}

function NumberField({ label, value, onChange, min = 0, max = 100000, step = 1, hint, disabled = false }: {
  label: string; value: number; onChange: (value: number) => void; min?: number; max?: number; step?: number; hint?: string; disabled?: boolean
}) {
  return <label className="monthly-lab-field"><span>{label}</span><input aria-label={label} type="number" min={min} max={max} step={step} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value === '' ? 0 : Number(event.target.value))} /><small>{hint}</small></label>
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className="monthly-lab-stat"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>
}

export function MonthlyBusinessLab({ rows, initialMonth }: { rows: PortfolioPeriod[]; initialMonth?: string }) {
  const selectable = useMemo(() => rows.filter((row) => row.period_type === 'MONTHLY'), [rows])
  const [month, setMonth] = useState(initialMonth ?? selectable.at(-1)?.period ?? '')
  const observed = selectable.find((row) => row.period === month)
  const [draft, setDraft] = useState<MonthlyLabScenarioInput | null>(observed ? fromObserved(observed) : null)
  const [mode, setMode] = useState<Mode>('OBSERVED')
  const [result, setResult] = useState<MonthlyLabScenario | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (initialMonth && selectable.some((row) => row.period === initialMonth)) setMonth(initialMonth)
  }, [initialMonth, selectable])

  useEffect(() => {
    if (!observed) return
    setDraft(fromObserved(observed))
    setResult(null)
    setError(null)
    setMode('OBSERVED')
  }, [month, rows])

  if (!selectable.length || !observed || !draft) return <section className="monthly-lab" aria-labelledby="monthly-lab-heading"><h3 id="monthly-lab-heading">Monthly Business Laboratory</h3><p role="status">No observed monthly baseline is available.</p></section>

  const setTop = (key: keyof MonthlyLabScenarioInput, value: number) => setDraft((old) => old ? { ...old, [key]: value } : old)
  const setPlan = (tier: string, key: keyof MonthlyLabScenarioInput['plans'][number], value: number) => setDraft((old) => old ? { ...old, plans: old.plans.map((plan) => plan.plan_tier === tier ? { ...plan, [key]: value } : plan) } : old)
  const reset = () => { setDraft(fromObserved(observed)); setResult(null); setError(null); setMode('OBSERVED') }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft) return
    setPending(true); setError(null)
    try { const next = await runMonthlyLabScenario({ ...draft, month }); setResult(next); setMode('SCENARIO') }
    catch (issue) { setError((issue as Error).message); setMode('SCENARIO') }
    finally { setPending(false) }
  }
  function exportResult() {
    if (!result) return
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `ravenstack-${month}-scenario.json`; link.click(); URL.revokeObjectURL(url)
  }
  const openingPlanLoss = observed.opening_relations_lost_any_time
  const openingPlanCloseLoss = observed.opening_relations_lost_at_close
  const openingCustomerLoss = observed.opening_customers_lost_any_time
  const openingCustomerCloseLoss = observed.opening_customers_lost_at_close

  return <section className="monthly-lab" aria-labelledby="monthly-lab-heading" data-testid="monthly-business-lab">
    <div className="monthly-lab-heading"><div><span className="panel-index">MONTHLY BUSINESS LABORATORY</span><h3 id="monthly-lab-heading">Change a decision assumption. Keep history intact.</h3><p>Start from one real month in the date-reconstructed ledger. Scenario values are submitted to the API; they never rewrite observed data.</p></div><label className="monthly-lab-month">Observed month<select aria-label="Select observed month" value={month} onChange={(event) => setMonth(event.target.value)}>{selectable.map((row) => <option key={row.period} value={row.period}>{row.period}</option>)}</select></label></div>
    <div className="monthly-lab-mode" role="tablist" aria-label="Laboratory mode"><button type="button" role="tab" aria-selected={mode === 'OBSERVED'} className={mode === 'OBSERVED' ? 'selected' : ''} onClick={() => setMode('OBSERVED')}>OBSERVED MODE <small>immutable source baseline</small></button><button type="button" role="tab" aria-selected={mode === 'SCENARIO'} className={mode === 'SCENARIO' ? 'selected' : ''} onClick={() => setMode('SCENARIO')}>SCENARIO MODE <small>hypothetical inputs and outputs</small></button></div>

    {mode === 'OBSERVED' ? <div className="monthly-lab-observed" data-testid="observed-mode">
      <div className="monthly-lab-evidence">CONDITIONAL DATE RECONSTRUCTION · ACCOUNT × PLAN-TIER PROXY</div>
      <div className="monthly-lab-stats"><Stat label="Opening customers" value={count.format(observed.opening_customers)} /><Stat label="Customer losses · any time / close" value={`${count.format(openingCustomerLoss)} / ${count.format(openingCustomerCloseLoss)}`} note="Unique accounts losing all plan-tier coverage" /><Stat label="New customers" value={count.format(observed.new_customers)} /><Stat label="Customer returns" value={count.format(observed.customer_reactivations)} /><Stat label="Closing customers" value={count.format(observed.closing_customers)} /><Stat label="Plan relations · opening → close" value={`${count.format(observed.opening_plan_relations)} → ${count.format(observed.closing_plan_relations)}`} /><Stat label="Plan losses · gross / still lost at close" value={`${count.format(openingPlanLoss)} / ${count.format(openingPlanCloseLoss)}`} note="Gross loss and persistent opening-cohort loss are distinct" /><Stat label="Acquired / reactivated plan relations" value={`${count.format(observed.new_plan_relationships)} / ${count.format(observed.plan_reactivations)}`} /></div>
      <div className="monthly-lab-caveat">Plan-tier is a proxy, not verified product identity. The month-level balances are reconstructed from subscription dates. Recorded recurring revenue and causal intervention effects are not identified.</div>
    </div> : <div className="monthly-lab-scenario" data-testid="scenario-mode">
      <form onSubmit={submit} className="monthly-lab-form">
        <div className="monthly-lab-observed-strip"><b>Observed baseline · {month}</b><span>{observed.opening_customers} customers → {observed.closing_customers}; {observed.opening_plan_relations} plan relations → {observed.closing_plan_relations}</span><button type="button" onClick={reset}>Reset to observed month</button></div>
        <div className="monthly-lab-form-section"><h4>Customer movements</h4><div className="monthly-lab-input-grid">
          <NumberField label="Opening customers · fixed" value={draft.opening_customers} onChange={(v) => setTop('opening_customers', v)} max={100000} disabled />
          <NumberField label="New customers" value={draft.new_customers} onChange={(v) => setTop('new_customers', v)} />
          <NumberField label="Complete customer loss events" value={draft.customer_loss_events} onChange={(v) => setTop('customer_loss_events', v)} />
          <NumberField label="Customer reactivations" value={draft.customer_reactivations} onChange={(v) => setTop('customer_reactivations', v)} />
          <NumberField label="Opening customers lost at any time" value={draft.opening_customer_loss_any} onChange={(v) => setTop('opening_customer_loss_any', v)} />
          <NumberField label="Opening customers still lost at close" value={draft.opening_customer_loss_at_close} onChange={(v) => setTop('opening_customer_loss_at_close', v)} />
        </div></div>
        <div className="monthly-lab-form-section"><h4>Plan-level proxy movements and assumed values</h4><div className="monthly-lab-plan-list">{draft.plans.map((plan) => <fieldset key={plan.plan_tier}><legend>{plan.plan_tier} · observed opening {plan.opening_relations}</legend><div className="monthly-lab-input-grid">
          <NumberField label={`${plan.plan_tier} opening relations · fixed`} value={plan.opening_relations} onChange={(v) => setPlan(plan.plan_tier, 'opening_relations', v)} disabled />
          <NumberField label={`${plan.plan_tier} new relations`} value={plan.new_relations} onChange={(v) => setPlan(plan.plan_tier, 'new_relations', v)} />
          <NumberField label={`${plan.plan_tier} loss events`} value={plan.loss_events} onChange={(v) => setPlan(plan.plan_tier, 'loss_events', v)} />
          <NumberField label={`${plan.plan_tier} reactivations`} value={plan.reactivations} onChange={(v) => setPlan(plan.plan_tier, 'reactivations', v)} />
          <NumberField label={`${plan.plan_tier} opening cohort lost any time`} value={plan.opening_cohort_loss_any} onChange={(v) => setPlan(plan.plan_tier, 'opening_cohort_loss_any', v)} />
          <NumberField label={`${plan.plan_tier} opening cohort still lost at close`} value={plan.opening_cohort_loss_at_close} onChange={(v) => setPlan(plan.plan_tier, 'opening_cohort_loss_at_close', v)} />
          <NumberField label={`${plan.plan_tier} assumed monthly value`} value={plan.assumed_monthly_value} onChange={(v) => setPlan(plan.plan_tier, 'assumed_monthly_value', v)} hint="user-defined units / relation / month" />
        </div></fieldset>)}</div></div>
        <div className="monthly-lab-form-section"><h4>Portfolio moves and financial assumptions</h4><div className="monthly-lab-input-grid">
          <NumberField label="Portfolio expansions" value={draft.portfolio_expansions} onChange={(v) => setTop('portfolio_expansions', v)} />
          <NumberField label="Portfolio contractions" value={draft.portfolio_contractions} onChange={(v) => setTop('portfolio_contractions', v)} />
          <NumberField label="Possible upgrades · separate annotation" value={draft.possible_upgrades} onChange={(v) => setTop('possible_upgrades', v)} />
          <NumberField label="Possible downgrades · separate annotation" value={draft.possible_downgrades} onChange={(v) => setTop('possible_downgrades', v)} />
          <NumberField label="Assumed monthly value per customer" value={draft.assumed_customer_monthly_value} onChange={(v) => setTop('assumed_customer_monthly_value', v)} hint="user-defined units" />
          <NumberField label="Assumed acquisition cost / customer" value={draft.assumed_acquisition_cost_per_customer} onChange={(v) => setTop('assumed_acquisition_cost_per_customer', v)} hint="user-defined units" />
          <NumberField label="Assumed retention cost / contacted account" value={draft.assumed_retention_cost_per_account} onChange={(v) => setTop('assumed_retention_cost_per_account', v)} hint="user-defined units" />
          <NumberField label="Assumed outreach uptake" value={draft.assumed_uptake_pct * 100} onChange={(v) => setTop('assumed_uptake_pct', v / 100)} max={100} step={1} hint="percent of customers with opening-cohort loss" />
          <NumberField label="Assumed incremental retention lift" value={draft.assumed_incremental_retention_lift_pct * 100} onChange={(v) => setTop('assumed_incremental_retention_lift_pct', v / 100)} max={100} step={1} hint="percentage points; hypothetical" />
          <NumberField label="Evaluation horizon" value={draft.horizon_months} onChange={(v) => setTop('horizon_months', v)} min={1} max={36} hint="months" />
        </div><p className="monthly-lab-caveat">Upgrade/downgrade counts are informational candidates; they are not added again to plan losses or acquisitions. Values are assumptions, not recorded MRR or ARR.</p></div>
        <div className="monthly-lab-actions"><button type="submit" disabled={pending}>{pending ? 'Calculating…' : 'Calculate scenario'}</button><button type="button" className="secondary" onClick={reset}>Reset</button></div>
        {error && <p role="alert" className="monthly-lab-error">Scenario was not accepted: {error}</p>}
      </form>
      {result && <section className="monthly-lab-result" aria-live="polite" data-testid="scenario-results"><div className="monthly-lab-evidence">SCENARIO ONLY · HYPOTHETICAL USER ASSUMPTIONS</div><div className="monthly-lab-stats"><Stat label="Scenario closing customers" value={count.format(result.scenario.closing_customers)} note={`Δ ${count.format(result.comparison.customer_closing_base_delta)} · ${result.comparison.customer_closing_base_delta_pct === null ? 'UNDEFINED' : `${result.comparison.customer_closing_base_delta_pct}%`} vs observed`} /><Stat label="Scenario closing plan relations" value={count.format(result.scenario.closing_plan_relations)} note={`Δ ${count.format(result.comparison.plan_closing_base_delta)} · ${result.comparison.plan_closing_base_delta_pct === null ? 'UNDEFINED' : `${result.comparison.plan_closing_base_delta_pct}%`} vs observed`} /><Stat label="Customer gross / persistent cohort loss" value={`${result.scenario.customer_cohort_gross_loss_rate_pct === null ? 'UNDEFINED' : `${result.scenario.customer_cohort_gross_loss_rate_pct}%`} / ${result.scenario.customer_cohort_closing_loss_rate_pct === null ? 'UNDEFINED' : `${result.scenario.customer_cohort_closing_loss_rate_pct}%`}`} /><Stat label="Plan-proxy gross / persistent cohort loss" value={`${result.scenario.plan_cohort_gross_loss_rate_pct === null ? 'UNDEFINED' : `${result.scenario.plan_cohort_gross_loss_rate_pct}%`} / ${result.scenario.plan_cohort_closing_loss_rate_pct === null ? 'UNDEFINED' : `${result.scenario.plan_cohort_closing_loss_rate_pct}%`}`} /><Stat label="Modeled monthly opening → closing run-rate" value={result.scenario.monthly_modeled_opening_run_rate === null ? 'UNSET' : `${money.format(result.scenario.monthly_modeled_opening_run_rate)} → ${money.format(result.scenario.monthly_modeled_closing_run_rate)}`} note="Assumed units only; incomparable to recorded revenue" /><Stat label="Modeled gross loss value · monthly" value={result.scenario.monthly_modeled_gross_loss_value === null ? 'UNSET' : money.format(result.scenario.monthly_modeled_gross_loss_value)} note="Plan loss events × user-assumed tier value" /><Stat label="Modeled acquisition value · horizon" value={result.scenario.monthly_modeled_acquisition_value === null ? 'UNSET' : money.format(result.scenario.monthly_modeled_acquisition_value * draft.horizon_months)} note="New plan relations × user-assumed tier value × horizon" /><Stat label="Modeled protected value · base case" value={result.scenario.modeled_protected_customer_value === null ? 'UNSET' : money.format(result.scenario.modeled_protected_customer_value)} note="Not causal benefit or observed revenue" /><Stat label="Modeled protected plan value · base case" value={result.scenario.modeled_protected_plan_value_over_horizon === null ? 'UNSET' : money.format(result.scenario.modeled_protected_plan_value_over_horizon)} note="Assumed plan values × hypothetical avoided losses" /><Stat label="Modeled net contribution · base case" value={result.scenario.modeled_net_contribution === null ? 'UNSET' : money.format(result.scenario.modeled_net_contribution)} note="Benefit/cost arithmetic under inputs; not accounting profit" /></div><p className="monthly-lab-caveat">Customer value protected = opening customers with a date-reconstructed loss × assumed uptake × assumed incremental lift × assumed monthly value × horizon. Plan value is modeled separately from customer value to avoid double counting. Net contribution = modeled protected customer value + modeled acquired customer value − assumed acquisition and retention costs.</p><div className="segment-table-wrap"><table><caption>Scenario sensitivity · assumptions scaled at 0.5× / 1.0× / 1.5×</caption><thead><tr><th>Case</th><th>Uptake</th><th>Incremental lift</th><th>Retained customers (equivalent)</th><th>Protected customer value</th><th>Protected plan value</th><th>Retention cost</th><th>Acquisition cost</th><th>Net contribution</th><th>Break-even monthly value / retained customer</th></tr></thead><tbody>{(['conservative', 'base', 'optimistic'] as const).map((key) => { const row = result.scenario.scenario_cases[key]; return <tr key={key}><th>{key}</th><td>{row.assumed_uptake_pct}%</td><td>{row.assumed_incremental_lift_pct_points} pp</td><td>{row.incremental_customers_retained_equivalent}</td><td>{row.modeled_protected_customer_value === null ? 'Not modeled' : money.format(row.modeled_protected_customer_value)}</td><td>{row.modeled_protected_plan_value_over_horizon === null ? 'Not modeled' : money.format(row.modeled_protected_plan_value_over_horizon)}</td><td>{money.format(row.modeled_retention_cost)}</td><td>{money.format(row.modeled_acquisition_cost)}</td><td>{row.modeled_net_contribution === null ? 'Not modeled' : money.format(row.modeled_net_contribution)}</td><td>{row.break_even_monthly_value_per_retained_customer === null ? 'UNDEFINED' : money.format(row.break_even_monthly_value_per_retained_customer)}</td></tr> })}</tbody></table></div><ul className="monthly-lab-caveat-list">{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul><button type="button" className="monthly-lab-export" onClick={exportResult}>Export scenario JSON</button></section>}
    </div>}
  </section>
}
