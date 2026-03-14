import { useSPINReports } from '@/hooks/useSPINGenerator';
import { Card, Badge, Stat } from '@/components/ui';
import { SPINSection } from '@/components/composite';
import { ScorerExplicabilityDashboard } from '@/components/dashboard/ScorerExplicabilityDashboard';
import type { PipelineOpportunity, Account, Product, DealScore } from '@/types';

interface DealDetailPageProps {
  deal: DealScore;
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
}

export function DealDetailPage({
  deal,
  pipeline,
  accounts,
  products,
}: DealDetailPageProps) {
  const { reports } = useSPINReports([deal], pipeline, accounts, products);
  const report = reports[0];

  if (!report) {
    return (
      <Card padding="lg">
        <p className="text-slate-400">Erro ao carregar detalhes do deal.</p>
      </Card>
    );
  }

  const daysInPipeline = Math.floor(
    (new Date().getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header Card */}
      <Card padding="lg" className="border-t-4 border-t-hubspot-orange shadow-lg overflow-hidden">
        <div className="flex flex-col md:flex-row justify-between items-start gap-8">
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-4">
              <h1 className="text-4xl font-extrabold text-hubspot-black tracking-tight">
                {report.context.accountName || 'Prospect'}
              </h1>
              <Badge tier={deal.tier} />
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm font-bold text-hubspot-dark/50 uppercase tracking-widest">
              <span className="flex items-center gap-1">🏢 {report.context.sector}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-hubspot-gray-200" />
              <span className="flex items-center gap-1">📦 {deal.product}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-hubspot-gray-200" />
              <span className="flex items-center gap-1">🔄 {deal.deal_stage}</span>
            </div>
          </div>
          <div className="bg-hubspot-gray-100 p-6 rounded-2xl border border-hubspot-gray-200 text-center min-w-[160px]">
            <div className="text-sm font-black text-hubspot-dark/40 uppercase tracking-tighter mb-1">Score Lead</div>
            <div className="text-6xl font-black text-hubspot-orange tracking-tighter">
              {deal.score}
            </div>
            <div className="text-[10px] font-bold text-hubspot-dark/60 mt-2 uppercase tracking-widest border-t border-hubspot-gray-200 pt-2">
              Qualificação Final
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-10 pt-8 border-t border-hubspot-gray-100">
          {report.context.employees && (
            <Stat
              label="Tamanho da Empresa"
              value={report.context.employees.toLocaleString()}
              icon="👥"
              subtitle="Colaboradores"
            />
          )}
          {report.context.winRate !== undefined && (
            <Stat
              label="Taxa Histórica"
              value={`${((report.context.winRate ?? 0) * 100).toFixed(0)}%`}
              icon="📈"
              subtitle="Win Rate na Conta"
            />
          )}
          {report.context.avgTicket && (
            <Stat
              label="Ticket Médio"
              value={`$${(report.context.avgTicket ?? 0).toFixed(0)}`}
              icon="💰"
              subtitle="Investimento Previsto"
            />
          )}
          <Stat
            label="Tempo do Deal"
            value={`${daysInPipeline} dias`}
            icon="⏱️"
            subtitle="No Pipeline Atual"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Why This Score? - Using Explicability Dashboard */}
        <div className="lg:col-span-1 space-y-8">
          <section>
            <ScorerExplicabilityDashboard
              deal={deal}
              showDetailed={true}
            />
          </section>

          {/* Deal History */}
          {report.context.totalDeals && report.context.totalDeals > 0 && (
            <section>
              <h2 className="text-xl font-bold text-hubspot-black mb-4 flex items-center gap-2 uppercase tracking-tight">
                📜 Histórico da Conta
              </h2>
              <div className="space-y-3">
                {/* Won deals */}
                {report.context.wonDeals && report.context.wonDeals > 0 && (
                  <Card variant="default" padding="md" className="bg-green-50/50 border-green-200">
                    <p className="text-sm font-bold text-green-800 flex items-center gap-2">
                      <span className="text-lg">✅</span> {report.context.wonDeals} deals Won
                    </p>
                    <p className="text-[10px] font-bold text-green-600/70 uppercase tracking-widest mt-1">
                      Receita Acumulada: ${pipeline.filter(d => d.account === report.context.accountName && d.deal_stage === 'Won').reduce((sum, d) => sum + d.close_value, 0).toFixed(0)}
                    </p>
                  </Card>
                )}
                {/* Lost deals */}
                {report.context.lostDeals && report.context.lostDeals > 0 && (
                  <Card variant="default" padding="md" className="bg-red-50/50 border-red-200">
                    <p className="text-sm font-bold text-red-800 flex items-center gap-2">
                      <span className="text-lg">❌</span> {report.context.lostDeals} deals Lost
                    </p>
                    <p className="text-[10px] font-bold text-red-600/70 uppercase tracking-widest mt-1">
                      Oportunidade Perdida: ${report.context.lostRevenue?.toFixed(0) || '0'}
                    </p>
                  </Card>
                )}
              </div>
            </section>
          )}
        </div>

        {/* SPIN Script - HIGHLIGHTED SECTION */}
        <div className="lg:col-span-2 space-y-8">
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-hubspot-black uppercase tracking-tight flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-hubspot-orange text-white flex items-center justify-center text-sm italic">S</span>
                Script Estratégico SPIN
              </h2>
              <Badge tier="HOT" />
            </div>

            <Card padding="lg" className="border-2 border-hubspot-orange shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <span className="text-8xl font-black">SPIN</span>
              </div>
              <div className="relative z-10">
                <SPINSection
                  script={report.spin_script}
                  accountName={report.context.accountName}
                />
              </div>
            </Card>
          </section>

          {/* Next Steps */}
          <section>
            <h2 className="text-xl font-bold text-hubspot-black mb-4 uppercase tracking-tight">
              📋 Próximas Ações Recomendadas
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Ligar agora', icon: '📞', color: 'hover:border-hubspot-orange hover:text-hubspot-orange' },
                { label: 'Enviar email', icon: '📧', color: 'hover:border-blue-500 hover:text-blue-500' },
                { label: 'Nota interna', icon: '📝', color: 'hover:border-yellow-500 hover:text-yellow-500' },
                { label: 'Status deal', icon: '🔄', color: 'hover:border-green-500 hover:text-green-500' }
              ].map((action) => (
                <button
                  key={action.label}
                  className={`flex flex-col items-center justify-center gap-3 p-6 bg-white border-2 border-hubspot-gray-100 rounded-2xl transition-all duration-200 group shadow-sm active:scale-95 ${action.color}`}
                >
                  <span className="text-3xl group-hover:scale-110 transition-transform">{action.icon}</span>
                  <span className="text-[10px] font-black uppercase tracking-widest">{action.label}</span>
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
