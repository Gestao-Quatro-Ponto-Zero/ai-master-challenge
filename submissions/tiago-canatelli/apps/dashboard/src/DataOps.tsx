import { useEffect, useState } from 'react'
import { num, post } from './api'
import { useView } from './hooks'
import { Badge, Card, State } from './ui'

type Run = { run_id: string; started_at: string; finished_at: string | null; status: string; source: string; source_version: number | null; trigger: string }
type Step = { step_id: number; run_id: string; dataset: string; layer: string; rows_read: number | null; rows_loaded: number; rows_rejected: number; status: string; duration_ms: number | null; bytes: number | null }
type Dq = { run_id: string; check_name: string; table_name: string; severity: string; status: string; failing_rows: number; total_rows: number; details: string }
type Table = { schema_name: string; table_name: string; layer: string; description: string | null; row_count: number; column_count: number }
type Column = { schema_name: string; table_name: string; column_name: string; data_type: string; description: string | null; is_key: boolean; null_pct: number | null; distinct_count: number | null }

const tone = (s: string) => (s === 'success' || s === 'pass' ? 'green' : s === 'failed' || s === 'fail' ? 'red' : s === 'running' ? 'amber' : 'slate')
const LAYERS = ['raw', 'bronze', 'silver', 'dq', 'gold', 'catalog']

