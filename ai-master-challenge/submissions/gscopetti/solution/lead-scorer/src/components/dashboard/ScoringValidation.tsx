import { useDataContext } from '@/context/DataContext';
import { useDealScoring } from '@/hooks/useDealScoring';
import { useAccountScoring } from '@/hooks/useAccountScoring';
import { getTierInfo } from '@/utils/tiers';
import { SPINScriptViewer } from '@/components/spin/SPINScriptViewer';

export function ScoringValidation() {
  const { state } = useDataContext();
  const { accounts, products, pipeline } = state;

  // V2 Model: 4-pillar architecture
  const dealScores = useDealScoring(pipeline, accounts, products);
  const accountScores = useAccountScoring(pipeline, accounts, products);

  if (!state.isLoaded) {
    return null;
  }

  // Count by tier
  const dealsByTier = {
    HOT: dealScores.filter((d) => d.tier === 'HOT').length,
    WARM: dealScores.filter((d) => d.tier === 'WARM').length,
    COOL: dealScores.filter((d) => d.tier === 'COOL').length,
    COLD: dealScores.filter((d) => d.tier === 'COLD').length,
  };

  const accountsByTier = {
    HOT: accountScores.filter((a) => a.tier === 'HOT').length,
    WARM: accountScores.filter((a) => a.tier === 'WARM').length,
    COOL: accountScores.filter((a) => a.tier === 'COOL').length,
    COLD: accountScores.filter((a) => a.tier === 'COLD').length,
  };

  // Get top deals
  const topDeals = dealScores.slice(0, 5);
  const topAccounts = accountScores.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Deals Ativos</p>
          <p className="text-2xl font-bold text-white">{dealScores.length}</p>
        </div>
        <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Contas</p>
          <p className="text-2xl font-bold text-white">{accountScores.length}</p>
        </div>
        <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Win Rate Global</p>
          <p className="text-2xl font-bold text-white">
            {(
              (pipeline.filter((d) => d.deal_stage === 'Won').length /
                (pipeline.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost').length || 1)) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
        <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">Pipeline Value</p>
          <p className="text-2xl font-bold text-white">
            ${(
              pipeline.filter((d) => d.deal_stage === 'Won').reduce((sum, d) => sum + d.close_value, 0) / 1000000
            ).toFixed(1)}
            M
          </p>
        </div>
      </div>

      {/* Deal Tier Distribution */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-4">Distribuição de Deals por Tier</h3>
        <div className="grid grid-cols-4 gap-2">
          {(
            [
              { tier: 'HOT', count: dealsByTier.HOT },
              { tier: 'WARM', count: dealsByTier.WARM },
              { tier: 'COOL', count: dealsByTier.COOL },
              { tier: 'COLD', count: dealsByTier.COLD },
            ] as const
          ).map(({ tier, count }) => {
            const info = getTierInfo(tier);
            return (
              <div key={tier} className={`p-3 rounded-lg ${info.bgColor}`}>
                <p className="text-sm font-bold">{info.badge}</p>
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-xs mt-1">{((count / dealScores.length) * 100).toFixed(0)}%</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Account Tier Distribution */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-4">Distribuição de Contas por Tier</h3>
        <div className="grid grid-cols-4 gap-2">
          {(
            [
              { tier: 'HOT', count: accountsByTier.HOT },
              { tier: 'WARM', count: accountsByTier.WARM },
              { tier: 'COOL', count: accountsByTier.COOL },
              { tier: 'COLD', count: accountsByTier.COLD },
            ] as const
          ).map(({ tier, count }) => {
            const info = getTierInfo(tier);
            return (
              <div key={tier} className={`p-3 rounded-lg ${info.bgColor}`}>
                <p className="text-sm font-bold">{info.badge}</p>
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-xs mt-1">{((count / accountScores.length) * 100).toFixed(0)}%</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Deals */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-4">Top 5 Deals (por Score)</h3>
        <div className="space-y-2">
          {topDeals.map((deal) => {
            const info = getTierInfo(deal.tier);
            return (
              <div key={deal.opportunity_id} className="p-3 bg-slate-900 rounded-lg border border-slate-700 flex justify-between items-center">
                <div>
                  <p className="font-bold">
                    {deal.product} {info.badge}
                  </p>
                  <p className="text-xs text-slate-400">
                    {deal.account || '(sem account)'} • {deal.sales_agent}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{deal.score}</p>
                  <p className="text-xs text-slate-400">{deal.deal_stage}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Accounts */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-4">Top 5 Contas (por Score)</h3>
        <div className="space-y-2">
          {topAccounts.map((account) => {
            const info = getTierInfo(account.tier);
            return (
              <div key={account.account} className="p-3 bg-slate-900 rounded-lg border border-slate-700 flex justify-between items-center">
                <div>
                  <p className="font-bold">
                    {account.account} {info.badge}
                  </p>
                  <p className="text-xs text-slate-400">
                    {account.deals_summary.won}W / {account.deals_summary.lost}L • {(account.win_rate * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{account.score}</p>
                  <p className="text-xs text-slate-400">${(account.revenue_total / 1000).toFixed(0)}k revenue</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SPIN Scripts */}
      <div className="border-t border-slate-700 pt-6">
        <h2 className="text-2xl font-bold mb-4">📝 Scripts SPIN Selling</h2>
        <SPINScriptViewer
          dealScores={dealScores}
          pipeline={pipeline}
          accounts={accounts}
          products={products}
        />
      </div>

      {/* Console Logs */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-2">✅ Validação Concluída</h3>
        <p className="text-sm text-slate-300 mb-3">
          Todos os scores foram calculados e scripts SPIN gerados. Verifique o console do navegador para detalhes completos.
        </p>
        <button
          onClick={() => {
            console.log('=== DEAL SCORES (Top 10) ===', dealScores.slice(0, 10));
            console.log('=== ACCOUNT SCORES (Top 10) ===', accountScores.slice(0, 10));
            alert('✅ Scores logados no console. Abra DevTools (F12) para ver.');
          }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
        >
          📋 Ver Detalhes no Console
        </button>
      </div>
    </div>
  );
}
