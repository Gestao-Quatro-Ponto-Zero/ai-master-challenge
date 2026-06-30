// src/components/AlertsPanel.jsx
// Painel lateral de alertas — abre ao clicar no sino do header.

import { X, BellOff, RefreshCw } from 'lucide-react'

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime()
  const mins  = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days  = Math.floor(diff / 86_400_000)
  if (mins < 2)   return 'agora mesmo'
  if (mins < 60)  return `${mins}min atrás`
  if (hours < 24) return `${hours}h atrás`
  return `${days}d atrás`
}

function severityConfig(severity) {
  if (severity === 'critical') return { color: '#DC2626', bg: '#FEF2F2', border: '#FECACA', label: 'Crítico', dot: '🔴' }
  if (severity === 'warning')  return { color: '#D97706', bg: '#FFFBEB', border: '#FDE68A', label: 'Atenção', dot: '🟡' }
  return                               { color: '#475569', bg: '#F8FAFC', border: '#E2E8F0', label: 'Info',    dot: '🔵' }
}

function AlertItem({ alert, onDismiss }) {
  const cfg = severityConfig(alert.severity)

  return (
    <div style={{
      border: `1px solid ${cfg.border}`,
      borderLeft: `3px solid ${cfg.color}`,
      borderRadius: 'var(--radius)',
      padding: '10px 12px',
      background: cfg.bg,
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
    }}>
      {/* Header do alerta */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: cfg.color }}>
            {cfg.dot} {alert.title}
          </span>
          {alert.sales_agent && (
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              {alert.sales_agent} · {alert.regional_office || ''}
            </span>
          )}
        </div>
        <button
          onClick={() => onDismiss(alert.id)}
          title="Marcar como visto"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', padding: 2, flexShrink: 0,
            display: 'flex', borderRadius: 4,
          }}
        >
          <X size={13} />
        </button>
      </div>

      {/* Mensagem */}
      <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
        {alert.message}
      </p>

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          {timeAgo(alert.created_at)}
        </span>
        {alert.days_in_pipeline && (
          <span style={{
            fontSize: 10, fontWeight: 600,
            color: cfg.color,
            background: '#fff',
            border: `1px solid ${cfg.border}`,
            borderRadius: 100,
            padding: '1px 7px',
          }}>
            {alert.days_in_pipeline}d no pipeline
          </span>
        )}
      </div>
    </div>
  )
}

export default function AlertsPanel({ alertsData, onDismiss, onDismissAll, onRefresh, onClose }) {
  const alerts = alertsData?.alerts || []
  const unseen = alertsData?.unseen || 0

  const critical = alerts.filter(a => a.severity === 'critical')
  const warning  = alerts.filter(a => a.severity === 'warning')
  const info     = alerts.filter(a => a.severity === 'info')

  return (
    <>
      <div className="detail-overlay" onClick={onClose} />

      <div className="detail-panel" style={{ width: 380 }}>
        {/* Header */}
        <div className="detail-header">
          <div className="detail-header-left">
            <span className="detail-account-name">🔔 Alertas</span>
            <div className="detail-meta">
              <span className="detail-agent">
                {unseen > 0 ? `${unseen} não vistos` : 'Tudo em dia'}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {unseen > 0 && (
              <button
                onClick={onDismissAll}
                title="Marcar todos como vistos"
                style={{
                  background: 'var(--bg)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)', padding: '4px 10px',
                  fontSize: 11, color: 'var(--text-secondary)',
                  cursor: 'pointer', fontFamily: 'var(--font)',
                }}
              >
                Limpar todos
              </button>
            )}
            <button className="detail-close" onClick={onRefresh} title="Atualizar">
              <RefreshCw size={14} />
            </button>
            <button className="detail-close" onClick={onClose}>
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="detail-body">
          {alerts.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '40px 0', color: 'var(--text-muted)' }}>
              <BellOff size={32} strokeWidth={1.5} />
              <p style={{ fontSize: 13 }}>Nenhum alerta ativo no momento.</p>
            </div>
          ) : (
            <>
              {critical.length > 0 && (
                <div className="factors-section">
                  <span className="factors-title" style={{ color: '#DC2626' }}>
                    🔴 Críticos — {critical.length}
                  </span>
                  {critical.map(a => <AlertItem key={a.id} alert={a} onDismiss={onDismiss} />)}
                </div>
              )}

              {warning.length > 0 && (
                <div className="factors-section">
                  <span className="factors-title" style={{ color: '#D97706' }}>
                    🟡 Atenção — {warning.length}
                  </span>
                  {warning.map(a => <AlertItem key={a.id} alert={a} onDismiss={onDismiss} />)}
                </div>
              )}

              {info.length > 0 && (
                <div className="factors-section">
                  <span className="factors-title">
                    🔵 Informativo — {info.length}
                  </span>
                  {info.map(a => <AlertItem key={a.id} alert={a} onDismiss={onDismiss} />)}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}