import { useState, useEffect } from 'react'
import axios from 'axios'
import { DealCard } from '../components/DealCard'
import { CopilotPanel } from '../components/CopilotPanel'

const STAGE_LABEL = { Engaging: 'Em Negociação', Prospecting: 'Prospecção' }

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
      <div style={{ fontSize: 26, fontWeight: 800, color: color ?? '#E8E9ED', lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: '#8B8FA8', marginTop: 5 }}>{sub}</div>
      )}
    </div>
  )
}

function fmt(v) {
  if (v == null || isNaN(v)) return '$0'
  return '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

export function Vendedor() {
  const [data, setData]         = useState(null)
  const [filter, setFilter]     = useState('Todos')
  const [statusFilter, setStatus] = useState('Todos')
  const [agentFilter, setAgent] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    axios.get('/api/pipeline').then(r => setData(r.data))
  }, [])

  if (!data) {
    return (
      <div style={{ padding: 40, color: '#8B8FA8', textAlign: 'center', fontSize: 14 }}>
        Carregando pipeline...
      </div>
    )
  }

  const { summary, deals } = data
  const tiers = summary.tier_breakdown

  const agents = [...new Set(deals.map(d => d.sales_agent))].sort()

  // Filtro combinado: tier + status + agente
  const filtered = deals
    .filter(d => {
      if (filter === 'Alerta') return d.alert
      if (filter !== 'Todos') return d.tier === filter
      return true
    })
    .filter(d => {
      if (statusFilter === 'Em Negociação') return d.deal_stage === 'Engaging'
      if (statusFilter === 'Prospecção')    return d.deal_stage === 'Prospecting'
      return true
    })
    .filter(d => !agentFilter || d.sales_agent === agentFilter)
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))

  // KPIs calculados SOBRE os deals filtrados
  const filteredScored = filtered.filter(d => d.has_score)
  const totalValue     = filtered.reduce((s, d) => s + (d.deal_value ?? 0), 0)
  const avgWR          = filteredScored.length
    ? filteredScored.reduce((s, d) => s + (d.wr_breakdown?.wr_agent_product ?? 0), 0) / filteredScored.length
    : 0
  const avgMoment      = filteredScored.length
    ? filteredScored.reduce((s, d) => s + (d.wr_breakdown?.wr_agent_recent ?? 0), 0) / filteredScored.length
    : 0
  const altaCount  = filtered.filter(d => d.tier === 'Alta').length
  const altaValue  = filtered.filter(d => d.tier === 'Alta').reduce((s, d) => s + (d.deal_value ?? 0), 0)
  const baixaCount = filtered.filter(d => d.tier === 'Baixa').length
  const baixaValue = filtered.filter(d => d.tier === 'Baixa').reduce((s, d) => s + (d.deal_value ?? 0), 0)
  const semAnalise = filtered.filter(d => d.alert).length

  const toggle = id => setExpanded(prev => prev === id ? null : id)

  // Filtro tier — labels com contagem do total (sem agente filter)
  const tierCounts = {
    Todos: deals.length,
    Alta:  tiers['Alta']  ?? 0,
    Média: tiers['Média'] ?? 0,
    Baixa: tiers['Baixa'] ?? 0,
    Alerta: summary.unscored_alerts,
  }
  const TIER_FILTERS = [
    { key: 'Todos', label: `Todos os Negócios` },
    { key: 'Alta',  label: `Alta Prioridade` },
    { key: 'Média', label: `Média Prioridade` },
    { key: 'Baixa', label: `Baixa Prioridade` },
    { key: 'Alerta', label: `Atenção Necessária` },
  ]
  const STATUS_FILTERS = ['Todos', 'Em Negociação', 'Prospecção']

  const agentFirstName = agentFilter ? agentFilter.split(' ')[0] : null

  const copilotSuggestions = agentFilter ? [
    'Quais dos meus negócios estão em risco de vencer sem fechamento?',
    'Tenho negócios de Alta Prioridade sem contato nos últimos 7 dias?',
    'Em qual produto eu tenho a maior taxa de conversão histórica?',
  ] : [
    'Quais negócios do pipeline têm maior risco de perda esta semana?',
    'Quais responsáveis estão com mais negócios em Baixa Prioridade?',
    'Existe algum negócio que deveria ser fechado para limpar o pipeline?',
  ]

  return (
    <div>
      {/* Header personalizado por responsável */}
      {agentFirstName && (
        <div style={{
          background: 'linear-gradient(135deg, #1C1F2E 0%, #13151F 100%)',
          borderRadius: 10,
          borderLeft: '3px solid #4F8EF7',
          padding: '16px 20px',
          marginBottom: 20,
        }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#E8E9ED', marginBottom: 4 }}>
            Olá, {agentFirstName}.
          </div>
          <div style={{ fontSize: 13, color: '#8B8FA8', lineHeight: 1.6 }}>
            Você tem <span style={{ color: '#E8E9ED', fontWeight: 600 }}>{filtered.length} negócios abertos</span> —{' '}
            <span style={{ color: '#1D9E75', fontWeight: 600 }}>{altaCount} em Alta Prioridade</span>.{' '}
            {avgMoment >= 0.65
              ? 'Seu momento está excelente. Bom dia para prospectar.'
              : 'Seu momento está abaixo da média. Foque nos negócios de Alta Prioridade.'}
          </div>
        </div>
      )}

      {/* Mensagens do gerente */}
      {!agentFirstName && (
        <div style={{
          background: '#1C1F2E', borderRadius: 10,
          border: '0.5px solid #2A2D3E', padding: '14px 18px',
          marginBottom: 20,
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#555870', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
            Mensagens do seu Gerente
          </div>
          <div style={{ fontSize: 13, color: '#8B8FA8' }}>
            Nenhuma mensagem nova. Seu gerente pode enviar orientações sobre negócios específicos.
          </div>
        </div>
      )}

      {/* KPIs reativos (sobre os deals filtrados) */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        <KpiCard
          label="Valor Total em Negociação"
          value={fmt(totalValue)}
          color="#4F8EF7"
          sub={`${filtered.length} negócios no filtro atual`}
        />
        <KpiCard
          label="Taxa de Conversão Histórica"
          value={`${(avgWR * 100).toFixed(0)}%`}
          color="#1D9E75"
          sub="seu histórico nesse produto"
        />
        <KpiCard
          label="Negócios em Alta Prioridade"
          value={altaCount}
          color="#1D9E75"
          sub={fmt(altaValue) + ' em valor'}
        />
        <KpiCard
          label="Baixa Prioridade"
          value={baixaCount}
          color={baixaCount > 0 ? '#F0A500' : '#555870'}
          sub={fmt(baixaValue) + ' em valor'}
        />
        <KpiCard
          label="Sem Análise"
          value={semAnalise}
          color={semAnalise > 0 ? '#E24B4A' : '#555870'}
          sub="dados insuficientes no CRM"
        />
        <KpiCard
          label="Seu Momento Atual"
          value={`${(avgMoment * 100).toFixed(0)}%`}
          color={avgMoment >= 0.65 ? '#1D9E75' : '#F0A500'}
          sub="últimos 20 negócios"
        />
      </div>

      {/* Filtros de tier */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        {TIER_FILTERS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            style={{
              padding: '6px 13px', borderRadius: 6, fontSize: 12,
              background: filter === key ? '#4F8EF7' : '#1C1F2E',
              color: filter === key ? '#FFFFFF' : '#8B8FA8',
              border: `0.5px solid ${filter === key ? '#4F8EF7' : '#2A2D3E'}`,
              fontWeight: filter === key ? 700 : 400,
            }}
          >
            {label} ({tierCounts[key]})
          </button>
        ))}
      </div>

      {/* Filtros de status + agente */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
        {STATUS_FILTERS.map(s => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            style={{
              padding: '5px 12px', borderRadius: 6, fontSize: 12,
              background: statusFilter === s ? '#252839' : 'transparent',
              color: statusFilter === s ? '#E8E9ED' : '#8B8FA8',
              border: `0.5px solid ${statusFilter === s ? '#555870' : '#2A2D3E'}`,
            }}
          >
            {s === 'Todos' ? 'Todas as Etapas' : s}
          </button>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          {!agentFilter && (
            <div style={{
              fontSize: 11, color: '#4F8EF7',
              marginBottom: 4, textAlign: 'right',
            }}>
              ↓ Selecione um responsável para ver o pipeline personalizado
            </div>
          )}
          <select
            value={agentFilter}
            onChange={e => setAgent(e.target.value)}
            style={{
              padding: '5px 10px', borderRadius: 6, fontSize: 12,
              border: `0.5px solid ${agentFilter ? '#4F8EF7' : '#2A2D3E'}`,
              background: '#1C1F2E', color: '#8B8FA8',
              outline: 'none',
            }}
          >
            <option value="">Ver pipeline de um responsável...</option>
            {agents.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>

      {/* Contagem */}
      <div style={{ fontSize: 12, color: '#555870', marginBottom: 10 }}>
        {filtered.length} negócio{filtered.length !== 1 ? 's' : ''} · ordenados por prioridade (maior primeiro)
      </div>

      {/* Deal cards */}
      {filtered.slice(0, 150).map(d => (
        <DealCard
          key={d.opportunity_id}
          deal={d}
          expanded={expanded === d.opportunity_id}
          onToggle={() => toggle(d.opportunity_id)}
          isPersonal={!!agentFilter}
        />
      ))}

      {filtered.length > 150 && (
        <p style={{ textAlign: 'center', color: '#555870', fontSize: 13, marginTop: 16 }}>
          Mostrando 150 de {filtered.length} negócios. Use os filtros para refinar.
        </p>
      )}

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: '#555870', fontSize: 14 }}>
          Nenhum negócio encontrado para este filtro.
        </div>
      )}

      <CopilotPanel suggestions={copilotSuggestions} />
    </div>
  )
}
