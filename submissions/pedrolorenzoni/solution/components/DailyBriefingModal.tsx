'use client'

import { Target, X } from 'lucide-react'
import { Deal } from '../lib/data'
import { computeDealSmell, computeKillerScore } from '../lib/scores'

interface DailyBriefingModalProps {
  deals: Deal[]
  agentName: string
  onClose: () => void
}

export default function DailyBriefingModal({ deals, agentName, onClose }: DailyBriefingModalProps) {
  const firstName = agentName.split(' ')[0]

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Foco do dia"
    >
      {/* Backdrop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.55)',
        }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Card */}
      <div
        style={{
          position: 'relative',
          zIndex: 61,
          maxWidth: '36rem',
          width: '90%',
          borderRadius: '1rem',
          background: '#0f1a45',
          border: '1px solid rgba(255,255,255,0.1)',
          padding: '2rem',
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
            <Target size={22} color="#b9915b" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <span
                style={{
                  fontSize: '1.125rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  display: 'block',
                  lineHeight: 1.3,
                  fontFamily: 'Manrope, sans-serif',
                }}
              >
                Foco de hoje, {firstName}
              </span>
              <span
                style={{
                  fontSize: '0.875rem',
                  color: 'rgba(255,255,255,0.6)',
                  display: 'block',
                  marginTop: '0.25rem',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                Seus 3 deals com maior potencial agora
              </span>
            </div>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            aria-label="Fechar modal"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'rgba(255,255,255,0.55)',
              padding: '4px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              marginLeft: '1rem',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.9)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.55)')}
          >
            <X size={18} />
          </button>
        </div>

        {/* Divider */}
        <div
          style={{
            height: '1px',
            background: 'rgba(255,255,255,0.08)',
            marginBottom: '1.25rem',
          }}
        />

        {/* Deal list */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {deals.map((deal, index) => {
            const ds = computeDealSmell(deal)
            const ks = computeKillerScore(deal)
            const isEngaging = deal.deal_stage === 'Engaging'

            return (
              <div key={deal.opportunity_id}>
                <div
                  style={{
                    padding: '1rem 0',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  {/* Stage badge + Account name row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        fontFamily: 'Inter, sans-serif',
                        letterSpacing: '0.04em',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: isEngaging
                          ? 'rgba(185,145,91,0.2)'
                          : 'rgba(255,255,255,0.1)',
                        color: isEngaging ? '#b9915b' : '#ffffff',
                        flexShrink: 0,
                      }}
                    >
                      {deal.deal_stage}
                    </span>
                    <span
                      style={{
                        fontSize: '15px',
                        fontWeight: 700,
                        color: '#ffffff',
                        fontFamily: 'Manrope, sans-serif',
                        lineHeight: 1.2,
                      }}
                    >
                      {deal.account}
                    </span>
                  </div>

                  {/* Product */}
                  <span
                    style={{
                      fontSize: '13px',
                      color: 'rgba(255,255,255,0.6)',
                      fontFamily: 'Inter, sans-serif',
                    }}
                  >
                    {deal.product}
                  </span>

                  {/* Scores row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <span
                        style={{
                          fontSize: '13px',
                          color: 'rgba(255,255,255,0.5)',
                          fontFamily: 'Inter, sans-serif',
                        }}
                      >
                        KS
                      </span>
                      <span
                        style={{
                          fontSize: '14px',
                          fontWeight: 700,
                          color: '#b9915b',
                          fontFamily: 'Manrope, sans-serif',
                        }}
                      >
                        {ks}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <span
                        style={{
                          fontSize: '13px',
                          color: 'rgba(255,255,255,0.5)',
                          fontFamily: 'Inter, sans-serif',
                        }}
                      >
                        Deal Smell
                      </span>
                      <span
                        style={{
                          fontSize: '14px',
                          fontWeight: 700,
                          color: '#b9915b',
                          fontFamily: 'Manrope, sans-serif',
                        }}
                      >
                        {ds}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Separator between deals (not after the last one) */}
                {index < deals.length - 1 && (
                  <div
                    style={{
                      height: '1px',
                      background: 'rgba(255,255,255,0.08)',
                    }}
                  />
                )}
              </div>
            )
          })}
        </div>

        {/* Divider before footer */}
        <div
          style={{
            height: '1px',
            background: 'rgba(255,255,255,0.08)',
            marginTop: '0.25rem',
            marginBottom: '1.25rem',
          }}
        />

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              background: '#b9915b',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 24px',
              fontSize: '14px',
              fontWeight: 700,
              fontFamily: 'Manrope, sans-serif',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = '#a57e4a')}
            onMouseLeave={(e) => (e.currentTarget.style.background = '#b9915b')}
          >
            Vamos vender! →
          </button>
        </div>
      </div>
    </div>
  )
}
