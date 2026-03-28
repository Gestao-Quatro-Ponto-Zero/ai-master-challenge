import { useDealScoring } from '@/hooks/useDealScoring';
import { useAccountScoring } from '@/hooks/useAccountScoring';
import type { PipelineOpportunity, Account, Product, DealScore, SalesTeam } from '@/types';
import { LeadCard } from '@/components/composite';
import { Card, Badge } from '@/components/ui';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface DashboardPageProps {
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
  onSelectDeal?: (deal: DealScore) => void;
  salesTeams?: SalesTeam[];
}

export function DashboardPageNew({
  pipeline,
  accounts,
  products,
  onSelectDeal,
  salesTeams,
}: DashboardPageProps) {
  // V2 Model: 4-pillar architecture with enriched data for filtering
  const dealScores = useDealScoring(pipeline, accounts, products, salesTeams);
  const accountScores = useAccountScoring(pipeline, accounts, products);

  // Filter active deals
  const activeDeals = dealScores.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  );

  // Get HOT leads
  const hotDeals = dealScores
    .filter((d) => d.tier === 'HOT')
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  const topPriorityDeals =
    hotDeals.length < 5
      ? [
        ...hotDeals,
        ...dealScores
          .filter((d) => d.tier === 'WARM')
          .sort((a, b) => b.score - a.score)
          .slice(0, 5 - hotDeals.length),
      ]
      : hotDeals;

  // Metrics
  const tierCounts = {
    HOT: dealScores.filter((d) => d.tier === 'HOT').length,
    WARM: dealScores.filter((d) => d.tier === 'WARM').length,
    COOL: dealScores.filter((d) => d.tier === 'COOL').length,
    COLD: dealScores.filter((d) => d.tier === 'COLD').length,
  };

  const wonDeals = pipeline.filter((d) => d.deal_stage === 'Won');
  const lostDeals = pipeline.filter((d) => d.deal_stage === 'Lost');
  const globalWinRate =
    wonDeals.length + lostDeals.length > 0
      ? wonDeals.length / (wonDeals.length + lostDeals.length)
      : 0;

  const pipelineValue = wonDeals.reduce((sum, d) => sum + d.close_value, 0);

  // Chart data
  const tierChartData = [
    { name: 'HOT', value: tierCounts.HOT, fill: '#dc2626' },
    { name: 'WARM', value: tierCounts.WARM, fill: '#f59e0b' },
    { name: 'COOL', value: tierCounts.COOL, fill: '#3b82f6' },
    { name: 'COLD', value: tierCounts.COLD, fill: '#9ca3af' },
  ];

  const topDeals = dealScores.slice(0, 10);
  const topDealsChartData = topDeals.map((d) => ({
    name: d.product.substring(0, 12),
    score: d.score,
  }));

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="rounded-3xl bg-hubspot-black p-12 text-white shadow-2xl border-b-8 border-hubspot-orange overflow-hidden relative group">
        <div className="absolute -right-20 -top-20 w-64 h-64 bg-hubspot-orange/10 rounded-full blur-3xl group-hover:bg-hubspot-orange/20 transition-all duration-700" />
        <div className="flex justify-between items-center relative z-10">
          <div>
            <h2 className="text-5xl font-black mb-4 tracking-tighter uppercase">Bem-vindo de volta! 👋</h2>
            <p className="text-white/60 text-xl font-bold uppercase tracking-[0.2em]">
              Você tem <span className="text-hubspot-orange">{topPriorityDeals.length}</span> leads HOT prontos para ação
            </p>
          </div>
          <div className="text-right border-l-4 border-hubspot-orange pl-10 py-2">
            <div className="text-7xl font-black text-white tracking-tighter">
              {dealScores.length}
            </div>
            <p className="text-white/40 text-[10px] font-black mt-2 uppercase tracking-[0.3em]">Deals em pipeline</p>
          </div>
        </div>
      </div>

      {/* TOP PRIORITY LEADS */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <h3 className="text-2xl font-bold text-slate-900">
            🔥 Seus Leads Prioritários
          </h3>
          <span className="inline-flex items-center px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-semibold">
            {topPriorityDeals.length} em foco
          </span>
        </div>

        {topPriorityDeals.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {topPriorityDeals.map((deal) => (
              <LeadCard
                key={deal.opportunity_id}
                deal={deal}
                onView={onSelectDeal}
              />
            ))}
          </div>
        ) : (
          <Card padding="lg" className="bg-blue-50 border-blue-200 text-center py-12">
            <p className="text-slate-600 text-lg">
              Nenhum lead HOT no momento. Veja os leads WARM! 🌤️
            </p>
          </Card>
        )}
      </div>

      {/* KEY METRICS - 4 COLUMN GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Deals Ativos</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {activeDeals.length}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {((activeDeals.length / dealScores.length) * 100).toFixed(0)}% do total
              </p>
            </div>
            <div className="text-4xl">📊</div>
          </div>
        </div>

        <div className="rounded-xl bg-white border border-red-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Leads HOT</p>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {tierCounts.HOT}
              </p>
              <p className="text-xs text-slate-500 mt-2">Prioridade máxima</p>
            </div>
            <div className="text-4xl">🔥</div>
          </div>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Win Rate</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {(globalWinRate * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {wonDeals.length}W / {lostDeals.length}L
              </p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Pipeline Value</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                ${(pipelineValue / 1000000).toFixed(1)}M
              </p>
              <p className="text-xs text-slate-500 mt-2">Receita Won</p>
            </div>
            <div className="text-4xl">💰</div>
          </div>
        </div>
      </div>

      {/* CHARTS SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tier Distribution */}
        <Card variant="default" padding="lg" className="border-slate-200 bg-white">
          <h3 className="text-lg font-bold text-slate-900 mb-6">
            Distribuição por Tier
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={tierChartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {tierChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
            {tierChartData.map((tier) => (
              <div key={tier.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: tier.fill }}
                />
                <span className="text-slate-700">
                  <span className="font-semibold">{tier.name}</span>: {tier.value}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Top 10 Deals */}
        <Card variant="default" padding="lg" className="border-slate-200 bg-white">
          <h3 className="text-lg font-bold text-slate-900 mb-6">
            Top 10 Deals por Score
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={topDealsChartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 150 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e5e7eb"
                vertical={false}
              />
              <XAxis type="number" stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="score" fill="#3b82f6" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* TOP ACCOUNTS */}
      <Card variant="default" padding="lg" className="border-slate-200 bg-white">
        <h3 className="text-lg font-bold text-slate-900 mb-6">
          Top 5 Contas por Score
        </h3>
        <div className="space-y-3">
          {accountScores.slice(0, 5).map((account, idx) => (
            <div
              key={account.account}
              className="flex items-center justify-between p-4 rounded-lg hover:bg-slate-50 transition-colors border border-slate-200"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <span className="text-lg">{idx + 1}</span>
                </div>
                <div>
                  <p className="font-bold text-slate-900">{account.account}</p>
                  <p className="text-xs text-slate-600 mt-1">
                    {account.deals_summary.won}W / {account.deals_summary.lost}L •{' '}
                    {(account.win_rate * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-600">
                  {account.score}
                </p>
                <Badge tier={account.tier} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
