import { useState, useEffect } from 'react'
import axios from 'axios'
import { CopilotPanel } from '../components/CopilotPanel'

const BASELINE_WR      = 0.632
const BASELINE_ALTA_WR = 0.72
const META1_WR         = 0.66
const META2_ALTA       = 0.15

function ProgressBar({ value, max = 100, color, height = 8 }) {
  const pct = Math.min((value / max) * 100, 100)
  return (
    <div style={{ height, background: '#2A2D3E', borderRadius: height }}>
      <div style={{
        height: '100%', borderRadius: height,
        width: `${pct}%`, background: color,
        transition: 'width 0.7s ease',
      }} />
    </div>
  )
}

function SectionCard({ title, children }) {
  return (
    <div style={{
      background: '#1C1F2E', borderRadius: 12,
      border: '0.5px solid #2A2D3E', padding: '20px', marginBottom: 20,
    }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: '#E8E9ED', marginBottom: 16 }}>{title}</div>
      {children}
    </div>
  )
}

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
  if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`
  if (v >= 1000)    return `$${(v / 1000).toFixed(0)}k`
  return '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

export function RevOps() {
  const [pipeline, setPipeline]     = useState(null)
  const [finSummary, setFinSummary] = useState(null)

  useEffect(() => {
    Promise.all([
      axios.get('/api/pipeline'),
      axios.get('/api/pipeline/summary'),
    ]).then(([pRes, sRes]) => {
      setPipeline(pRes.data)
      setFinSummary(sRes.data)
    })
  }, [])

  if (!pipeline || !finSummary) {
    return (
      <div style={{ padding: 40, color: '#8B8FA8', textAlign: 'center', fontSize: 14 }}>
        Carregando...
      </div>
    )
  }

  const { summary, deals } = pipeline
  const tiers = summary.tier_breakdown
  const total = summary.total

  const altaCount  = tiers['Alta']  ?? 0
  const mediaCount = tiers['Média'] ?? 0
  const baixaCount = tiers['Baixa'] ?? 0
  const alertCount = summary.unscored_alerts

  const altaPct     = altaCount / total
  const coveragePct = summary.scored / total

  const meta2Pct = Math.min((altaPct / META2_ALTA) * 100, 100)
  const meta2Ok  = altaPct >= META2_ALTA

  const redistImpact = finSummary.total_redistribution_impact ?? 0

  // Revenue sem análise calculada dos deals
  const revSemAnalise = deals
    ? deals.filter(d => d.alert).reduce((s, d) => s + (d.deal_value ?? 0), 0)
    : 0

  // Saúde do CRM
  const healthItems = [
    {
      label: 'Cobertura de score',
      value: `${(coveragePct * 100).toFixed(1)}%`,
      ok: coveragePct >= 0.95,
      target: '≥ 95%',
    },
    {
      label: 'Pipeline Alta Prioridade',
      value: `${(altaPct * 100).toFixed(1)}%`,
      ok: altaPct >= META2_ALTA,
      target: `≥ ${(META2_ALTA * 100).toFixed(0)}%`,
    },
    {
      label: 'Negócios sem análise',
      value: `${((alertCount / total) * 100).toFixed(1)}%`,
      ok: alertCount / total <= 0.05,
      target: '≤ 5%',
    },
    {
      label: 'Pipeline Baixa Prioridade',
      value: `${((baixaCount / total) * 100).toFixed(1)}%`,
      ok: baixaCount / total <= 0.10,
      target: '≤ 10%',
    },
    {
      label: 'Risco de prazo (7 dias)',
      value: summary.deadline_risks,
      ok: summary.deadline_risks === 0,
      target: '= 0',
    },
  ]
  const healthScore = Math.round(healthItems.filter(h => h.ok).length / healthItems.length * 100)
  const healthColor = healthScore >= 80 ? '#1D9E75' : healthScore >= 60 ? '#F0A500' : '#E24B4A'

  const ACTION_CARDS = [
    {
      label: 'ALTA PRIORIDADE',
      color: '#1D9E75',
      bg: '#0D2E22',
      count: altaCount,
      value: finSummary.revenue_alta,
      action: 'Proteger — garantir que os responsáveis estão ativos nestes deals. Nenhum deve ficar mais de 7 dias sem contato.',
      icon: '▲',
    },
    {
      label: 'MÉDIA PRIORIDADE',
      color: '#F0A500',
      bg: '#2E2200',
      count: mediaCount,
      value: finSummary.revenue_media,
      action: 'Qualificar — identificar quais têm potencial de subir para Alta. Foco em deals com mais de 30 dias sem movimento.',
      icon: '◑',
    },
    {
      label: 'BAIXA PRIORIDADE',
      color: '#E24B4A',
      bg: '#2E0D0D',
      count: baixaCount,
      value: finSummary.revenue_baixa,
      action: 'Decisão necessária — redistribuir para agente com histórico mais forte no produto, ou fechar como perdido para limpar o pipeline.',
      icon: '▼',
    },
    {
      label: 'SEM ANÁLISE',
      color: '#555870',
      bg: '#1C1F2E',
      count: alertCount,
      value: revSemAnalise,
      action: 'Urgente — o modelo não consegue avaliar estes negócios. Responsáveis precisam vincular a empresa no CRM para receber orientação.',
      icon: '?',
    },
  ]

  const copilotSuggestions = [
    'Estamos no caminho das metas de 90 dias?',
    'Qual o impacto financeiro de resolver o problema de contas sem vinculação?',
    'Qual região tem maior concentração de negócios em Baixa Prioridade?',
  ]

  return (
    <div>
      {/* BLOCO 1 — Onde está o dinheiro hoje? */}
      <SectionCard title="Onde está o dinheiro hoje?">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <KpiCard
            label="Valor Total em Negociação"
            value={fmt(finSummary.total_pipeline_value)}
            color="#4F8EF7"
            sub={`${total} negócios abertos`}
          />
          <KpiCard
            label="Receita Qualificada (Alta Prior.)"
            value={fmt(finSummary.revenue_alta)}
            color="#1D9E75"
            sub={`${altaCount} negócios de alta prioridade`}
          />
          <KpiCard
            label="Receita em Risco"
            value={fmt(finSummary.revenue_at_risk)}
            color="#E24B4A"
            sub="baixa prioridade + sem análise"
          />
          <KpiCard
            label="Ganho Potencial com Realocações"
            value={fmt(redistImpact)}
            color={redistImpact > 0 ? '#1D9E75' : '#555870'}
            sub="impacto estimado de realocações"
          />
        </div>

        {/* Narrativa conectando os números */}
        <div style={{
          background: '#0F1117', borderRadius: 8,
          padding: '12px 16px', marginTop: 14,
          borderLeft: '3px solid #4F8EF7',
        }}>
          <div style={{ fontSize: 13, color: '#8B8FA8', lineHeight: 1.7 }}>
            De{' '}
            <strong style={{ color: '#4F8EF7' }}>{fmt(finSummary.total_pipeline_value)}</strong>{' '}
            em negociação,{' '}
            <strong style={{ color: '#1D9E75' }}>{fmt(finSummary.revenue_alta)}</strong>{' '}
            está qualificado pelo modelo como Alta Prioridade.{' '}
            <strong style={{ color: '#E24B4A' }}>{fmt(finSummary.revenue_at_risk)}</strong>{' '}
            está em risco por baixa probabilidade ou dados insuficientes.
            {redistImpact > 0 && (
              <>{' '}Executar as realocações sugeridas pode recuperar{' '}
              <strong style={{ color: '#1D9E75' }}>{fmt(redistImpact)}</strong>{' '}
              em valor esperado.</>
            )}
          </div>
        </div>
      </SectionCard>

      {/* BLOCO 2 — Contrato de Resultado */}
      <SectionCard title="Contrato de Resultado">
        {/* Baseline */}
        <div style={{
          background: '#0F1117', borderRadius: 8, padding: '12px 16px', marginBottom: 12,
        }}>
          <div style={{ fontSize: 12, color: '#555870', marginBottom: 3 }}>Ponto de Partida</div>
          <div style={{ fontSize: 14, color: '#E8E9ED' }}>
            Historicamente, o time converte{' '}
            <strong style={{ color: '#4F8EF7' }}>{(BASELINE_WR * 100).toFixed(1)}%</strong>{' '}
            dos negócios
          </div>
        </div>

        {/* Meta 1 */}
        <div style={{
          background: '#0F1117', borderRadius: 8, padding: '12px 16px', marginBottom: 12,
          borderLeft: '3px solid #F0A500',
        }}>
          <div style={{ fontSize: 12, color: '#555870', marginBottom: 3 }}>Meta 1</div>
          <div style={{ fontSize: 14, color: '#E8E9ED' }}>
            Negócios de Alta Prioridade devem converter ≥{' '}
            <strong style={{ color: '#F0A500' }}>{(META1_WR * 100).toFixed(0)}%</strong>
          </div>
          <div style={{
            background: '#1C2030', borderRadius: 6,
            padding: '8px 12px', marginTop: 8,
            fontSize: 12, color: '#8B8FA8',
          }}>
            📊 Em acompanhamento — será verificada quando os{' '}
            {altaCount} negócios de Alta Prioridade fecharem.
            O modelo histórico sugere conversão de ~{Math.round(BASELINE_ALTA_WR * 100)}%
            para este perfil de deals.
          </div>
        </div>

        {/* Meta 2 */}
        <div style={{
          background: meta2Ok ? '#0D2E22' : '#2E2200',
          borderRadius: 8, padding: '12px 16px',
          borderLeft: `3px solid ${meta2Ok ? '#1D9E75' : '#F0A500'}`,
        }}>
          <div style={{ fontSize: 12, color: '#555870', marginBottom: 3 }}>Meta 2</div>
          <div style={{ fontSize: 14, color: '#E8E9ED', marginBottom: 6 }}>
            ≥ {(META2_ALTA * 100).toFixed(0)}% do pipeline em Alta Prioridade
            {' '}
            <span style={{ color: meta2Ok ? '#1D9E75' : '#F0A500', fontWeight: 700 }}>
              (hoje: {(altaPct * 100).toFixed(1)}% {meta2Ok ? '✅' : '⚠'})
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', marginBottom: 10 }}>
            {meta2Ok
              ? `Meta atingida — ${altaCount} negócios qualificados representam ${fmt(finSummary.revenue_alta)} em pipeline que o modelo considera com alta probabilidade de conversão.`
              : `Faltam ${Math.ceil((META2_ALTA - altaPct) * total)} negócios para atingir a meta`
            }
          </div>
          <ProgressBar value={meta2Pct} color={meta2Ok ? '#1D9E75' : '#F0A500'} height={8} />
          <div style={{ fontSize: 11, color: '#8B8FA8', marginTop: 5, textAlign: 'right' }}>
            {meta2Pct.toFixed(0)}% da meta
          </div>
        </div>
      </SectionCard>

      {/* BLOCO 3 — O que precisa ser feito agora? */}
      <SectionCard title="O que precisa ser feito agora?">
        {/* Ação 1 — account nulo */}
        <div style={{
          background: '#2E1A00', border: '0.5px solid #F0A500',
          borderRadius: 10, padding: '14px 16px', marginBottom: 10,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#F0A500' }}>
              Campanha de Preenchimento de Conta
            </span>
            <span style={{
              fontSize: 11, background: '#F0A500', color: '#000',
              borderRadius: 4, padding: '2px 8px', fontWeight: 700,
            }}>
              IMPACTO ALTO
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6, marginBottom: 10 }}>
            68% do pipeline ativo não tem empresa vinculada.
            Isso bloqueia o Combo Agente × Setor — nossa variável
            mais poderosa (diferença de 61 pontos percentuais
            de conversão entre deals com e sem setor identificado).
          </div>
          <div style={{ fontSize: 11, color: '#F0A500', fontWeight: 600 }}>
            → Próximo passo: notificar os {Math.round(alertCount + total * 0.3)} responsáveis com deals sem conta vinculada.
          </div>
        </div>

        {/* Ação 2 — modelo */}
        <div style={{
          background: '#0F1F3D', border: '0.5px solid #4F8EF7',
          borderRadius: 10, padding: '14px 16px', marginBottom: 10,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#4F8EF7' }}>
              Recalibração do Modelo
            </span>
            <span style={{
              fontSize: 11, background: '#4F8EF7', color: '#fff',
              borderRadius: 4, padding: '2px 8px', fontWeight: 700,
            }}>
              PLANEJADO
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6, marginBottom: 10 }}>
            O modelo foi treinado com dados históricos.
            Em produção, retreinar mensalmente com os novos
            fechamentos garante que o scorer aprende com os
            padrões mais recentes do time.
          </div>
          <div style={{ fontSize: 11, color: '#4F8EF7', fontWeight: 600 }}>
            → Frequência recomendada: mensal. Comando: <code style={{ background: '#0A0E1A', padding: '1px 6px', borderRadius: 4 }}>python api/train.py</code>
          </div>
        </div>

        {/* Ação 3 — redistribuições */}
        {redistImpact > 0 && (
          <div style={{
            background: '#0D2E22', border: '0.5px solid #1D9E75',
            borderRadius: 10, padding: '14px 16px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#1D9E75' }}>
                Realocações de Carteira Pendentes
              </span>
              <span style={{
                fontSize: 11, background: '#1D9E75', color: '#fff',
                borderRadius: 4, padding: '2px 8px', fontWeight: 700,
              }}>
                {fmt(redistImpact)} POTENCIAL
              </span>
            </div>
            <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6, marginBottom: 10 }}>
              O modelo identificou negócios com agentes que têm
              histórico fraco no produto. Redistribuir para agentes
              com histórico forte pode aumentar o valor esperado
              do pipeline.
            </div>
            <div style={{ fontSize: 11, color: '#1D9E75', fontWeight: 600 }}>
              → Ver detalhes: painel do Gerente → Realocações Sugeridas
            </div>
          </div>
        )}
      </SectionCard>

      {/* BLOCO 4 — Saúde do Sistema + Pauta de Ação */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <SectionCard title={`Saúde do Sistema de Análise — ${healthScore}%`}>
          {healthItems.map((item, i) => (
            <div key={item.label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '9px 0', borderTop: i > 0 ? '0.5px solid #2A2D3E' : 'none',
              fontSize: 13,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 14 }}>{item.ok ? '✅' : '❌'}</span>
                <span style={{ color: '#8B8FA8' }}>{item.label}</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontWeight: 600, color: item.ok ? '#1D9E75' : '#E24B4A' }}>
                  {item.value}
                </span>
                <span style={{ fontSize: 11, color: '#555870', marginLeft: 8 }}>
                  meta {item.target}
                </span>
              </div>
            </div>
          ))}
          <div style={{ marginTop: 14 }}>
            <ProgressBar value={healthScore} color={healthColor} height={8} />
          </div>

          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '0.5px solid #2A2D3E' }}>
            <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.7 }}>
              <p style={{ marginBottom: 6 }}>
                <strong style={{ color: '#E8E9ED' }}>Cobertura:</strong>{' '}
                {(coveragePct * 100).toFixed(1)}% dos negócios estão sendo analisados pelo modelo.
              </p>
              <p style={{ marginBottom: 6 }}>
                <strong style={{ color: '#E8E9ED' }}>Precisão:</strong>{' '}
                O modelo prevê conversões com ~65% de acerto (baseline: 63% sem modelo).
              </p>
              <p style={{ marginBottom: 6 }}>
                <strong style={{ color: '#E8E9ED' }}>Sem dados:</strong>{' '}
                {alertCount} negócios não têm histórico suficiente — responsáveis notificados.
              </p>
              <p>
                <strong style={{ color: '#F0A500' }}>Principal limitação:</strong>{' '}
                68% dos negócios ativos não têm empresa vinculada no CRM — isso impede a análise de setor, nossa variável mais discriminante (gap de 61 pontos percentuais de conversão).
              </p>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Pauta de Ação por Faixa">
          {ACTION_CARDS.map(card => (
            <div
              key={card.label}
              style={{
                background: card.bg,
                border: `0.5px solid ${card.color}`,
                borderRadius: 10,
                padding: '14px 16px',
                marginBottom: 10,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 14,
              }}
            >
              <div style={{
                width: 40, height: 40, borderRadius: 8,
                background: card.color + '22',
                border: `1px solid ${card.color}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, color: card.color, fontWeight: 800,
                flexShrink: 0,
              }}>
                {card.icon}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  alignItems: 'flex-start', marginBottom: 6,
                }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: card.color, letterSpacing: '0.06em' }}>
                    {card.label}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#E8E9ED', whiteSpace: 'nowrap', marginLeft: 8 }}>
                    {card.count} · {fmt(card.value)}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#8B8FA8', lineHeight: 1.6 }}>
                  {card.action}
                </div>
              </div>
            </div>
          ))}

          {/* Gap de performance */}
          <div style={{ marginTop: 6, paddingTop: 14, borderTop: '0.5px solid #2A2D3E' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#555870', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              Gap de Performance Identificado
            </div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#F0A500', marginBottom: 4 }}>
              {fmt(finSummary.gap_performance ?? 390637)}
            </div>
            <div style={{ fontSize: 12, color: '#8B8FA8' }}>
              Diferença entre receita atual e potencial máximo com modelo otimizado
            </div>
          </div>
        </SectionCard>
      </div>

      <CopilotPanel suggestions={copilotSuggestions} />
    </div>
  )
}
