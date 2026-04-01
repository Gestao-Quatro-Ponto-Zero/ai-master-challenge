import { Activity } from 'lucide-react'

interface Props {
  health: {
    score: number
    details: {
      volume: number
      quality: number
      win_rate: number
      avg_score: number
      low_risk: number
    }
  }
}

const DETAIL_LABELS: Record<string, string> = {
  volume: 'Volume de pipeline',
  quality: 'Qualidade (% alta prioridade)',
  win_rate: 'Taxa de conversão',
  avg_score: 'Score médio',
  low_risk: 'Baixo risco',
}

export function HealthScore({ health }: Props) {
  const { score, details } = health

  let color: string, label: string, bg: string
  if (score >= 70) {
    color = 'var(--success)'; label = 'Saudável'; bg = 'rgba(22,163,74,0.06)'
  } else if (score >= 50) {
    color = 'var(--g4-gold)'; label = 'Atenção'; bg = 'rgba(185,145,91,0.06)'
  } else {
    color = 'var(--danger)'; label = 'Crítico'; bg = 'rgba(220,38,38,0.06)'
  }

  return (
    <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]" style={{ borderLeftWidth: '3px', borderLeftColor: color }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} style={{ color }} strokeWidth={2} />
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Saúde do Pipeline</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold" style={{ color }}>{score}</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ color, background: bg }}>{label}</span>
        </div>
      </div>

      <div className="space-y-2">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-[var(--text-secondary)] w-40">{DETAIL_LABELS[key] || key}</span>
            <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-primary)] overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${value}%`,
                  background: value >= 70 ? 'var(--success)' : value >= 50 ? 'var(--g4-gold)' : 'var(--danger)',
                }}
              />
            </div>
            <span className="text-xs font-medium w-8 text-right" style={{
              color: value >= 70 ? 'var(--success)' : value >= 50 ? 'var(--g4-gold)' : 'var(--danger)',
            }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
