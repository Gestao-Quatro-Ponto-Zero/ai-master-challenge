import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { num, pct, usd } from './api'
import { useView } from './hooks'
import { Card, Kpi, PERSONA_LABEL, State } from './ui'

type Overview = Record<string, number | string>
type Hazard = { quarter: string; tenure_bucket: string; churn_per_100_account_months: number }
type Cohort = { signup_cohort: string; churn_3m_pct: number | null; churn_6m_pct: number | null }
type ChurnType = { churn_quarter: string; churn_type: string; churn_events: number }
type Persona = { persona: string; accounts: number; mrr: number; pct_mrr: number; avg_probability_90d: number; mrr_at_risk_90d: number; pct_mrr_at_risk: number; recommended_play: string }

const BUCKETS = ['0-3m', '3-6m', '6-12m', '12m+']
const COLORS = ['#e11d48', '#f59e0b', '#3b82f6', '#64748b']

export default function OverviewPage() {
  const ov = useView<Overview>('kpi_overview')
  const hz = useView<Hazard>('tenure_hazard')
  const co = useView<Cohort>('cohort')
  const ct = useView<ChurnType>('churn_type')
  const ps = useView<Persona>('persona_summary')
  const o = ov.data?.[0]

  const hazard = Object.values((hz.data ?? []).reduce<Record<string, Record<string, number | string>>>((acc, r) => {
    acc[r.quarter] ??= { quarter: r.quarter }
    acc[r.quarter][r.tenure_bucket] = r.churn_per_100_account_months
    return acc
  }, {})).sort((a, b) => String(a.quarter).localeCompare(String(b.quarter)))

  const types = Object.values((ct.data ?? []).reduce<Record<string, Record<string, number | string>>>((acc, r) => {
    acc[r.churn_quarter] ??= { q: r.churn_quarter }
    acc[r.churn_quarter][r.churn_type] = r.churn_events
    return acc
  }, {})).sort((a, b) => String(a.q).localeCompare(String(b.q)))

  const cohorts = [...(co.data ?? [])].filter((c) => c.churn_3m_pct !== null).sort((a, b) => a.signup_cohort.localeCompare(b.signup_cohort))

  return (
    <div className="space-y-6">
      <section className="card border-l-4 border-l-rose-500">
        <p className="text-xs font-semibold uppercase tracking-wide text-rose-600">Diagnóstico</p>
        <h2 className="mt-1 text-lg font-semibold">
          O churn subiu porque as contas novas estão falhando nos primeiros 90 dias — e os indicadores de CS e Produto não enxergam isso.
        </h2>
        {o && (
          <p className="muted mt-2 text-sm">
            Em 2024Q4, contas com até 3 meses churnaram a <b>{num(o.hazard_new_accounts, 1)}</b> por 100 contas-mês, contra{' '}
            <b>{num(o.hazard_tenured_accounts, 1)}</b> das com 12+ meses. Churn em 6 meses: {pct(o.churn_6m_cohort_2023q2)} (coorte 2023Q2) →{' '}
            {pct(o.churn_6m_cohort_2024q2)} (2024Q2). O CSAT é {num(o.csat_avg, 2)} para quem sai e para quem fica, e{' '}
            {pct(o.silent_churn_pct)} dos churns não abrem ticket antes.
          </p>
        )}
      </section>

      <State loading={ov.loading} error={ov.error} />
      {o && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Kpi label="Contas ativas" value={num(o.active_accounts)} hint={`dados até ${o.as_of_date}`} />
          <Kpi label="MRR vigente" value={usd(o.active_mrr)} />
          <Kpi label="MRR em risco (90 dias)" value={usd(o.mrr_at_risk_90d)} tone="bad" hint="probabilidade × MRR por conta" />
          <Kpi label="Churns no último trimestre" value={num(o.churn_events_last_quarter)} tone="bad" hint={`2023Q4: ${num(o.churn_events_2023q4)}`} />
          <Kpi label="CSAT médio" value={num(o.csat_avg, 2)} hint={`só notas 3–5 · ${pct(o.csat_response_pct)} respondem`} />
          <Kpi label="Churn silencioso" value={pct(o.silent_churn_pct)} tone="bad" hint="sem ticket nos 90 dias antes" />
          <Kpi label="MRR perdido em Enterprise" value={pct(o.enterprise_pct_mrr_lost)} hint="dos eventos de churn" />
          <Kpi label="Top 10% dos churns" value={pct(o.top10_pct_mrr_lost)} hint="do MRR perdido" />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Contas novas churnam até 5× mais" subtitle="Churns por 100 contas-mês, por trimestre e tempo de casa" source="api.tenure_hazard">
          <State loading={hz.loading} error={hz.error} />
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={hazard}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="quarter" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Legend />
              {BUCKETS.map((b, i) => <Line key={b} dataKey={b} name={b} stroke={COLORS[i]} strokeWidth={b === '0-3m' ? 3 : 1.5} dot={false} connectNulls />)}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Cada coorte nova churna mais cedo" subtitle="% da coorte com churn em 3 e 6 meses (só coortes com tempo de observação)" source="api.cohort">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={cohorts}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="signup_cohort" fontSize={11} />
              <YAxis fontSize={11} unit="%" />
              <Tooltip />
              <Legend />
              <Bar dataKey="churn_3m_pct" name="3 meses" fill="#f59e0b" />
              <Bar dataKey="churn_6m_pct" name="6 meses" fill="#e11d48" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Quem está saindo" subtitle="Eventos por trimestre: 1º churn nos primeiros 3 meses, 1º churn depois, ou churn repetido" source="api.churn_type">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={types}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="q" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Legend />
              <Bar dataKey="primeiro_0_3m" stackId="a" name="1º churn < 3m" fill="#e11d48" />
              <Bar dataKey="primeiro_3m_mais" stackId="a" name="1º churn ≥ 3m" fill="#3b82f6" />
              <Bar dataKey="repetido" stackId="a" name="repetido" fill="#94a3b8" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Onde está o MRR em risco" subtitle="Personas de cliente (contas ativas)" source="api.persona_summary">
          <State loading={ps.loading} error={ps.error} />
          <table className="w-full text-sm">
            <thead className="muted text-left text-xs"><tr><th>Persona</th><th className="text-right">Contas</th><th className="text-right">% MRR</th><th className="text-right">Prob. 90d</th><th className="text-right">MRR em risco</th></tr></thead>
            <tbody>
              {[...(ps.data ?? [])].sort((a, b) => b.mrr_at_risk_90d - a.mrr_at_risk_90d).map((p) => (
                <tr key={p.persona} className="border-t border-slate-100 dark:border-slate-800" title={p.recommended_play}>
                  <td className="py-1">{PERSONA_LABEL[p.persona] ?? p.persona}</td>
                  <td className="num text-right">{num(p.accounts)}</td>
                  <td className="num text-right">{pct(p.pct_mrr)}</td>
                  <td className="num text-right">{pct(p.avg_probability_90d * 100, 0)}</td>
                  <td className="num text-right font-medium">{usd(p.mrr_at_risk_90d)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
