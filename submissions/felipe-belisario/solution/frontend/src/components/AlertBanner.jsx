const STYLES = {
  critical: { bg: '#2E0D0D', border: '#E24B4A', icon: '🔴', text: '#E24B4A' },
  warning:  { bg: '#2E2200', border: '#F0A500', icon: '⚠️', text: '#F0A500' },
  info:     { bg: '#0F1F3D', border: '#4F8EF7', icon: 'ℹ️', text: '#4F8EF7' },
  success:  { bg: '#0D2E22', border: '#1D9E75', icon: '✅', text: '#1D9E75' },
}

export function AlertBanner({ level = 'warning', message, onDismiss, children }) {
  const s = STYLES[level] ?? STYLES.warning
  return (
    <div style={{
      background: s.bg,
      border: `1px solid ${s.border}`,
      borderRadius: 8,
      padding: '12px 16px',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12,
    }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flex: 1 }}>
        <span style={{ fontSize: 16, flexShrink: 0 }}>{s.icon}</span>
        <div style={{ color: s.text, fontSize: 13, lineHeight: 1.5 }}>
          {message}
          {children}
        </div>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} style={{
          background: 'none', border: 'none', color: s.text,
          fontSize: 18, lineHeight: 1, padding: 0, flexShrink: 0,
          opacity: 0.6,
        }}>×</button>
      )}
    </div>
  )
}
