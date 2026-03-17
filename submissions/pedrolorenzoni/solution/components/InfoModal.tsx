'use client'

import { X, Target, AlertTriangle, Zap, BookOpen } from 'lucide-react'

interface InfoModalProps {
  onClose: () => void
}

export default function InfoModal({ onClose }: InfoModalProps) {
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
      aria-label="Informações sobre a plataforma"
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
          maxWidth: '32rem',
          width: '90%',
          borderRadius: '1rem',
          background: '#0f1a45',
          border: '1px solid rgba(255,255,255,0.1)',
          padding: '2rem',
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        {/* Card header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: '1.5rem',
          }}
        >
          <div>
            <span
              style={{
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#b9915b',
                display: 'block',
                lineHeight: 1.3,
              }}
            >
              G4 CRM
            </span>
            <span
              style={{
                fontSize: '0.875rem',
                color: '#ffffff',
                display: 'block',
                marginTop: '0.25rem',
              }}
            >
              Como funciona a plataforma
            </span>
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
            marginBottom: '1.5rem',
          }}
        />

        {/* Sections */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Section 1 — Objetivo da plataforma */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.5rem',
              }}
            >
              <Target size={16} color="#b9915b" style={{ flexShrink: 0 }} />
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                O que é esta plataforma?
              </span>
            </div>
            <p
              style={{
                fontSize: '0.8125rem',
                color: 'rgba(255,255,255,0.75)',
                lineHeight: 1.6,
                margin: 0,
                paddingLeft: '1.5rem',
              }}
            >
              O G4 CRM é o seu painel de controle de vendas. Aqui você acompanha seus deals ativos, entende quais estão em risco e sabe onde focar sua energia para bater a meta.
            </p>
          </div>

          {/* Divider */}
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

          {/* Section 2 — Deal Smell */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.5rem',
              }}
            >
              <AlertTriangle size={16} color="#ef4444" style={{ flexShrink: 0 }} />
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Deal Smell
              </span>
            </div>
            <p
              style={{
                fontSize: '0.8125rem',
                color: 'rgba(255,255,255,0.75)',
                lineHeight: 1.6,
                margin: 0,
                paddingLeft: '1.5rem',
              }}
            >
              É o sinal de alerta de um deal. Quanto maior o Deal Smell, mais sinais negativos esse negócio tem: atrasos no ciclo, falta de engajamento do cliente, etapas paradas há muito tempo. Um Deal Smell alto significa que o deal precisa de atenção agora — ou pode morrer.
            </p>
          </div>

          {/* Divider */}
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

          {/* Section 3 — Killer Score */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.5rem',
              }}
            >
              <Zap size={16} color="#b9915b" style={{ flexShrink: 0 }} />
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Killer Score (KS)
              </span>
            </div>
            <p
              style={{
                fontSize: '0.8125rem',
                color: 'rgba(255,255,255,0.75)',
                lineHeight: 1.6,
                margin: 0,
                paddingLeft: '1.5rem',
              }}
            >
              É o potencial de fechamento de um deal. Quanto maior o KS, maior a chance de fechar e maior o valor estratégico do negócio. Priorize deals com KS alto e Deal Smell baixo — são os mais saudáveis e prontos para fechar.
            </p>
          </div>

          {/* Divider */}
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

          {/* Section 4 — Como usar */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.5rem',
              }}
            >
              <BookOpen size={16} color="rgba(255,255,255,0.6)" style={{ flexShrink: 0 }} />
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Como usar
              </span>
            </div>
            <ul
              style={{
                fontSize: '0.8125rem',
                color: 'rgba(255,255,255,0.75)',
                lineHeight: 1.6,
                margin: 0,
                paddingLeft: '2.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <li>Dashboard: veja seus deals ativos e os KPIs do seu pipeline</li>
              <li>Contas: entenda a saúde das contas que você gerencia</li>
              <li>Equipe: veja como você está em relação ao seu time</li>
            </ul>
          </div>

        </div>
      </div>
    </div>
  )
}
