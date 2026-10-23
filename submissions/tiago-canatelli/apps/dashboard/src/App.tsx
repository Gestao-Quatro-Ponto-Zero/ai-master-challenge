import { useEffect, useState } from 'react'
import { me, post, setToken, type User } from './api'
import AssistantPage from './Assistant'
import DataOpsPage from './DataOps'
import OverviewPage from './Overview'
import RiskPage from './Risk'

const TABS = [
  { id: 'geral', label: 'Visão geral' },
  { id: 'risco', label: 'Contas em risco' },
  { id: 'dados', label: 'Ingestão e catálogo' },
  { id: 'ia', label: 'Assistente de IA' },
] as const
type Tab = (typeof TABS)[number]['id']

function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const r = await post<{ token: string; user: User }>('/auth/login', { email, code })
      setToken(r.token); onLogin(r.user)
    } catch (err) { setError((err as Error).message) } finally { setBusy(false) }
  }
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-3">
        <div>
          <h1 className="text-lg font-semibold">RavenStack · Diagnóstico de churn</h1>
          <p className="muted text-sm">Entre com seu e-mail e código pessoal. Cada área vê a visão geral e as visões da sua função.</p>
        </div>
        <input className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm dark:border-slate-700" placeholder="e-mail" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm dark:border-slate-700" placeholder="código" type="password" autoComplete="current-password" value={code} onChange={(e) => setCode(e.target.value)} />
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button disabled={busy || !email || !code} className="w-full rounded-lg bg-slate-900 py-2 text-sm text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">{busy ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const [tab, setTab] = useState<Tab>(() => {
    const h = window.location.hash.slice(1)
    return (TABS.some((t) => t.id === h) ? h : 'geral') as Tab
  })
  const [question, setQuestion] = useState<string | null>(null)

  useEffect(() => { me().then((u) => { setUser(u); setChecking(false) }) }, [])

  if (checking) return <div className="muted p-8 text-sm">Carregando…</div>
  if (!user) return <Login onLogin={setUser} />

  const tabs = TABS.filter((t) => user.tabs.includes(t.id))
  const current: Tab = user.tabs.includes(tab) ? tab : 'geral'
  const go = (t: Tab) => { setTab(t); window.location.hash = t }
  const logout = () => { setToken(null); setUser(null) }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">RavenStack · Diagnóstico de churn</h1>
          <p className="muted text-sm">Lake no Supabase (raw → bronze → silver → gold) · dados sintéticos do Kaggle (River @ Rivalytics, MIT)</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <nav className="flex flex-wrap gap-1 rounded-xl bg-slate-200/60 p-1 dark:bg-slate-800">
            {tabs.map((t) => (
              <button key={t.id} onClick={() => go(t.id)}
                className={`rounded-lg px-3 py-1.5 text-sm ${current === t.id ? 'bg-white shadow-sm dark:bg-slate-950' : 'muted'}`}>
                {t.label}
              </button>
            ))}
          </nav>
          <div className="text-right text-xs">
            <div className="font-medium">{user.name}</div>
            <div className="muted">{user.label} · <button className="underline" onClick={logout}>sair</button></div>
          </div>
        </div>
      </header>
      {current === 'geral' && <OverviewPage />}
      {current === 'risco' && <RiskPage onAsk={(q) => { setQuestion(q); go('ia') }} />}
      {current === 'dados' && <DataOpsPage canIngest={user.can_edit} />}
      {current === 'ia' && <AssistantPage initialQuestion={question} user={user} />}
    </div>
  )
}
