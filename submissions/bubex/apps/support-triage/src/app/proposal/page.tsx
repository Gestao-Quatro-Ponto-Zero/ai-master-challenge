import { Suspense } from 'react'
import { getOverview, getBottlenecks, getChannelStats, getTypeStats } from '@/lib/queries'
import { ProposalDiagnosis, ProposalDiagnosisSkeleton } from '@/components/ProposalDiagnosis'

export default async function ProposalPage() {
  const [overview, bottlenecks, channelStats, typeStats] = await Promise.all([
    getOverview(),
    getBottlenecks(),
    getChannelStats(),
    getTypeStats(),
  ])

  return (
    <div className="space-y-10 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Proposta de Automação</h1>
        <p className="text-gray-500 text-sm mt-1">Baseada nos dados reais do diagnóstico operacional.</p>
      </div>

      {/* Diagnóstico resumido — gerado por IA sobre os dados reais */}
      <Suspense fallback={<ProposalDiagnosisSkeleton />}>
        <ProposalDiagnosis
          overview={overview}
          bottlenecks={bottlenecks}
          channelStats={channelStats}
          typeStats={typeStats}
        />
      </Suspense>

      {/* Fluxo proposto */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Fluxo proposto com IA</h2>
        <div className="space-y-1 text-sm">
          {[
            { step: '1', label: 'Ticket entra', detail: 'Via qualquer canal (email, chat, telefone, social)' },
            { step: '2', label: 'IA classifica e prioriza', detail: 'Categoria, prioridade sugerida e flag de automação — automático, sem agente', ai: true },
            { step: '3a', label: 'FAQ / status / pedido simples?', detail: 'IA sugere resposta baseada em tickets anteriores resolvidos → agente aprova em 1 clique', ai: true },
            { step: '3b', label: 'Técnico / emocional / complexo?', detail: 'Roteado para especialista com contexto completo já preenchido pela IA', ai: false },
            { step: '4', label: 'Resolução', detail: 'IA sugere texto de fechamento baseado na resolução → agente edita e assina', ai: true },
            { step: '5', label: 'CSAT coletado', detail: 'Feedback automaticamente vinculado ao tipo de ticket e canal para análise contínua', ai: true },
          ].map(s => (
            <div key={s.step} className="flex gap-3 items-start py-2 border-b border-gray-100 last:border-0">
              <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {s.step}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-800">{s.label}</span>
                  {s.ai === true && (
                    <span className="text-xs bg-blue-50 text-blue-600 border border-blue-200 px-2 py-0.5 rounded-full">IA</span>
                  )}
                </div>
                <p className="text-gray-500 text-xs mt-0.5">{s.detail}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 italic mt-2">
          Regra de ouro: <strong>IA sugere, humano decide e assina.</strong> Nenhuma resposta ao cliente é enviada sem aprovação humana.
        </p>
      </section>

      {/* O que automatizar / não */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">O que automatizar — e o que não</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          <div>
            <p className="text-sm font-semibold text-green-700 mb-2">Automatizar</p>
            <div className="space-y-2">
              {[
                ['Classificação e roteamento', 'Volume alto, critério claro, erro tem baixo custo imediato'],
                ['Triagem de prioridade inicial', 'Urgência pode ser detectada por palavras-chave + LLM'],
                ['Resposta para FAQ de status', 'Perguntas sobre pedidos/billing têm estrutura previsível'],
                ['Sugestão de resposta de fechamento', 'Baseada em resoluções anteriores similares'],
                ['Detecção de duplicatas', 'Comparação semântica entre tickets abertos do mesmo cliente'],
              ].map(([title, reason]) => (
                <div key={title} className="bg-green-50 rounded-lg p-3">
                  <p className="text-sm font-medium text-green-800">{title}</p>
                  <p className="text-xs text-green-600 mt-0.5">{reason}</p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-red-700 mb-2">NÃO automatizar</p>
            <div className="space-y-2">
              {[
                ['Tickets com carga emocional alta', 'Frustração e raiva exigem empatia humana — IA piora o atendimento'],
                ['Escalações e reclamações formais', 'Risco legal e reputacional alto demais para delegação total'],
                ['Problemas técnicos sem precedente', 'Sem base de conhecimento, LLM pode alucinar a solução'],
                ['Resposta final ao cliente', 'IA sugere, mas humano sempre revisa antes de enviar'],
                ['Decisões de cancelamento/reembolso', 'Impacto financeiro direto — requer autorização humana'],
              ].map(([title, reason]) => (
                <div key={title} className="bg-red-50 rounded-lg p-3">
                  <p className="text-sm font-medium text-red-800">{title}</p>
                  <p className="text-xs text-red-600 mt-0.5">{reason}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ROI estimado */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">ROI estimado</h2>
        <div className="space-y-3 text-sm text-gray-700">
          <p>
            <strong>Premissa:</strong> automação de classificação e roteamento reduz o tempo médio de resolução
            em 20% nos tickets automatizáveis (estimativa conservadora baseada em benchmarks de mercado).
          </p>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Tickets fechados/mês (extrapolado)</span>
              <span className="font-semibold">~{Math.round(overview.closedTickets * 4).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tempo médio de resolução atual</span>
              <span className="font-semibold">{overview.avgResolutionHours}h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Redução estimada com automação (20%)</span>
              <span className="font-semibold text-green-700">-{(overview.avgResolutionHours * 0.2).toFixed(1)}h por ticket</span>
            </div>
            <div className="flex justify-between border-t border-gray-200 pt-2">
              <span className="text-gray-600">Horas economizadas/mês</span>
              <span className="font-bold text-green-700">
                ~{Math.round(overview.closedTickets * 4 * overview.avgResolutionHours * 0.2).toLocaleString()}h
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Custo estimado (R$35/h · agente CLT pleno)</span>
              <span className="font-bold text-green-700">
                R${Math.round(overview.closedTickets * 4 * overview.avgResolutionHours * 0.2 * 35).toLocaleString()}/mês
              </span>
            </div>
          </div>
          <p className="text-xs text-gray-400 italic">
            Premissas documentadas: R$35/h (custo médio agente CLT), 20% de redução conservadora,
            volume extrapolado do dataset de amostra. Validar com dados de produção reais.
          </p>
        </div>
      </section>

      {/* Limitações */}
      <section className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-2">
        <h2 className="text-sm font-semibold text-amber-800 uppercase tracking-wide">Limitações honestas</h2>
        <ul className="text-sm text-amber-700 space-y-1 list-disc list-inside">
          <li>O dataset é sintético — as descrições contêm placeholders não substituídos, reduzindo a qualidade do texto para NLP.</li>
          <li>Todos os timestamps estão agrupados em 2023-06-01 — impossível analisar sazonalidade ou tendência temporal.</li>
          <li>CSAT é uniformemente distribuído (média 3.0 em todos os segmentos) — em dados reais, a variação seria maior e mais reveladora.</li>
          <li>ROI estimado não considera custo de implementação, treinamento da equipe ou manutenção do modelo.</li>
          <li>O classificador não foi treinado especificamente no Dataset 1 — usa Dataset 2 (IT tickets) como referência conceitual.</li>
        </ul>
      </section>
    </div>
  )
}
