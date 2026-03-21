import { useState, useEffect } from 'react'
import axios from 'axios'
import { CopilotPanel } from '../components/CopilotPanel'

const SCORE_COLOR = s => s >= 7 ? '#1D9E75' : s >= 4 ? '#F0A500' : '#E24B4A'

function KpiCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: '#1C1F2E', borderRadius: 12,
      border: '0.5px solid #2A2D3E', padding: '16px 20px',
      minWidth: 160, flex: '1 1 160px',
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#555870', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 800, color: color ?? '#E8E9ED', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: '#8B8FA8', marginTop: 5 }}>{sub}</div>}
    </div>
  )
}

function fmt(v) {
  if (v == null || isNaN(v)) return '$0'
  return '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function fmtPct(v) {
  if (v == null || isNaN(v)) return '—'
  return Math.round(v * 100) + '%'
}

function AgentRow({ agent }) {
  const color = SCORE_COLOR(agent.avg_score ?? 0)
  return (
    <tr style={{ borderTop: '0.5px solid #2A2D3E' }}>
      <td style={{ padding: '11px 16px', fontWeight: 600, color: '#E8E9ED' }}>{agent.sales_agent}</td>
      <td style={{ padding: '11px 16px', color: '#8B8FA8', textAlign: 'center' }}>{agent.total_deals}</td>
      <td style={{ padding: '11px 16px', textAlign: 'center' }}>
        <span style={{ fontWeight: 700, color, fontSize: 14 }}>
          {agent.avg_score != null ? agent.avg_score.toFixed(1) : '—'}
        </span>
      </td>
      <td style={{ padding: '11px 16px', color: '#1D9E75', fontWeight: 600, textAlign: 'center' }}>{agent.alta}</td>
      <td style={{ padding: '11px 16px', color: '#F0A500', fontWeight: 600, textAlign: 'center' }}>{agent.media}</td>
      <td style={{ padding: '11px 16px', color: '#E24B4A', fontWeight: 600, textAlign: 'center' }}>{agent.baixa}</td>
      <td style={{ padding: '11px 16px', textAlign: 'center', color: agent.alerts > 0 ? '#E24B4A' : '#555870' }}>
        {agent.alerts > 0 ? `⚠ ${agent.alerts}` : '—'}
      </td>
    </tr>
  )
}

