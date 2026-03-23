import type { Manager } from '@/types'

type Props = {
  name?: string
  role?: string
  region?: string
  managers?: Manager[]
  isFilterOpen?: boolean
  onFilterToggle?: () => void
  onManagerChange?: (name: string) => void
}

export default function ProfileCard({
  name = 'Cameron Williamson',
  role = 'Manager',
  region = 'Central',
  managers = [],
  isFilterOpen = false,
  onFilterToggle,
  onManagerChange,
}: Props) {
  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: 'auto',
        paddingBottom: '0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        borderRadius: '20px 20px 0 0',
        background: '#fff',
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
      }}
    >
      {/* card__img */}
      <div style={{ position: 'relative', height: '192px', width: '100%', backgroundColor: '#061d34', borderRadius: '20px 20px 0 0' }}>
        <button
          className="transition-transform duration-200 ease-out hover:scale-110"
          onClick={onFilterToggle}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: isFilterOpen ? 'rgba(187,147,91,0.35)' : 'rgba(255,255,255,0.12)',
            border: 'none',
            borderRadius: '8px',
            padding: '7px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" y1="6" x2="20" y2="6" />
            <line x1="8" y1="12" x2="16" y2="12" />
            <line x1="11" y1="18" x2="13" y2="18" />
          </svg>
        </button>

        {/* Manager picker dropdown */}
        {isFilterOpen && managers.length > 0 && (
          <div
            style={{
              position: 'absolute',
              top: '3rem',
              right: '1rem',
              background: '#061d34',
              borderRadius: '12px',
              padding: '6px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
              zIndex: 10,
              minWidth: '180px',
            }}
          >
            {managers.map((m) => (
              <button
                key={m.manager}
                onClick={() => {
                  onManagerChange?.(m.manager)
                  onFilterToggle?.()
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  background: m.manager === name ? 'rgba(187,147,91,0.25)' : 'transparent',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  cursor: 'pointer',
                  color: m.manager === name ? '#bb935b' : 'rgba(255,255,255,0.75)',
                  fontSize: '0.82rem',
                  fontWeight: m.manager === name ? 600 : 400,
                }}
                onMouseEnter={(e) => {
                  if (m.manager !== name) {
                    (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.08)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (m.manager !== name) {
                    (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }
                }}
              >
                {m.manager}
                <span style={{ display: 'block', fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)', fontWeight: 400 }}>
                  {m.regional_office}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* card__avatar */}
      <div
        style={{
          position: 'absolute',
          width: '114px',
          height: '114px',
          background: '#bb935b',
          borderRadius: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          top: '135px',
          border: '4px solid #fff',
        }}
      >
        <span style={{ fontSize: '2.8rem', fontWeight: 700, color: '#fff', lineHeight: 1 }}>
          {name.charAt(0).toUpperCase()}
        </span>
      </div>

      {/* card__title */}
      <div style={{ marginTop: '60px', fontWeight: 500, fontSize: '18px', color: '#000' }}>
        {name}
      </div>

      {/* card__subtitle */}
      <div style={{ marginTop: '10px', fontWeight: 400, fontSize: '15px', color: '#78858F' }}>
        {role} · {region}
      </div>
    </div>
  )
}
