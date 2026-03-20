'use client'

import { scoreLabel } from '@/types'

const styles = {
  hot:  'bg-red-100 text-red-700 border border-red-200',
  warm: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  cold: 'bg-blue-100 text-blue-600 border border-blue-200',
}

const labels = { hot: '🔥 Hot', warm: '☀️ Warm', cold: '❄️ Cold' }

export function ScoreBadge({ score }: { score: number }) {
  const label = scoreLabel(score)
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${styles[label]}`}>
      {labels[label]}
      <span className="font-bold">{score}</span>
    </span>
  )
}
