// components/DealsTable.jsx
import { ChevronRight } from 'lucide-react'

// ── helpers ──────────────────────────────────────────────────────────────────

function fmtValue(v) {
  if (!v || v === 0) return '—'
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}k`
  return `$${v}`
}

function tierColor(tier) {
  return tier === 'hot' ? '#DC2626' : tier === 'warm' ? '#D97706' : '#94A3B8'
}

function TierBadge({ tier }) {
  const labels = { hot: '🔥 Hot', warm: '🌡 Warm', cold: '❄ Cold' }
  return <span className={`tier-badge ${tier}`}>{labels[tier] || tier}</span>
}

function StagePill({ stage }) {
  const cls = stage?.toLowerCase() === 'engaging' ? 'engaging' : 'prospecting'
  return <span className={`stage-pill ${cls}`}>{stage}</span>
}

function ScoreCell({ score, tier }) {
  return (
    <div className="score-cell">
      <span className="score-number" style={{ color: tierColor(tier) }}>{score}</span>
      <div className="score-bar-wrap">
        <div
          className="score-bar-fill"
          style={{ width: `${score}%`, background: tierColor(tier) }}
        />
      </div>
    </div>
  )
}

function UrgencyDot({ urgency }) {
  return <span className={`urgency-dot ${urgency}`} />
}

// ── componente principal ──────────────────────────────────────────────────────

export default function DealsTable({ deals, loading, error, selectedId, onSelect }) {
  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner" />
        <p>Carregando pipeline e calculando scores…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="state-container">
        <p style={{ color: '#DC2626' }}>⚠ Não foi possível conectar à API.</p>
        <p style={{ fontSize: 11 }}>Certifique-se que o backend está rodando em <code>localhost:8000</code></p>
      </div>
    )
  }

  if (!deals || deals.length === 0) {
    return (
      <div className="state-container">
        <p>Nenhum deal encontrado para os filtros selecionados.</p>
      </div>
    )
  }

  return (
    <table className="deals-table">
      <thead>
        <tr>
          <th style={{ width: 120 }}>Score</th>
          <th style={{ width: 70 }}>Tier</th>
          <th>Conta</th>
          <th style={{ width: 100 }}>Stage</th>
          <th>Vendedor</th>
          <th>Ação recomendada</th>
          <th style={{ width: 90 }}>Valor</th>
          <th style={{ width: 36 }}></th>
        </tr>
      </thead>
      <tbody>
        {deals.map(deal => (
          <tr
            key={deal.opportunity_id}
            className={selectedId === deal.opportunity_id ? 'selected' : ''}
            onClick={() => onSelect(deal)}
          >
            {/* Score */}
            <td><ScoreCell score={deal.score} tier={deal.tier} /></td>

            {/* Tier */}
            <td><TierBadge tier={deal.tier} /></td>

            {/* Conta */}
            <td>
              <div className="account-cell">
                <span className="account-name">{deal.account || '—'}</span>
                {deal.sector && (
                  <span className="account-sub">{deal.sector}</span>
                )}
              </div>
            </td>

            {/* Stage */}
            <td><StagePill stage={deal.deal_stage} /></td>

            {/* Vendedor */}
            <td>
              <div className="account-cell">
                <span className="account-name" style={{ fontSize: 12 }}>{deal.sales_agent || '—'}</span>
                {deal.regional_office && (
                  <span className="account-sub">{deal.regional_office}</span>
                )}
              </div>
            </td>

            {/* Ação */}
            <td>
              <div className="action-cell">
                <UrgencyDot urgency={deal.action_urgency} />
                {deal.action}
              </div>
            </td>

            {/* Valor */}
            <td>
              <span className="value-cell">{fmtValue(deal.close_value)}</span>
            </td>

            {/* Chevron */}
            <td>
              <ChevronRight size={14} className="row-chevron" />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}