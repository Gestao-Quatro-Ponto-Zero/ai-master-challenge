type Props = {
  name?: string
  title?: string
  region?: string
  prospect?: number
  engaging?: number
  won?: number
  lost?: number
  onClick?: () => void
}

export default function SellerCard({
  name = 'Cameron Williamson',
  title = 'Seller',
  region = 'Central',
  prospect = 0,
  engaging = 0,
  won = 0,
  lost = 0,
  onClick,
}: Props) {
  return (
    <div
      onClick={onClick}
      className="transition-transform duration-200 ease-out hover:scale-[1.03]"
      style={{
        position: 'relative',
        width: '100%',
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(48px)',
        WebkitBackdropFilter: 'blur(48px)',
        borderRadius: '20px',
        padding: '2rem',
        boxShadow: '0 8px 32px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.08)',
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {/* Arrow top-right */}
      <div style={{
        position: 'absolute', top: '1rem', right: '1rem', zIndex: 2,
        background: 'rgba(255,255,255,0.12)',
        borderRadius: '8px',
        padding: '5px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="7" y1="17" x2="17" y2="7" /><polyline points="7 7 17 7 17 17" />
        </svg>
      </div>

      {/* Banner top */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '100%',
          height: '96px',
          backgroundColor: '#061d34',
          borderRadius: '20px 20px 0 0',
          zIndex: 0,
        }}
      />

      {/* Avatar */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          backgroundColor: '#bb935b',
          margin: '0 auto 1rem',
          border: '3px solid white',
          boxShadow: '0px 0px 6px rgba(0,0,0,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span style={{ fontSize: '2.2rem', fontWeight: 700, color: '#fff', lineHeight: 1 }}>
          {name.charAt(0).toUpperCase()}
        </span>
      </div>

      {/* Info */}
      <div style={{ textAlign: 'left', marginBottom: '1.5rem', position: 'relative', zIndex: 1 }}>
        <p style={{ fontSize: '1.5rem', fontWeight: 600, color: '#1a1a1a', marginBottom: '0.25rem' }}>
          {name}
        </p>
        <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>
          {title} · {region}
        </div>
      </div>

      {/* Stats */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '1rem',
          paddingTop: '1rem',
          borderTop: '1px solid #eee',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 600, color: '#1a1a1a' }}>{prospect}</div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Prospect</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 600, color: '#1a1a1a' }}>{engaging}</div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Engaging</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 600, color: '#1a1a1a' }}>{won}</div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Won</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 600, color: '#1a1a1a' }}>{lost}</div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Lost</div>
        </div>
      </div>
    </div>
  )
}
