// components/analytics/FunnelCharts.jsx
// Gráficos de funil: distribuição por stage e win rate por produto.
// SVG puro — sem biblioteca externa.

function HorizontalBar({ label, value, max, color, suffix = '', secondLabel = '' }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
      <div style={{ width: 110, fontSize: 12, color: 'var(--text-secondary)', textAlign: 'right', flexShrink: 0 }}>
        {label}
      </div>
      <div style={{ flex: 1, height: 24, background: 'var(--bg)', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: color, borderRadius: 4,
          transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
          display: 'flex', alignItems: 'center', paddingLeft: 8,
        }}>
          {pct > 20 && (
            <span style={{ fontSize: 11, fontWeight: 600, color: '#fff' }}>
              {value}{suffix}
            </span>
          )}
        </div>
        {pct <= 20 && (
          <span style={{ position: 'absolute', left: `${pct}%`, top: '50%', transform: 'translateY(-50%)', marginLeft: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-primary)' }}>
            {value}{suffix}
          </span>
        )}
      </div>
      {secondLabel && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 50, textAlign: 'right' }}>
          {secondLabel}
        </div>
      )}
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
      {children}
    </div>
  )
}

function Card({ children, title }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 20 }}>
      {title && <SectionTitle>{title}</SectionTitle>}
      {children}
    </div>
  )
}

function StageDonut({ byStage, total }) {
  // Mini donut SVG
  const size   = 100
  const radius = 38
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * radius

  const colors  = ['#1B6FDE', '#7C3AED']
  let offset = 0

  const slices = byStage.map((s, i) => {
    const pct   = total > 0 ? s.count / total : 0
    const dash  = pct * circumference
    const gap   = circumference - dash
    const slice = { ...s, pct, dash, gap, offset, color: colors[i] }
    offset += dash
    return slice
  })

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <svg width={size} height={size} style={{ flexShrink: 0 }}>
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="var(--border)" strokeWidth={14} />
        {slices.map((s, i) => (
          <circle
            key={i}
            cx={cx} cy={cy} r={radius}
            fill="none"
            stroke={s.color}
            strokeWidth={14}
            strokeDasharray={`${s.dash} ${s.gap}`}
            strokeDashoffset={-s.offset + circumference * 0.25}
            strokeLinecap="butt"
          />
        ))}
        <text x={cx} y={cy - 4} textAnchor="middle" fontSize={16} fontWeight={800} fill="var(--text-primary)">{total}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fontSize={9} fill="var(--text-muted)">ativos</text>
      </svg>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: s.color, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 12, fontWeight: 600 }}>{s.stage}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.count} deals · {s.pct}%</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function FunnelCharts({ data }) {
  if (!data) return null

  const { by_stage, by_product, total_active } = data
  const maxWR    = Math.max(...by_product.map(p => p.win_rate), 0.01)
  const maxCount = Math.max(...by_product.map(p => p.won + p.lost + p.active), 1)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Stage donut + barras */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        <Card title="Distribuição por Stage">
          <StageDonut byStage={by_stage} total={total_active} />
        </Card>

        <Card title="Deals por Stage">
          {by_stage.map(s => (
            <HorizontalBar
              key={s.stage}
              label={s.stage}
              value={s.count}
              max={total_active}
              color={s.stage === 'Engaging' ? '#1B6FDE' : '#7C3AED'}
              secondLabel={`${s.pct}%`}
            />
          ))}

          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
              Taxa Engaging / Total
            </div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#1B6FDE' }}>
              {total_active > 0
                ? `${Math.round((by_stage.find(s => s.stage === 'Engaging')?.count || 0) / total_active * 100)}%`
                : '—'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              deals avançados de Prospecting
            </div>
          </div>
        </Card>
      </div>

      {/* Win Rate por Produto */}
      <Card title="Win Rate por Produto">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

          {/* Barras de win rate */}
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>Taxa de conversão</div>
            {by_product.map(p => {
              const wr = Math.round(p.win_rate * 100)
              const color = wr >= 55 ? '#16A34A' : wr >= 35 ? '#D97706' : '#DC2626'
              return (
                <HorizontalBar
                  key={p.product}
                  label={p.product}
                  value={`${wr}%`}
                  max={100}
                  color={color}
                  secondLabel={p.avg_days_to_close ? `${p.avg_days_to_close}d` : ''}
                />
              )
            })}
          </div>

          {/* Volume de deals */}
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>Volume total de deals</div>
            {by_product.map(p => {
              const total = p.won + p.lost + p.active
              return (
                <div key={p.product} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{p.product}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {p.won}W · {p.lost}L · {p.active} ativos
                    </span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg)', borderRadius: 4, display: 'flex', overflow: 'hidden' }}>
                    <div style={{ width: `${(p.won / total) * 100}%`, background: '#16A34A' }} />
                    <div style={{ width: `${(p.active / total) * 100}%`, background: '#1B6FDE' }} />
                    <div style={{ width: `${(p.lost / total) * 100}%`, background: '#E2E8F0' }} />
                  </div>
                </div>
              )
            })}
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              {[['#16A34A', 'Won'], ['#1B6FDE', 'Ativo'], ['#E2E8F0', 'Lost']].map(([c, l]) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--text-muted)' }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
                  {l}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}