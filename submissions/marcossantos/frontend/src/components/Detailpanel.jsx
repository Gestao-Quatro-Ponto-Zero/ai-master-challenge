// components/DetailPanel.jsx
import { X } from 'lucide-react'

// ── helpers ───────────────────────────────────────────────────────────────────

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

// ── Score Hero ────────────────────────────────────────────────────────────────

function ScoreHero({ score, tier }) {
  const color = tierColor(tier)
  const label = tier === 'hot' ? 'Alta prioridade' : tier === 'warm' ? 'Prioridade média' : 'Baixa prioridade'
  return (
    <div className="score-hero">
      <span className="score-hero-number" style={{ color }}>{score}</span>
      <div className="score-hero-right">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TierBadge tier={tier} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</span>
        </div>
        <div className="score-hero-bar-wrap">
          <div
            className="score-hero-bar-fill"
            style={{ width: `${score}%`, background: color }}
          />
        </div>
        <span className="score-hero-label">{score} / 100 pontos</span>
      </div>
    </div>
  )
}

// ── Action Box ────────────────────────────────────────────────────────────────

function ActionBox({ action, urgency }) {
  return (
    <div className={`action-box ${urgency}`}>
      {action}
    </div>
  )
}

// ── Info Grid ─────────────────────────────────────────────────────────────────

function InfoGrid({ deal }) {
  const items = [
    { label: 'Stage',       value: <span className={`stage-pill ${deal.deal_stage?.toLowerCase() === 'engaging' ? 'engaging' : 'prospecting'}`}>{deal.deal_stage}</span> },
    { label: 'Valor',       value: fmtValue(deal.close_value) },
    { label: 'Dias no pipe',value: `${deal.days_in_pipeline}d` },
    { label: 'Produto',     value: deal.product || '—' },
    { label: 'Setor',       value: deal.sector || '—' },
    { label: 'Funcionários',value: deal.employees ? Number(deal.employees).toLocaleString('pt-BR') : '—' },
    { label: 'Receita',     value: deal.revenue ? fmtValue(deal.revenue) : '—' },
    { label: 'Região',      value: deal.regional_office || '—' },
  ]

  return (
    <div className="info-grid">
      {items.map(item => (
        <div key={item.label} className="info-item">
          <span className="info-item-label">{item.label}</span>
          <span className="info-item-value">{item.value}</span>
        </div>
      ))}
    </div>
  )
}

// ── Factor Item ───────────────────────────────────────────────────────────────

function FactorItem({ factor }) {
  const pct = Math.round((factor.points / factor.max_points) * 100)
  return (
    <div className={`factor-item ${factor.signal}`}>
      <div className="factor-top">
        <span className="factor-label">{factor.label}</span>
        <span className="factor-points">+{factor.points} / {factor.max_points}</span>
      </div>
      <div className="factor-bar-wrap">
        <div
          className={`factor-bar-fill ${factor.signal}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="factor-reason">{factor.reason}</span>
    </div>
  )
}

// ── Componente Principal ──────────────────────────────────────────────────────

export default function DetailPanel({ deal, onClose }) {
  if (!deal) return null

  return (
    <>
      <div className="detail-overlay" onClick={onClose} />

      <div className="detail-panel">
        {/* Header */}
        <div className="detail-header">
          <div className="detail-header-left">
            <span className="detail-account-name">{deal.account}</span>
            <div className="detail-meta">
              {deal.manager && (
                <span className="detail-agent">Manager: {deal.manager}</span>
              )}
              {deal.sales_agent && (
                <span className="detail-agent">· {deal.sales_agent}</span>
              )}
            </div>
          </div>
          <button className="detail-close" onClick={onClose} title="Fechar">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="detail-body">
          {/* Score */}
          <ScoreHero score={deal.score} tier={deal.tier} />

          {/* Ação */}
          <ActionBox action={deal.action} urgency={deal.action_urgency} />

          {/* Info da conta */}
          <InfoGrid deal={deal} />

          {/* Breakdown de fatores */}
          <div className="factors-section">
            <span className="factors-title">Por que esse score?</span>
            {(deal.factors || []).map((f, i) => (
              <FactorItem key={i} factor={f} />
            ))}
          </div>
        </div>
      </div>
    </>
  )
}