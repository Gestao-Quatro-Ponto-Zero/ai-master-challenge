// Componente legado — substituído por PriorityBadge no DealCard.jsx
// Mantido para referência histórica.

const R = 34
const CIRC = 2 * Math.PI * R

function tierColor(score) {
  if (score === null || score === undefined) return '#555870'
  if (score >= 7) return '#1D9E75'
  if (score >= 4) return '#F0A500'
  return '#E24B4A'
}

export function ScoreRing({ score, size = 84 }) {
  if (score === null || score === undefined) {
    return (
      <div style={{
        width: size, height: size, borderRadius: '50%',
        border: '3px dashed #BDBDBD',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        fontSize: 10, color: '#9E9E9E', gap: 2,
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 16 }}>?</span>
        <span>s/ score</span>
      </div>
    )
  }

  const color = tierColor(score)
  const offset = CIRC * (1 - score / 10)
  const vb = 84

  return (
    <svg width={size} height={size} viewBox={`0 0 ${vb} ${vb}`} style={{ flexShrink: 0 }}>
      <circle cx="42" cy="42" r={R} fill="none" stroke="#2A2D3E" strokeWidth="6" />
      <circle
        cx="42" cy="42" r={R} fill="none"
        stroke={color} strokeWidth="6"
        strokeDasharray={CIRC}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 42 42)"
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
      <text x="42" y="46" textAnchor="middle" fontSize="18" fontWeight="700" fill={color}>
        {score.toFixed(1)}
      </text>
    </svg>
  )
}
