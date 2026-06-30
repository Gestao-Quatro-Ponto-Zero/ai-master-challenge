// components/analytics/TeamRanking.jsx
// Tabela de ranking de vendedores com win rate, deals ativos e status.

function fmt(n) {
  if (!n) return '$0'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

function StatusBadge({ status }) {
  const cfg = {
    strong:          { label: '✅ Top performer', color: '#16A34A', bg: '#F0FDF4', border: '#BBF7D0' },
    average:         { label: '🟡 Na média',      color: '#D97706', bg: '#FFFBEB', border: '#FDE68A' },
    needs_coaching:  { label: '🔴 Coaching',      color: '#DC2626', bg: '#FEF2F2', border: '#FECACA' },
  }
  const c = cfg[status] || cfg.average
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: '2px 8px',
      borderRadius: 100, border: `1px solid ${c.border}`,
      background: c.bg, color: c.color, whiteSpace: 'nowrap',
    }}>
      {c.label}
    </span>
  )
}

function WinRateBar({ rate, globalRate }) {
  const pct = Math.round(rate * 100)
  const color = rate >= globalRate * 1.15 ? '#16A34A'
              : rate >= globalRate * 0.85 ? '#D97706'
              : '#DC2626'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 100, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 100, transition: 'width 0.5s' }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 32 }}>{pct}%</span>
    </div>
  )
}

export default function TeamRanking({ data }) {
  if (!data) return null

  const { agents, team_win_rate, global_win_rate, total_active, pipeline_value } = data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* KPIs do time */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        {[
          { label: 'Win Rate do Time', value: `${Math.round(team_win_rate * 100)}%`,
            note: `Global: ${Math.round(global_win_rate * 100)}%`,
            color: team_win_rate >= global_win_rate ? '#16A34A' : '#DC2626' },
          { label: 'Vendedores',    value: agents.length,         note: 'no time',        color: 'var(--accent)' },
          { label: 'Deals Ativos',  value: total_active,          note: 'Prospect+Engag', color: 'var(--accent)' },
          { label: 'Em Pipeline',   value: fmt(pipeline_value),   note: 'valor total',    color: 'var(--accent)' },
        ].map(k => (
          <div key={k.label} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: '12px 14px',
          }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              {k.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: k.color }}>{k.value}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{k.note}</div>
          </div>
        ))}
      </div>

      {/* Tabela de agentes */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}>
              {['#', 'Vendedor', 'Win Rate', 'Deals Ativos', '🔥 Hot', 'Pipeline', 'Fechados', 'Status'].map(h => (
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
            {agents.map((agent, i) => (
              <tr key={agent.sales_agent} style={{
                borderBottom: '1px solid var(--border)',
                background: i % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)',
              }}>
                <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>
                  {i + 1}
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: 'var(--accent)', color: '#fff',
                      fontSize: 11, fontWeight: 700,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      {agent.sales_agent.charAt(0)}
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{agent.sales_agent}</div>
                      {agent.regional_office && (
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{agent.regional_office}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td style={{ padding: '10px 14px', minWidth: 140 }}>
                  <WinRateBar rate={agent.win_rate} globalRate={global_win_rate} />
                </td>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600, textAlign: 'center' }}>
                  {agent.active_deals}
                </td>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600, color: '#DC2626', textAlign: 'center' }}>
                  {agent.hot_deals}
                </td>
                <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600 }}>
                  {fmt(agent.pipeline_value)}
                </td>
                <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>
                  {agent.won_deals}W / {agent.lost_deals}L
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <StatusBadge status={agent.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}