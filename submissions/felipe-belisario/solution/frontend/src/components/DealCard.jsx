import { useState } from 'react'

const TIER_COLOR   = { Alta: '#1D9E75', Média: '#F0A500', Baixa: '#E24B4A' }
const TIER_BG      = { Alta: '#0D2E22', Média: '#2E2200', Baixa: '#2E0D0D' }
const TIER_LABEL   = { Alta: 'ALTA PRIORIDADE', Média: 'MÉDIA PRIORIDADE', Baixa: 'BAIXA PRIORIDADE' }
const STAGE_LABEL  = { Engaging: 'Em Negociação', Prospecting: 'Prospecção' }

function getActionText(stage, tier, agent, wr) {
  const wrPct = wr != null ? Math.round(wr * 100) : null
  if (!tier) {
    return 'Não conseguimos calcular a prioridade deste negócio. Vincule a empresa no CRM para receber orientação.'
  }
  const key = `${stage}_${tier}`
  const actions = {
    Prospecting_Alta: `Primeiro contato prioritário — ligue hoje. ${agent} tem ${wrPct}% de conversão em negócios assim.`,
    Prospecting_Média: 'Pesquise a empresa antes de contatar. Prepare uma abordagem personalizada.',
    Prospecting_Baixa: 'Baixa probabilidade de conversão neste perfil. Priorize outros negócios primeiro.',
    Engaging_Alta: 'Negócio quente — agende reunião esta semana. Não deixe esfriar.',
    Engaging_Média: 'Identifique a principal objeção e prepare resposta. Retome o contato nos próximos 3 dias.',
    Engaging_Baixa: 'Probabilidade baixa de fechar. Considere redistribuir para outro responsável ou fechar como perdido.',
  }
  return actions[key] ?? 'Acompanhe este negócio conforme o momento da negociação.'
}

function PriorityBadge({ tier }) {
  const color = TIER_COLOR[tier] ?? '#555870'
  const bg    = TIER_BG[tier]   ?? '#1C1F2E'
  const label = tier ? TIER_LABEL[tier] : 'SEM ANÁLISE'
  return (
    <div style={{
      background: bg,
      border: `1.5px solid ${color}`,
      borderRadius: 8,
      padding: '8px 12px',
      minWidth: 110,
      maxWidth: 130,
      flexShrink: 0,
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 9, fontWeight: 700, color, letterSpacing: '0.08em', marginBottom: 3 }}>
        PRIORIDADE
      </div>
      <div style={{ fontSize: 12, fontWeight: 800, color, lineHeight: 1.2 }}>
        {label.replace(' PRIORIDADE', '')}
      </div>
    </div>
  )
}

