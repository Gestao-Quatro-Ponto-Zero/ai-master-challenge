import { useDealScoring } from '@/hooks/useDealScoring';
import { useAccountScoring } from '@/hooks/useAccountScoring';
import { getTierInfo } from '@/utils/tiers';
import type { PipelineOpportunity, Account, Product, DealScore } from '@/types';
import { LeadCard } from '@/components/composite';
import { Card, Stat, Button, Badge } from '@/components/ui';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DashboardPageProps {
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
  onSelectDeal?: (deal: DealScore) => void;
}

export function DashboardPage({
  pipeline,
  accounts,
  products,
  onSelectDeal,
}: DashboardPageProps) {
  // V2 Model: 4-pillar architecture (no salesTeams parameter needed)
  const dealScores = useDealScoring(pipeline, accounts, products);
  const accountScores = useAccountScoring(pipeline, accounts, products);

  // Filter active deals
  const activeDeals = dealScores.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  );

  // Get HOT leads (top priority for action)
  const hotDeals = dealScores
    .filter((d) => d.tier === 'HOT')
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  // If not enough HOT deals, fill with WARM
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

  // Count by tier
  const tierCounts = {
    HOT: dealScores.filter((d) => d.tier === 'HOT').length,
    WARM: dealScores.filter((d) => d.tier === 'WARM').length,
    COOL: dealScores.filter((d) => d.tier === 'COOL').length,
    COLD: dealScores.filter((d) => d.tier === 'COLD').length,
  };

  // Calculate metrics
  const wonDeals = pipeline.filter((d) => d.deal_stage === 'Won');
  const lostDeals = pipeline.filter((d) => d.deal_stage === 'Lost');
  const globalWinRate =
    wonDeals.length + lostDeals.length > 0
      ? wonDeals.length / (wonDeals.length + lostDeals.length)
      : 0;

  const pipelineValue = wonDeals.reduce((sum, d) => sum + d.close_value, 0);

  // Prepare chart data
  const tierChartData = [
    { name: 'HOT', value: tierCounts.HOT, fill: '#dc2626' },
    { name: 'WARM', value: tierCounts.WARM, fill: '#eab308' },
    { name: 'COOL', value: tierCounts.COOL, fill: '#3b82f6' },
    { name: 'COLD', value: tierCounts.COLD, fill: '#64748b' },
  ];

  const topDeals = dealScores.slice(0, 10);
  const topDealsChartData = topDeals.map((d) => ({
    name: d.product.substring(0, 15),
    score: d.score,
  }));

  return (
    <div className="space-y-10">
      {/* TOP 5 HOT LEADS SECTION - MAIN FOCUS */}
      <section>
        <div className="mb-8 flex items-end justify-between border-b border-hubspot-gray-200 pb-4">
          <div>
            <h2 className="text-3xl font-bold text-hubspot-black tracking-tight flex items-center gap-3">
              🔥 Seus Leads Hot
            </h2>
            <p className="text-hubspot-dark/50 font-medium mt-1">
              Top prioritized opportunities awaiting your immediate action.
            </p>
          </div>
          <div className="text-right">
            <span className="text-4xl font-bold text-hubspot-orange">{topPriorityDeals.length}</span>
            <span className="text-xs font-bold text-hubspot-dark/40 uppercase tracking-widest block">Ativos agora</span>
          </div>
        </div>

        {topPriorityDeals.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
            {topPriorityDeals.map((deal) => (
              <LeadCard
                key={deal.opportunity_id}
                deal={deal}
                onView={onSelectDeal}
              />
            ))}
          </div>
        ) : (
          <Card padding="lg" className="text-center py-16 bg-hubspot-gray-100/50 border-dashed">
            <p className="text-hubspot-dark/40 font-bold uppercase tracking-widest text-sm">
              Nenhum lead HOT no momento. Verifique os leads WARM! 🌤️
            </p>
          </Card>
        )}
      </section>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Stat
          label="Deals Ativos"
          value={activeDeals.length}
          subtitle={`${((activeDeals.length / dealScores.length) * 100).toFixed(0)}% do volume total`}
          icon="📊"
        />

        <Stat
          label="Prioridade Máxima"
          value={tierCounts.HOT}
          subtitle="Aguardando contato"
          highlight
          icon="🔥"
        />

        <Stat
          label="Taxa de Conversão"
          value={`${(globalWinRate * 100).toFixed(1)}%`}
          subtitle={`${wonDeals.length} ganhos / ${lostDeals.length} perdidos`}
          icon="🏆"
        />

        <Stat
          label="Pipeline Total"
          value={`$${(pipelineValue / 1000000).toFixed(1)}M`}
          subtitle="Receita projetada (Won)"
          icon="💰"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tier Distribution */}
        <Card className="lg:col-span-1 shadow-sm overflow-hidden border-t-4 border-t-hubspot-orange">
          <div className="p-6 border-b border-hubspot-gray-100 flex justify-between items-center bg-hubspot-gray-100/20">
            <h3 className="font-bold text-hubspot-black uppercase tracking-widest text-xs">Distribuição de Tiers</h3>
            <Badge tier="HOT" />
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={tierChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                >
                  {tierChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-6 space-y-3">
              {tierChartData.map((tier) => (
                <div key={tier.name} className="flex items-center justify-between group cursor-default">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-2.5 h-2.5 rounded-full ring-2 ring-offset-2 ring-transparent group-hover:ring-current transition-all"
                      style={{ backgroundColor: tier.fill, color: tier.fill }}
                    />
                    <span className="text-sm font-bold text-hubspot-dark/60 group-hover:text-hubspot-black transition-colors uppercase tracking-widest">
                      {tier.name}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-hubspot-black">{tier.value}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Top 10 Deals */}
        <Card className="lg:col-span-2 shadow-sm border-t-4 border-t-hubspot-dark">
          <div className="p-6 border-b border-hubspot-gray-100 flex justify-between items-center bg-hubspot-gray-100/20">
            <h3 className="font-bold text-hubspot-black uppercase tracking-widest text-xs">Top 10 Oportunidades por Score</h3>
            <span className="text-[10px] font-bold text-hubspot-dark/40 uppercase tracking-widest">Tempo Real</span>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={380}>
              <BarChart
                data={topDealsChartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" horizontal={false} />
                <XAxis type="number" hide />
                <Tooltip
                  cursor={{ fill: '#F3F4F6' }}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold' }}
                />
                <Bar
                  dataKey="score"
                  fill="#FF5630"
                  radius={[0, 4, 4, 0]}
                  barSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Account Statistics */}
      <section>
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-xl font-bold text-hubspot-black tracking-tight">Top 5 Contas Estratégicas</h3>
          <Button variant="link" size="sm">Ver todas as contas →</Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {accountScores.slice(0, 5).map((account) => {
            const tierInfo = getTierInfo(account.tier);
            return (
              <Card
                key={account.account}
                padding="md"
                variant="interactive"
                className="bg-white border-hubspot-gray-200"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 bg-hubspot-gray-100 rounded-hb">🏢</div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-hubspot-black leading-none">{account.score}</p>
                    <p className="text-[10px] font-bold text-hubspot-dark/40 uppercase tracking-tighter mt-1">{tierInfo.badge}</p>
                  </div>
                </div>
                <div>
                  <p className="font-bold text-hubspot-black truncate">{account.account}</p>
                  <div className="mt-2 pt-2 border-t border-hubspot-gray-100 flex justify-between items-center text-[10px] font-bold text-hubspot-dark/40 uppercase tracking-widest">
                    <span>Win Rate: {(account.win_rate * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