function RedistCard({ s }) {
  const [done, setDone] = useState(false)

  return (
    <div style={{
      background: '#0F1117', borderRadius: 10,
      border: '0.5px solid #2A2D3E', padding: '16px 18px', marginBottom: 10,
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: '#4F8EF7', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
        Realocação Sugerida
      </div>

      <div style={{ fontSize: 14, fontWeight: 700, color: '#E8E9ED', marginBottom: 4 }}>
        {s.account ? s.account : (
          <span>
            <span style={{ color: '#F0A500' }}>Empresa não identificada</span>
            <span style={{
              marginLeft: 8, background: '#2E2200',
              color: '#F0A500', borderRadius: 4,
              padding: '1px 6px', fontSize: 10, fontWeight: 700,
            }}>
              ⚠ Preencher conta
            </span>
          </span>
        )}
      </div>
      <div style={{ fontSize: 13, color: '#8B8FA8', marginBottom: 10 }}>
        Produto: <span style={{ color: '#E8E9ED' }}>{s.product}</span> — Valor: <span style={{ color: '#4F8EF7', fontWeight: 600 }}>{fmt(s.deal_value)}</span>
      </div>

      <div style={{ display: 'flex', gap: 20, marginBottom: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 11, color: '#555870', marginBottom: 2 }}>Responsável atual</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#E24B4A' }}>{s.current_agent}</div>
          <div style={{ fontSize: 12, color: '#8B8FA8' }}>
            Taxa de conversão nesse produto: <strong>{fmtPct(s.current_wr)}</strong>
          </div>
        </div>
        <div style={{ fontSize: 18, color: '#555870', alignSelf: 'center' }}>→</div>
        <div>
          <div style={{ fontSize: 11, color: '#555870', marginBottom: 2 }}>Sugestão</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#1D9E75' }}>{s.suggested_agent}</div>
          <div style={{ fontSize: 12, color: '#8B8FA8' }}>
            Taxa de conversão nesse produto: <strong>{fmtPct(s.suggested_wr)}</strong>
          </div>
        </div>
      </div>

      <div style={{
        background: '#0D2E22', borderRadius: 6, padding: '8px 12px', marginBottom: 12,
        fontSize: 13, color: '#1D9E75', fontWeight: 600,
      }}>
        Ganho estimado: +{fmt(s.financial_impact)} em valor esperado
        <span style={{ fontWeight: 400, color: '#8B8FA8', marginLeft: 8 }}>
          (+{Math.round((s.wr_gain ?? 0) * 100)} pontos percentuais de conversão)
        </span>
      </div>

      {done ? (
        <div style={{
          background: '#0D2E22', border: '1px solid #1D9E75',
          borderRadius: 8, padding: '12px 16px',
        }}>
          <div style={{ color: '#1D9E75', fontWeight: 700, marginBottom: 6 }}>
            ✓ Realocação registrada
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6 }}>
            Em produção, {s.suggested_agent} receberia uma notificação imediata
            com os detalhes do negócio e o motivo da realocação. O score seria
            recalculado com o histórico do novo responsável.
          </div>
        </div>
      ) : (
        <button
          onClick={e => { e.stopPropagation(); setDone(true) }}
          style={{
            width: '100%', padding: '10px 0', borderRadius: 8,
            background: '#4F8EF7', border: 'none',
            fontSize: 13, fontWeight: 700, color: '#FFFFFF',
            cursor: 'pointer',
          }}
        >
          Realocar e Notificar Responsável
        </button>
      )}
    </div>
  )
}

