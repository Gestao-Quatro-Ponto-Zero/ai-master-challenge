import { useState } from 'react'
import { num, pct, usd } from './api'
import { useView } from './hooks'
import { Badge, Card, PERSONA_LABEL, State } from './ui'

type Risk = {
  account_id: string; account_name: string; industry: string; current_plan: string; current_billing: string
  persona: string; mrr: number; probability_90d: number; mrr_at_risk_90d: number
  driver_1: string | null; driver_2: string | null; driver_3: string | null; suggested_action: string
  tenure_months: number; churn_count: number
}
type A360 = Record<string, string | number | boolean | null>

function Account({ id, onAsk }: { id: string; onAsk: (q: string) => void }) {
  const a = useView<A360>('account_360', { account_id: id })
  const r = a.data?.[0]
  return (
    <Card title={`Conta ${id}`} subtitle="Visão 360" source="api.account_360">
      <State loading={a.loading} error={a.error} />
      {r && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          {[
            ['Nome', r.account_name], ['Indústria', r.industry], ['País', r.country], ['Canal', r.referral_source],
            ['Plano / cobrança', `${r.current_plan} · ${r.current_billing}`], ['MRR', usd(r.current_mrr)],
            ['Tempo de casa', `${num(r.tenure_months, 1)} meses`], ['Churns anteriores', r.churn_count],
            ['Persona', PERSONA_LABEL[String(r.persona)] ?? r.persona], ['Prob. churn 90d', pct(Number(r.probability_90d) * 100, 0)],
            ['Tickets (90d / total)', `${r.tickets_90d} / ${r.tickets_total}`], ['CSAT médio', r.csat_avg ?? '—'],
            ['Uso (90d)', num(r.usage_90d)], ['Último motivo de churn', r.last_churn_reason ?? '—'],
          ].map(([k, v]) => (
            <div key={String(k)} className="contents"><dt className="muted">{k}</dt><dd className="num">{String(v)}</dd></div>
          ))}
        </dl>
      )}
      {r && (
        <div className="mt-3 space-y-2 text-sm">
          <p><b>Por que está em risco:</b> {[r.driver_1, r.driver_2, r.driver_3].filter(Boolean).join(' · ') || '—'}</p>
          <p><b>Jogada recomendada:</b> {r.suggested_action}</p>
          <button className="rounded-lg bg-slate-900 px-3 py-1.5 text-white dark:bg-slate-100 dark:text-slate-900"
            onClick={() => onAsk(`Explique o risco da conta ${id}: estado, persona, drivers, MRR em risco e próxima ação.`)}>
            Perguntar à IA sobre esta conta
          </button>
        </div>
      )}
    </Card>
  )
}

export default function RiskPage({ onAsk }: { onAsk: (q: string) => void }) {
  const q = useView<Risk>('risk_queue', { limit: '500' })
  const [persona, setPersona] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const rows = [...(q.data ?? [])].filter((r) => !persona || r.persona === persona).sort((a, b) => b.mrr_at_risk_90d - a.mrr_at_risk_90d)
  const total = rows.reduce((s, r) => s + r.mrr_at_risk_90d, 0)

  const exportCsv = () => {
    const head = ['account_id', 'account_name', 'persona', 'mrr', 'probability_90d', 'mrr_at_risk_90d', 'driver_1', 'driver_2', 'suggested_action']
    const csv = [head.join(','), ...rows.map((r) => head.map((h) => JSON.stringify((r as unknown as Record<string, unknown>)[h] ?? '')).join(','))].join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    Object.assign(document.createElement('a'), { href: url, download: 'fila_de_risco.csv' }).click()
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
      <Card title="Fila do CS — quem ligar primeiro" subtitle={`${rows.length} contas · ${usd(total)} de MRR em risco em 90 dias`} source="api.risk_queue">
        <div className="mb-3 flex flex-wrap gap-2">
          <select className="rounded-lg border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-700" value={persona} onChange={(e) => setPersona(e.target.value)}>
            <option value="">Todas as personas</option>
            {Object.entries(PERSONA_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <button className="rounded-lg border border-slate-300 px-3 py-1 text-sm dark:border-slate-700" onClick={exportCsv}>Exportar CSV</button>
        </div>
        <State loading={q.loading} error={q.error} empty={q.data?.length === 0} />
        <div className="max-h-[560px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="muted sticky top-0 bg-white text-left text-xs dark:bg-slate-900">
              <tr><th>Conta</th><th>Persona</th><th className="text-right">MRR</th><th className="text-right">Prob.</th><th className="text-right">Em risco</th><th>Principal motivo</th></tr>
            </thead>
            <tbody>
              {rows.slice(0, 200).map((r) => (
                <tr key={r.account_id} onClick={() => setSelected(r.account_id)}
                  className={`cursor-pointer border-t border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800 ${selected === r.account_id ? 'bg-slate-100 dark:bg-slate-800' : ''}`}>
                  <td className="py-1"><div className="font-medium">{r.account_name}</div><div className="muted text-xs">{r.account_id} · {r.current_plan} {r.current_billing}</div></td>
                  <td><Badge tone={r.persona === 'recem_chegado' || r.persona === 'em_retracao' ? 'red' : 'slate'}>{PERSONA_LABEL[r.persona] ?? r.persona}</Badge></td>
                  <td className="num text-right">{usd(r.mrr)}</td>
                  <td className="num text-right">{pct(r.probability_90d * 100, 0)}</td>
                  <td className="num text-right font-medium">{usd(r.mrr_at_risk_90d)}</td>
                  <td className="text-xs">{r.driver_1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <div>{selected ? <Account id={selected} onAsk={onAsk} /> : <Card title="Selecione uma conta"><p className="muted text-sm">Clique numa linha para ver a visão 360 e a jogada recomendada.</p></Card>}</div>
    </div>
  )
}
