import type { ReactNode } from 'react'

export function Card({ title, subtitle, source, children, className = '' }: {
  title?: string; subtitle?: string; source?: string; children: ReactNode; className?: string
}) {
  return (
    <section className={`card ${className}`}>
      {title && <h3 className="text-sm font-semibold">{title}</h3>}
      {subtitle && <p className="muted mb-3 text-xs">{subtitle}</p>}
      {children}
      {source && <p className="muted mt-2 text-[11px]" title="View de origem no Supabase">fonte: {source}</p>}
    </section>
  )
}

export function Kpi({ label, value, hint, tone = 'neutral' }: {
  label: string; value: string; hint?: string; tone?: 'neutral' | 'bad' | 'good'
}) {
  const color = tone === 'bad' ? 'text-rose-600 dark:text-rose-400' : tone === 'good' ? 'text-emerald-600' : ''
  return (
    <div className="card">
      <p className="muted text-xs">{label}</p>
      <p className={`num mt-1 text-2xl font-semibold ${color}`}>{value}</p>
      {hint && <p className="muted mt-1 text-xs">{hint}</p>}
    </div>
  )
}

export function State({ loading, error, empty }: { loading?: boolean; error?: string | null; empty?: boolean }) {
  if (loading) return <div className="h-24 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
  if (error) return <p className="text-sm text-rose-600">Não foi possível carregar: {error}. Verifique se a API está no ar.</p>
  if (empty) return <p className="muted text-sm">Nenhum dado ainda — rode <code>ravenlake ingest</code>.</p>
  return null
}

export function Badge({ children, tone = 'slate' }: { children: ReactNode; tone?: 'slate' | 'red' | 'amber' | 'green' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
    red: 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
    amber: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  }
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${tones[tone]}`}>{children}</span>
}

export const PERSONA_LABEL: Record<string, string> = {
  reincidente: 'Reincidente', em_retracao: 'Em retração', recem_chegado: 'Recém-chegado',
  em_expansao: 'Em expansão', ancora_enterprise: 'Âncora Enterprise',
  grande_sem_compromisso: 'Grande sem compromisso', pro_anual: 'Pro anual', pequeno_basic: 'Pequeno (Basic)',
}
