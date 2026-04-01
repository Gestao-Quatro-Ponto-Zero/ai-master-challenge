import { useAccountScoring } from '@/hooks/useAccountScoring';
import { getTierInfo } from '@/utils/tiers';
import type { PipelineOpportunity, Account, Product } from '@/types';

interface AccountsPageProps {
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
}

export function AccountsPage({ pipeline, accounts, products }: AccountsPageProps) {
  const accountScores = useAccountScoring(pipeline, accounts, products);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="text-[10px] font-black text-hubspot-dark/40 uppercase tracking-[0.2em] ml-1">
        Análise de Contas Estratégicas ({accountScores.length} totais)
      </div>

      <div className="bg-white rounded-hb border-2 border-hubspot-gray-200 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-hubspot-gray-100 border-b-2 border-hubspot-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Score</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Tier</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Conta</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Setor</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Win Rate</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Deals</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Ticket Médio</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Volume (K)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hubspot-gray-100">
              {accountScores.map((account) => {
                const tierInfo = getTierInfo(account.tier);
                const accountData = accounts.find((a) => a.account === account.account);

                return (
                  <tr key={account.account} className="hover:bg-hubspot-gray-100/50 transition-colors group">
                    <td className="px-6 py-5">
                      <span className="text-xl font-black text-hubspot-black tracking-tighter">{account.score}</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="scale-90 origin-left">
                        {tierInfo.badge}
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <p className="font-bold text-hubspot-black">{account.account}</p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="px-2 py-1 bg-hubspot-gray-100 text-[9px] font-black text-hubspot-dark/50 rounded uppercase tracking-tighter">
                        {accountData?.sector || '—'}
                      </span>
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-sm font-black text-green-700">
                        {(account.win_rate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-5 font-bold text-hubspot-dark/60 text-xs">
                      {account.deals_summary.won}W <span className="text-hubspot-dark/20 mx-1">/</span> {account.deals_summary.lost}L
                    </td>
                    <td className="px-6 py-5 text-hubspot-black font-black text-xs">
                      ${account.avg_ticket.toFixed(0)}
                    </td>
                    <td className="px-6 py-5">
                      <span className="px-3 py-1 bg-hubspot-orange/10 text-hubspot-orange text-[10px] font-black rounded-full border border-hubspot-orange/20">
                        ${(account.revenue_total / 1000).toFixed(0)}k
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
