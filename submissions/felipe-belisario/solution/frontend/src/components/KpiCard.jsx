export function KpiCard({ label, value, sub, color, trend }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: '0.5px solid var(--border)',
      padding: '16px 20px',
      minWidth: 148,
      flex: '1 1 148px',
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: color ?? 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 5 }}>{sub}</div>
      )}
      {trend !== undefined && (
        <div style={{ fontSize: 12, color: trend >= 0 ? '#1D9E75' : '#E24B4A', marginTop: 5 }}>
          {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
        </div>
      )}
    </div>
  )
}
