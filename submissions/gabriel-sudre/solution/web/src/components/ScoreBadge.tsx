export function ScoreBadge({ score }: { score: number }) {
  let color: string, bg: string, label: string

  if (score >= 70) {
    color = 'var(--success)'
    bg = 'rgba(22,163,74,0.08)'
    label = 'Alto'
  } else if (score >= 40) {
    color = 'var(--g4-gold)'
    bg = 'rgba(185,145,91,0.10)'
    label = 'Médio'
  } else {
    color = 'var(--danger)'
    bg = 'rgba(220,38,38,0.08)'
    label = 'Baixo'
  }

  return (
    <div
      className="flex flex-col items-center justify-center px-3 py-2 rounded-lg"
      style={{ background: bg }}
    >
      <span className="text-xl font-bold" style={{ color }}>{score}</span>
      <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>{label}</span>
    </div>
  )
}