function FeatureBar({ label, sublabel, value, color, note }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#E8E9ED', marginBottom: 2 }}>{label}</div>
      {sublabel && (
        <div style={{ fontSize: 11, color: '#8B8FA8', marginBottom: 6 }}>{sublabel}</div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ flex: 1, height: 6, background: '#2A2D3E', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${Math.min(pct, 100)}%`,
            background: color,
            borderRadius: 3,
            transition: 'width 0.5s ease',
          }} />
        </div>
        <span style={{ fontSize: 13, fontWeight: 700, color, minWidth: 36, textAlign: 'right' }}>
          {pct}%
        </span>
      </div>
      {note && (
        <div style={{ fontSize: 11, color: '#F0A500', marginTop: 4 }}>⚠ {note}</div>
      )}
    </div>
  )
}

function fmt(value) {
  if (value == null) return '—'
  return '$' + Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

export function DealCard({ deal, expanded, onToggle, isPersonal }) {
  const [contactRegistered, setContactRegistered] = useState(false)
  const [lostConfirming, setLostConfirming]       = useState(false)
  const [markedLost, setMarkedLost]               = useState(false)

  const color      = TIER_COLOR[deal.tier] ?? '#555870'
  const wr         = deal.wr_breakdown ?? {}
  const stageLabel = STAGE_LABEL[deal.deal_stage] ?? deal.deal_stage ?? '—'
  const chancePct  = deal._raw_prob != null ? Math.round(deal._raw_prob * 100) : null
  const actionText = getActionText(deal.deal_stage, deal.tier, deal.sales_agent, wr.wr_agent_product)

  const borderColor = deal.alert
    ? '#E24B4A'
    : deal.deadline_risk
    ? '#F0A500'
    : '#2A2D3E'

  // Dias desde o último contato
  const daysSinceEngage = deal.engage_date
    ? Math.floor((Date.now() - new Date(deal.engage_date).getTime()) / (1000 * 60 * 60 * 24))
    : null

  const urgencyEl = (() => {
    if (deal.deal_stage === 'Prospecting' && !deal.engage_date) {
      return <span style={{ fontSize: 11, color: '#8B8FA8' }}>○ Aguardando primeiro contato</span>
    }
    if (daysSinceEngage == null) return null
    if (daysSinceEngage > 88) {
      return <span style={{ fontSize: 11, color: '#E24B4A' }}>⚠ {daysSinceEngage} dias em aberto — além do ciclo normal</span>
    }
    if (daysSinceEngage >= 57) {
      return <span style={{ fontSize: 11, color: '#F0A500' }}>◑ {daysSinceEngage} dias — passando da média histórica (57d)</span>
    }
    return <span style={{ fontSize: 11, color: '#1D9E75' }}>● {daysSinceEngage} dias — dentro do ciclo normal</span>
  })()

  const features = [
    {
      label: `Seu histórico nesse produto (${deal.product ?? '—'})`,
      sublabel: wr.wr_agent_product != null
        ? isPersonal
          ? `Você fechou ${Math.round(wr.wr_agent_product * 10)} de cada 10 negócios similares`
          : `${deal.sales_agent} fechou ${Math.round(wr.wr_agent_product * 10)} de cada 10 negócios similares`
        : null,
      value: wr.wr_agent_product,
    },
    {
      label: 'Seu momento atual (últimos 20 negócios)',
      sublabel: wr.wr_agent_recent != null
        ? (wr.wr_agent_recent >= 0.65
            ? (isPersonal ? 'Você está em sequência forte' : 'Sequência forte — taxa recente acima da média')
            : 'Momento abaixo da média — foco em qualidade')
        : null,
      value: wr.wr_agent_recent,
    },
    {
      label: `Seu histórico nesse setor${deal.sector ? ` (${deal.sector})` : ''}`,
      sublabel: null,
      value: wr.wr_agent_sector,
      note: deal.sector_is_real === false ? 'Conta não vinculada — score parcial' : null,
    },
  ]

  return (
    <div
      onClick={onToggle}
      style={{
        background: '#1C1F2E',
        borderRadius: 12,
        border: `0.5px solid ${borderColor}`,
        padding: '16px 18px',
        marginBottom: 8,
        cursor: 'pointer',
        transition: 'background 0.15s ease, opacity 0.3s ease',
        opacity: markedLost ? 0.4 : 1,
      }}
      onMouseEnter={e => e.currentTarget.style.background = '#252839'}
      onMouseLeave={e => e.currentTarget.style.background = '#1C1F2E'}
    >
      {/* Badge de perdido */}
      {markedLost && (
        <div style={{
          background: '#2E0D0D', border: '1px solid #E24B4A',
          borderRadius: 6, padding: '5px 12px', marginBottom: 10,
          fontSize: 12, fontWeight: 700, color: '#E24B4A', display: 'inline-block',
        }}>
          ✕ Marcado como Perdido
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        <PriorityBadge tier={deal.tier} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: '#E8E9ED', marginBottom: 4 }}>
            {deal.account ?? '—'}
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 2 }}>
            <span style={{ color: '#E8E9ED' }}>
              {isPersonal ? 'Produto do meu portfolio' : 'Produto'}:
            </span>{' '}{deal.product ?? '—'}
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 8 }}>
            <span style={{ color: '#E8E9ED' }}>Etapa:</span> {stageLabel}
            {deal.deadline_risk && (
              <span style={{
                marginLeft: 8, background: '#2E2200', color: '#F0A500',
                borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 600,
              }}>
                ⏰ Fecha em 7d
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: 11, color: '#555870' }}>Valor do Negócio</span>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#E8E9ED' }}>
                {fmt(deal.deal_value)}
              </div>
            </div>
            {chancePct != null && (
              <div>
                <span style={{ fontSize: 11, color: '#555870' }}>Chance de Converter</span>
                <div style={{ fontSize: 15, fontWeight: 700, color }}>
                  {chancePct}%
                </div>
              </div>
            )}
            {!isPersonal && (
              <div>
                <span style={{ fontSize: 11, color: '#555870' }}>Responsável</span>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#E8E9ED' }}>
                  {deal.sales_agent ?? '—'}
                </div>
              </div>
            )}
          </div>

          {/* Urgência temporal */}
          {urgencyEl && (
            <div style={{ marginTop: 8 }}>{urgencyEl}</div>
          )}
        </div>

        <div style={{ fontSize: 11, color: '#555870', flexShrink: 0, paddingTop: 4 }}>
          {expanded ? '▲' : '▼'}
        </div>
      </div>

      {/* ── Expanded ── */}
      {expanded && (
        <div
          style={{ marginTop: 16, paddingTop: 16, borderTop: '0.5px solid #2A2D3E' }}
          onClick={e => e.stopPropagation()}
        >
          {/* Feature bars */}
          {features.some(f => f.value != null) && (
            <div style={{ marginBottom: 16 }}>
              <div style={{
                fontSize: 11, fontWeight: 700, color: '#555870',
                textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12,
              }}>
                Por que essa prioridade?
              </div>
              {features.map(f => (
                <FeatureBar
                  key={f.label}
                  label={f.label}
                  sublabel={f.sublabel}
                  value={f.value}
                  color={color}
                  note={f.note}
                />
              ))}
            </div>
          )}

          {/* Alert reason */}
          {deal.alert_reason && (
            <div style={{
              background: '#2E0D0D', borderRadius: 6,
              padding: '8px 12px', fontSize: 12, color: '#E24B4A', marginBottom: 16,
            }}>
              {deal.alert_reason}
            </div>
          )}

          {/* Ação recomendada */}
          <div style={{
            background: (deal.tier ? TIER_BG[deal.tier] : '#1C1F2E') ?? '#1C1F2E',
            border: `0.5px solid ${color}`,
            borderRadius: 8, padding: '12px 14px', marginBottom: 16,
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700, color,
              textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6,
            }}>
              Ação recomendada
            </div>
            <div style={{ fontSize: 13, color: '#E8E9ED', lineHeight: 1.55 }}>
              {actionText}
            </div>
          </div>

          {/* Botões / feedback inline */}
          {contactRegistered ? (
            <div style={{
              background: '#0D2E22', border: '1px solid #1D9E75',
              borderRadius: 8, padding: '12px 16px',
            }}>
              <div style={{ color: '#1D9E75', fontWeight: 700, marginBottom: 6 }}>
                ✓ Contato registrado — {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6 }}>
                Em produção, isso atualizaria o histórico de atividade no CRM,
                recalcularia o momentum do responsável nos próximos 20 deals
                e notificaria o gerente que este negócio foi trabalhado hoje.
              </div>
            </div>
          ) : lostConfirming ? (
            <div style={{
              background: '#2E0D0D', border: '1px solid #E24B4A',
              borderRadius: 8, padding: '12px 16px',
            }}>
              <div style={{ color: '#E24B4A', fontWeight: 700, marginBottom: 8 }}>
                Marcar como Perdido?
              </div>
              <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 12 }}>
                Em produção, isso removeria o negócio do pipeline ativo,
                registraria o motivo de perda e atualizaria as estatísticas
                históricas do responsável para os próximos cálculos de score.
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => { setMarkedLost(true); setLostConfirming(false) }}
                  style={{
                    flex: 1, padding: '8px', borderRadius: 6,
                    background: '#E24B4A', border: 'none',
                    color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  }}
                >
                  Confirmar
                </button>
                <button
                  onClick={() => setLostConfirming(false)}
                  style={{
                    flex: 1, padding: '8px', borderRadius: 6,
                    background: 'transparent', border: '1px solid #2A2D3E',
                    color: '#8B8FA8', fontSize: 12, cursor: 'pointer',
                  }}
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setContactRegistered(true)}
                style={{
                  flex: 1, padding: '10px 0', borderRadius: 8,
                  border: '1px solid #1D9E75', background: '#0D2E22',
                  fontSize: 13, fontWeight: 600, color: '#1D9E75', cursor: 'pointer',
                }}
              >
                ✓ Registrar Contato
              </button>
              <button
                onClick={() => setLostConfirming(true)}
                style={{
                  flex: 1, padding: '10px 0', borderRadius: 8,
                  border: '1px solid #E24B4A', background: '#2E0D0D',
                  fontSize: 13, fontWeight: 600, color: '#E24B4A', cursor: 'pointer',
                }}
              >
                ✕ Marcar como Perdido
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