function ActionPlanCard({ agent, stalledDeals }) {
  const [modal, setModal] = useState(false)
  const dealList = stalledDeals.slice(0, 3).map(d => d.account ?? d.opportunity_id).join(', ')
  const msg = `${agent}, vi que os negócios ${dealList} estão há mais de 30 dias sem movimento.\nPode me enviar um breve plano de ação para cada um até sexta-feira?`

  return (
    <div style={{
      background: '#1C1F2E', borderRadius: 10,
      border: '0.5px solid #2E2200', padding: '14px 16px', marginBottom: 8,
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#F0A500', marginBottom: 2 }}>
        {agent}
      </div>
      <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 10 }}>
        {stalledDeals.length} negócios parados há mais de 30 dias
      </div>
      <button
        onClick={() => setModal(true)}
        style={{
          padding: '7px 14px', borderRadius: 6,
          border: '1px solid #F0A500', background: '#2E2200',
          fontSize: 12, fontWeight: 600, color: '#F0A500', cursor: 'pointer',
        }}
      >
        Solicitar Plano de Ação
      </button>

      {modal && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
          }}
          onClick={() => setModal(false)}
        >
          <div
            style={{
              background: '#1C1F2E', borderRadius: 12, border: '0.5px solid #2A2D3E',
              padding: 24, maxWidth: 480, width: '90%',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontSize: 14, fontWeight: 700, color: '#E8E9ED', marginBottom: 12 }}>
              Mensagem para {agent}
            </div>
            <textarea
              readOnly
              value={msg}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8,
                border: '0.5px solid #2A2D3E', background: '#0F1117',
                fontSize: 13, color: '#E8E9ED', lineHeight: 1.6,
                resize: 'none', height: 90,
              }}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button
                onClick={() => { navigator.clipboard.writeText(msg); setModal(false) }}
                style={{
                  flex: 1, padding: '9px 0', borderRadius: 8,
                  background: '#4F8EF7', border: 'none',
                  fontSize: 13, fontWeight: 700, color: '#FFFFFF', cursor: 'pointer',
                }}
              >
                Copiar Mensagem
              </button>
              <button
                onClick={() => setModal(false)}
                style={{
                  padding: '9px 16px', borderRadius: 8,
                  border: '0.5px solid #2A2D3E', background: 'transparent',
                  fontSize: 13, color: '#8B8FA8', cursor: 'pointer',
                }}
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CoachingCard({ agent }) {
  const [copied, setCopied] = useState(false)
  const firstName = agent.sales_agent.split(' ')[0]
  const message =
    `Olá ${firstName}, vi que você tem ${agent.baixa} negócios em Baixa Prioridade ` +
    `com score médio de ${agent.avg_score?.toFixed(1)}. ` +
    `Podemos conversar sobre esses negócios esta semana? ` +
    `Quero entender o que está acontecendo e ver como posso ajudar.`

  return (
    <div style={{
      background: '#252839', borderRadius: 8,
      padding: '12px 14px', marginBottom: 8,
      display: 'flex', alignItems: 'flex-start',
      justifyContent: 'space-between', gap: 12,
    }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#E8E9ED', marginBottom: 3 }}>
          {agent.sales_agent}
        </div>
        <div style={{ fontSize: 12, color: '#8B8FA8' }}>
          Score médio:{' '}
          <span style={{ color: '#E24B4A', fontWeight: 600 }}>
            {agent.avg_score?.toFixed(1)}
          </span>
          {' · '}{agent.baixa} negócios em Baixa Prioridade
          {' · '}{agent.total_deals} negócios no total
        </div>
      </div>
      <button
        onClick={() => {
          navigator.clipboard.writeText(message)
          setCopied(true)
          setTimeout(() => setCopied(false), 2000)
        }}
        style={{
          padding: '7px 14px', borderRadius: 6, flexShrink: 0,
          background: copied ? '#0D2E22' : '#1C1F2E',
          border: `0.5px solid ${copied ? '#1D9E75' : '#2A2D3E'}`,
          color: copied ? '#1D9E75' : '#8B8FA8',
          fontSize: 12, fontWeight: 600, cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {copied ? '✓ Copiado' : '📋 Copiar mensagem'}
      </button>
    </div>
  )
}

function isPendente(account) {
  return account == null || account === '(conta pendente)'
}

function ManagerDashboard({ data }) {
  const { agent_summary, redistribution_suggestions, total_deals, team_size, manager, total_pipeline_value } = data

  const sorted     = [...agent_summary].sort((a, b) => (b.avg_score ?? 0) - (a.avg_score ?? 0))
  const avgScore   = sorted.reduce((s, a) => s + (a.avg_score ?? 0), 0) / (sorted.length || 1)
  const totalAlerts = sorted.reduce((s, a) => s + (a.alerts ?? 0), 0)
  const totalBaixa  = sorted.reduce((s, a) => s + (a.baixa ?? 0), 0)
  const totalValue  = total_pipeline_value ?? sorted.reduce((s, a) => s + (a.total_value ?? 0), 0)

  // Separar sugestões com e sem empresa vinculada
  const redistNormal   = redistribution_suggestions.filter(s => !isPendente(s.account))
  const redistPendente = redistribution_suggestions.filter(s => isPendente(s.account))
  const redistImpact   = redistNormal.reduce((s, r) => s + (r.financial_impact ?? 0), 0)
  const pendenteValue  = redistPendente.reduce((s, r) => s + (r.deal_value ?? 0), 0)

  const copilotSuggestions = [
    `Qual responsável do time de ${manager} precisa de atenção esta semana?`,
    'Quanto posso recuperar em receita executando todas as realocações sugeridas?',
    'Quem está em momento baixo e deveria receber coaching agora?',
  ]

  const lowPerformers = agent_summary.filter(a => (a.avg_score ?? 10) < 5.0)

  // Receita em risco: total_value dos agentes com score baixo
  const riskValue = data.deals
    ? data.deals.filter(d => d.tier === 'Baixa' || d.alert).reduce((s, d) => s + (d.deal_value ?? 0), 0)
    : 0

  // Agentes com baixo momento ou muita baixa
  const lowAgents = sorted.filter(a => (a.avg_score ?? 10) < 5 || (a.baixa ?? 0) >= 3)

  // Deals parados por agente (>30 dias sem engage)
  const today = Date.now()
  const agentStalled = {}
  if (data.deals) {
    for (const d of data.deals) {
      if (!d.engage_date) continue
      const days = (today - new Date(d.engage_date).getTime()) / 86400000
      if (days > 30) {
        if (!agentStalled[d.sales_agent]) agentStalled[d.sales_agent] = []
        agentStalled[d.sales_agent].push(d)
      }
    }
  }
  const stalledAgents = lowAgents.filter(a => (agentStalled[a.sales_agent] ?? []).length > 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: '#E8E9ED' }}>{manager}</h2>
        <span style={{ fontSize: 13, color: '#8B8FA8' }}>
          {team_size} responsáveis · {total_deals} negócios
        </span>
      </div>

      {/* KPIs financeiros */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
        <KpiCard
          label="Valor Total do Pipeline do Time"
          value={`$${(totalValue / 1000).toFixed(0)}k`}
          color="#4F8EF7"
          sub={`${total_deals} negócios abertos`}
        />
        <KpiCard
          label="Receita em Risco"
          value={`$${(riskValue / 1000).toFixed(0)}k`}
          color={riskValue > 0 ? '#E24B4A' : '#555870'}
          sub="baixa prioridade + sem análise"
        />
        <KpiCard
          label="Ganho Potencial com Realocações"
          value={`$${(redistImpact / 1000).toFixed(1)}k`}
          color={redistImpact > 0 ? '#1D9E75' : '#555870'}
          sub={`${redistribution_suggestions.length} realocações sugeridas`}
        />
        <KpiCard
          label="Negócios sem Orientação"
          value={totalAlerts}
          color={totalAlerts > 0 ? '#E24B4A' : '#555870'}
          sub="dados insuficientes no CRM"
        />
      </div>

      {/* Redistribuições sugeridas */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#E8E9ED', marginBottom: 10 }}>
          Realocações Sugeridas
        </div>
        {redistNormal.length > 0 ? (
          redistNormal.map((s, i) => (
            <RedistCard key={i} s={s} />
          ))
        ) : (
          <div style={{
            background: '#1C1F2E', borderRadius: 10,
            border: '0.5px solid #2A2D3E',
            textAlign: 'center', padding: '24px',
            color: '#555870',
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>✓</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#8B8FA8', marginBottom: 4 }}>
              Todos os negócios bem alocados
            </div>
            <div style={{ fontSize: 12 }}>
              Nenhuma realocação sugerida para este time.
              O modelo não encontrou combinações agente×produto
              com ganho superior a 10 pontos percentuais.
            </div>
          </div>
        )}
      </div>

      {/* Negócios sem empresa vinculada */}
      {redistPendente.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{
            background: '#1C1F2E', borderRadius: 10,
            border: '0.5px solid #2E2200', padding: '16px 18px',
          }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#F0A500', marginBottom: 6 }}>
              ⚠ Negócios sem empresa vinculada — preencher antes de realocar
            </div>
            <div style={{ fontSize: 13, color: '#8B8FA8', marginBottom: 4 }}>
              {redistPendente.length} negócio{redistPendente.length !== 1 ? 's' : ''} aguardam vinculação de conta no CRM.
            </div>
            <div style={{ fontSize: 13, color: '#F0A500', fontWeight: 600 }}>
              {fmt(pendenteValue)} em valor total em risco
            </div>
            <div style={{ fontSize: 12, color: '#555870', marginTop: 8 }}>
              Esses negócios têm potencial de realocação, mas não é possível identificar a empresa para concluir a sugestão. Atualize o campo "Conta" no CRM para cada um.
            </div>
          </div>
        </div>
      )}

      {/* Cobrar plano de ação */}
      {stalledAgents.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#E8E9ED', marginBottom: 10 }}>
            Cobrar Plano de Ação
          </div>
          {stalledAgents.map(a => (
            <ActionPlanCard
              key={a.sales_agent}
              agent={a.sales_agent}
              stalledDeals={agentStalled[a.sales_agent] ?? []}
            />
          ))}
        </div>
      )}

      {/* Responsáveis que precisam de atenção */}
      {lowPerformers.length > 0 && (
        <div style={{
          background: '#1C1F2E', borderRadius: 12,
          border: '0.5px solid #2A2D3E',
          padding: '16px 20px', marginBottom: 20,
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#E8E9ED', marginBottom: 4 }}>
            Responsáveis que precisam de atenção
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 16 }}>
            Estes responsáveis têm score médio abaixo de 5.0.
            Considere uma conversa de coaching ou revisão de carteira.
          </div>
          {lowPerformers.map(a => (
            <CoachingCard key={a.sales_agent} agent={a} />
          ))}
        </div>
      )}

      {/* Tabela de agentes */}
      <div style={{
        background: '#1C1F2E', borderRadius: 12,
        border: '0.5px solid #2A2D3E', overflow: 'hidden',
      }}>
        <div style={{ padding: '14px 20px', borderBottom: '0.5px solid #2A2D3E' }}>
          <span style={{ fontSize: 14, fontWeight: 700, color: '#E8E9ED' }}>Responsáveis do Time</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#0F1117' }}>
              {['Responsável', 'Negócios', 'Prioridade Média', 'Alta Prior.', 'Média Prior.', 'Baixa Prior.', 'Sem Orientação'].map(h => (
                <th key={h} style={{
                  padding: '10px 16px',
                  textAlign: h === 'Responsável' ? 'left' : 'center',
                  color: '#555870', fontWeight: 600, fontSize: 11,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(a => <AgentRow key={a.sales_agent} agent={a} />)}
          </tbody>
        </table>
      </div>

      <CopilotPanel
        suggestions={copilotSuggestions}
        manager={manager}
      />
    </div>
  )
}

export function Manager() {
  const [query, setQuery]  = useState('Summer Sewald')
  const [data, setData]    = useState(null)
  const [loading, setLoad] = useState(false)
  const [error, setError]  = useState('')

  const search = async (name) => {
    const q = (name ?? query).trim()
    if (!q) return
    setLoad(true); setError('')
    try {
      const r = await axios.get(`/api/manager/${encodeURIComponent(q)}`)
      setData(r.data)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Manager não encontrado.')
      setData(null)
    }
    setLoad(false)
  }

  useEffect(() => {
    search('Summer Sewald')
  }, [])

  const MANAGERS = ['Summer Sewald', 'Melvin Marxen', 'Dustin Brinkmann', 'Celia Rouche', 'Rocco Neubert', 'Cara Losch']

  return (
    <div>
      {/* Busca */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          placeholder="Nome do gerente..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          style={{
            flex: 1, padding: '10px 14px', borderRadius: 8,
            border: '0.5px solid #2A2D3E', fontSize: 14,
            background: '#1C1F2E', color: '#E8E9ED', outline: 'none',
          }}
        />
        <button
          onClick={() => search()}
          style={{
            padding: '10px 22px', borderRadius: 8, background: '#4F8EF7',
            color: '#FFFFFF', border: 'none', fontSize: 14, fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          Ver Time
        </button>
      </div>

      {/* Atalhos */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 24 }}>
        {MANAGERS.map(m => (
          <button
            key={m}
            onClick={() => { setQuery(m); search(m) }}
            style={{
              padding: '5px 12px', borderRadius: 20, fontSize: 12,
              border: '0.5px solid #2A2D3E', background: '#1C1F2E', color: '#8B8FA8',
              cursor: 'pointer',
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {error && <div style={{ color: '#E24B4A', marginBottom: 16, fontSize: 14 }}>{error}</div>}
      {loading && <div style={{ color: '#8B8FA8', padding: 20 }}>Carregando...</div>}
      {data && <ManagerDashboard data={data} />}

      {!data && !loading && !error && (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: '#555870', fontSize: 14 }}>
          Selecione um gerente acima para ver o pipeline do time.
        </div>
      )}
    </div>
  )
}
