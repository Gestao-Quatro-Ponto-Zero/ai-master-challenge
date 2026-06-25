// components/analytics/AtRiskTable.jsx

function fmt(n) {
  if (!n) return '$0'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

function RatioBadge({ ratio }) {
  const color  = ratio >= 2.0 ? '#DC2626' : '#D97706'
  const bg     = ratio >= 2.0 ? '#FEF2F2' : '#FFFBEB'
  const border = ratio >= 2.0 ? '#FECACA' : '#FDE68A'
  const label  = ratio >= 2.0 ? '🔴 Crítico' : '🟡 Atenção'
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 8px',
      borderRadius: 100, border: `1px solid ${border}`,
      background: bg, color, whiteSpace: 'nowrap',
    }}>
      {label} {ratio.toFixed(1)}x
    </span>
  )
}

function RegionCards({ byRegion }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10, marginBottom: 16 }}>
      {byRegion.map(r => (
        <div key={r.regional_office} style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius)', padding: '12px 14px',
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
            📍 {r.regional_office}
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: r.critical_count > 0 ? '#DC2626' : '#D97706' }}>
            {r.total_at_risk}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
            {r.critical_count > 0 && <span style={{ color: '#DC2626' }}>{r.critical_count} críticos · </span>}
            {r.warning_count} atenção
          </div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent)', marginTop: 4 }}>
            {fmt(r.total_value_at_risk)}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function AtRiskTable({ data }) {
  if (!data) return null

  const { deals, by_region, total_at_risk, critical_count, warning_count, total_value } = data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        {[
          { label: 'Total em Risco',  value: total_at_risk,          color: '#D97706' },
          { label: 'Críticos (2x+)',  value: critical_count,         color: '#DC2626' },
          { label: 'Atenção (1.5x)', value: warning_count,          color: '#D97706' },
          { label: 'Valor em Risco', value: fmt(total_value),       color: 'var(--accent)' },
        ].map(k => (
          <div key={k.label} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: '12px 14px',
          }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              {k.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: k.color }}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Por região */}
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Por Região
      </div>
      <RegionCards byRegion={by_region} />

      {/* Tabela de deals */}
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Deals em Risco — ordenados por criticidade
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}>
              {['Conta', 'Vendedor', 'Produto', 'Stage', 'Dias', 'Acima da média', 'Valor', 'Risco'].map(h => (
                <th key={h} style={{
                  padding: '9px 14px', textAlign: 'left',
                  fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                  textTransform: 'uppercase', color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {deals.map((deal, i) => (
              <tr key={deal.opportunity_id} style={{
                borderBottom: '1px solid var(--border)',
                background: deal.risk_ratio >= 2.0 ? '#FFF8F8' : i % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)',
              }}>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 500 }}>{deal.account || '—'}</td>
                <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{deal.sales_agent || '—'}</td>
                <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{deal.product || '—'}</td>
                <td style={{ padding: '10px 14px' }}>
                  <span className={`stage-pill ${deal.deal_stage?.toLowerCase() === 'engaging' ? 'engaging' : 'prospecting'}`}>
                    {deal.deal_stage}
                  </span>
                </td>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 700, color: deal.risk_ratio >= 2.0 ? '#DC2626' : '#D97706' }}>
                  {deal.days_in_pipeline}d
                </td>
                <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-muted)' }}>
                  +{deal.days_above_avg}d
                </td>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600 }}>
                  {fmt(deal.close_value)}
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <RatioBadge ratio={deal.risk_ratio} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}