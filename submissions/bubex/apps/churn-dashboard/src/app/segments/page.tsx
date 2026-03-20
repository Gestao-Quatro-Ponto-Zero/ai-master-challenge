import { getAnalysisOutput } from '@/lib/analysis-output'
import { getOverview } from '@/lib/queries'
import { SegmentsTable } from '@/components/SegmentsTable'

export default async function SegmentsPage() {
  const [overview, analysis] = await Promise.all([
    getOverview(),
    Promise.resolve(getAnalysisOutput()),
  ])

  const atRisk = analysis?.atRiskAccounts ?? []

  // Risk distribution
  const highRisk   = atRisk.filter(a => a.riskScore >= 70)
  const mediumRisk = atRisk.filter(a => a.riskScore >= 40 && a.riskScore < 70)
  const lowRisk    = atRisk.filter(a => a.riskScore < 40)

  // MRR at risk
  const mrrAtRisk = atRisk.filter(a => a.riskScore >= 40).reduce((sum, a) => sum + a.mrr, 0)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Contas em Risco</h1>
        <p className="text-gray-500 text-sm mt-1">
          Contas retidas com sinais de churn iminente · {overview.totalAccounts - overview.churnedAccounts} contas ativas analisadas
        </p>
      </div>

      {!analysis && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-sm text-yellow-800">
          <span className="font-semibold">Análise Python não encontrada.</span>{' '}
          Execute <code className="bg-yellow-100 px-1 rounded">python scripts/generate_analysis.py</code> para calcular os scores de risco.
        </div>
      )}

      {/* Risk summary KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
          <p className="text-xs text-red-400 uppercase tracking-wide mb-1">Risco Alto (≥70)</p>
          <p className="text-2xl font-bold text-red-700">{highRisk.length}</p>
          <p className="text-xs text-red-400 mt-0.5">contas</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-4">
          <p className="text-xs text-yellow-500 uppercase tracking-wide mb-1">Risco Médio (40-69)</p>
          <p className="text-2xl font-bold text-yellow-700">{mediumRisk.length}</p>
          <p className="text-xs text-yellow-400 mt-0.5">contas</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl px-5 py-4">
          <p className="text-xs text-green-500 uppercase tracking-wide mb-1">Risco Baixo (&lt;40)</p>
          <p className="text-2xl font-bold text-green-700">{lowRisk.length}</p>
          <p className="text-xs text-green-400 mt-0.5">contas</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">MRR em Risco (≥40)</p>
          <p className="text-2xl font-bold text-amber-600">${mrrAtRisk.toLocaleString()}</p>
          <p className="text-xs text-gray-400 mt-0.5">potencial de churn</p>
        </div>
      </div>

      {/* Risk methodology */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-800">
        <span className="font-semibold">Metodologia do Risk Score:</span>{' '}
        Baixo uso de features (+30), conta trial (+20), downgrade recente (+20),
        alto volume de tickets (+15), tickets escalados (+10), plano Basic (+5).
        Máximo: 100 pontos. Apenas contas retidas são incluídas.
      </div>

      {/* Table */}
      {atRisk.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Lista de Contas em Risco
          </h2>
          <SegmentsTable accounts={atRisk} />
        </div>
      ) : (
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
          Nenhum dado disponível. Execute o script Python para gerar os scores de risco.
        </div>
      )}
    </div>
  )
}