export default function DataOpsPage({ canIngest }: { canIngest: boolean }) {
  const [refresh, setRefresh] = useState(0)
  const runs = useView<Run>('ingestion_runs', {}, refresh)
  const sorted = [...(runs.data ?? [])].sort((a, b) => b.started_at.localeCompare(a.started_at))
  const live = sorted[0]?.status === 'running'
  const [force, setForce] = useState(true)
  const [msg, setMsg] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  // Atualiza a cada 3 s enquanto há uma ingestão rodando (progresso ao vivo); senão a cada 30 s.
  useEffect(() => {
    const id = window.setInterval(() => setRefresh((x) => x + 1), live || starting ? 3000 : 30000)
    return () => window.clearInterval(id)
  }, [live, starting])
  useEffect(() => { if (live) setStarting(false) }, [live])

  const startIngest = async () => {
    setMsg(null); setStarting(true)
    try {
      const r = await post<{ status: string; mode: string }>('/ingest', { force })
      setMsg(`Ingestão ${r.status} (${r.mode}). Acompanhe o progresso abaixo.`)
      setRunId(null)
      setRefresh((x) => x + 1)
    } catch (e) { setMsg((e as Error).message); setStarting(false) }
  }
  const [runId, setRunId] = useState<string | null>(null)
  const current = runId ?? sorted.find((r) => r.status !== 'skipped')?.run_id ?? sorted[0]?.run_id
  const steps = useView<Step>('ingestion_steps', current ? { run_id: current } : {}, refresh)
  const dq = useView<Dq>('dq_results', current ? { run_id: current } : {}, refresh)
  const tables = useView<Table>('catalog_tables')
  const cols = useView<Column>('catalog_columns')
  const [search, setSearch] = useState('')
  const [table, setTable] = useState<string | null>('silver.churn_events')

  const datasets = [...new Set((steps.data ?? []).map((s) => s.dataset))]
  const term = search.toLowerCase()
  const filteredTables = (tables.data ?? []).filter((t) => !term || `${t.schema_name}.${t.table_name} ${t.description ?? ''}`.toLowerCase().includes(term))
    .sort((a, b) => LAYERS.indexOf(a.layer) - LAYERS.indexOf(b.layer) || a.table_name.localeCompare(b.table_name))

  return (
    <div className="space-y-4">
      <Card title="Ingestão" subtitle="Kaggle MCP → raw (Storage) → bronze → silver → qualidade → gold → catálogo · agendada a cada 15 min (pg_cron do Supabase → API no Render)" source="api.ingestion_runs / api.ingestion_steps">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {sorted.slice(0, 8).map((r) => (
            <button key={r.run_id} onClick={() => setRunId(r.run_id)}
              className={`rounded-lg border px-2 py-1 text-xs ${current === r.run_id ? 'border-slate-900 dark:border-slate-100' : 'border-slate-200 dark:border-slate-700'}`}>
              {new Date(r.started_at).toLocaleString('pt-BR')} <Badge tone={tone(r.status)}>{r.status}</Badge> <span className="muted">{r.trigger === 'cron' ? '⏱ agendada' : 'manual'}</span>
            </button>
          ))}
          <span className="ml-auto flex items-center gap-2 text-xs">
            {live ? <Badge tone="amber">● ingestão em andamento — atualizando a cada 3 s</Badge> : <span className="muted">atualiza sozinho</span>}
            {canIngest && (
              <>
                <label className="muted flex items-center gap-1"><input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} /> reprocessar tudo</label>
                <button disabled={live || starting} onClick={startIngest} className="rounded-lg bg-slate-900 px-3 py-1 text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">
                  {live || starting ? 'Rodando…' : 'Executar ingestão agora'}
                </button>
              </>
            )}
          </span>
        </div>
        {msg && <p className="mb-2 text-sm">{msg}</p>}
        <State loading={steps.loading} error={steps.error} empty={steps.data?.length === 0} />
        <table className="w-full text-sm">
          <thead className="muted text-left text-xs"><tr><th>Dataset</th>{LAYERS.map((l) => <th key={l}>{l}</th>)}</tr></thead>
          <tbody>
            {datasets.map((d) => (
              <tr key={d} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1 font-medium">{d}</td>
                {LAYERS.map((l) => {
                  const s = (steps.data ?? []).find((x) => x.dataset === d && x.layer === l)
                  if (!s) return <td key={l} className="muted">—</td>
                  const progress = s.rows_read ? Math.round((100 * s.rows_loaded) / s.rows_read) : 100
                  return (
                    <td key={l} className="text-xs">
                      <Badge tone={tone(s.status)}>{s.status}</Badge>
                      {s.status === 'running' && <div className="mt-1 h-1.5 w-24 rounded bg-slate-200 dark:bg-slate-700"><div className="h-1.5 rounded bg-amber-500" style={{ width: `${progress}%` }} /></div>}
                      <div className="num muted">{s.rows_read ? `${num(s.rows_loaded)}/${num(s.rows_read)} (${progress}%)` : num(s.rows_loaded)}{s.rows_rejected ? ` · ${s.rows_rejected} rej.` : ''}</div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Qualidade de dados" subtitle="Checagens do run selecionado. error bloqueia o gold; warning e info viram achados." source="api.dq_results">
        <State loading={dq.loading} error={dq.error} />
        <table className="w-full text-sm">
          <thead className="muted text-left text-xs"><tr><th>Severidade</th><th>Checagem</th><th className="text-right">Falhas</th><th>O que significa</th></tr></thead>
          <tbody>
            {[...(dq.data ?? [])].sort((a, b) => ['error', 'warning', 'info'].indexOf(a.severity) - ['error', 'warning', 'info'].indexOf(b.severity)).map((c) => (
              <tr key={c.check_name} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1"><Badge tone={c.status === 'pass' ? 'green' : c.severity === 'error' ? 'red' : 'amber'}>{c.severity} · {c.status}</Badge></td>
                <td>{c.check_name}</td>
                <td className="num text-right">{num(c.failing_rows)} / {num(c.total_rows)}</td>
                <td className="muted text-xs">{c.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <Card title="Catálogo" subtitle={`${tables.data?.length ?? 0} tabelas e views`} source="api.catalog_tables">
          <input className="mb-2 w-full rounded-lg border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-700" placeholder="Buscar tabela ou descrição…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <ul className="max-h-[420px] space-y-1 overflow-auto text-sm">
            {filteredTables.map((t) => {
              const key = `${t.schema_name}.${t.table_name}`
              return (
                <li key={key}>
                  <button onClick={() => setTable(key)} className={`w-full rounded-lg px-2 py-1 text-left ${table === key ? 'bg-slate-100 dark:bg-slate-800' : ''}`}>
                    <Badge>{t.layer}</Badge> <span className="font-medium">{t.table_name}</span> <span className="num muted text-xs">{num(t.row_count)} linhas</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </Card>
        <Card title={table ?? 'Selecione uma tabela'} subtitle={(tables.data ?? []).find((t) => `${t.schema_name}.${t.table_name}` === table)?.description ?? ''} source="api.catalog_columns">
          <State loading={cols.loading} error={cols.error} />
          <table className="w-full text-sm">
            <thead className="muted text-left text-xs"><tr><th>Coluna</th><th>Tipo</th><th className="text-right">% nulos</th><th className="text-right">Distintos</th><th>Descrição</th></tr></thead>
            <tbody>
              {(cols.data ?? []).filter((c) => `${c.schema_name}.${c.table_name}` === table).map((c) => (
                <tr key={c.column_name} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="py-1 font-mono text-xs">{c.column_name}{c.is_key ? ' 🔑' : ''}</td>
                  <td className="muted text-xs">{c.data_type}</td>
                  <td className="num text-right">{c.null_pct ?? '—'}</td>
                  <td className="num text-right">{c.distinct_count ?? '—'}</td>
                  <td className="text-xs">{c.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
