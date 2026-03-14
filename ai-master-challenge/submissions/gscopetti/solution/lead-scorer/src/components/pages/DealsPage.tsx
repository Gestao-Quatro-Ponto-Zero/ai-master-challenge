import { useState } from 'react';
import { useDealScoring } from '@/hooks/useDealScoring';
import { getTierInfo } from '@/utils/tiers';
import type { PipelineOpportunity, Account, Product, DealScore, FilterOptions, SalesTeam } from '@/types';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface DealsPageProps {
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
  filters: FilterOptions;
  onSelectDeal: (deal: DealScore) => void;
  salesTeams?: SalesTeam[];
}

type SortField = 'score' | 'days' | 'product' | 'account';
type SortOrder = 'asc' | 'desc';

export function DealsPage({
  pipeline,
  accounts,
  products,
  filters,
  onSelectDeal,
  salesTeams,
}: DealsPageProps) {
  // V2 Model: 4-pillar architecture with enriched data for filtering
  const dealScores = useDealScoring(pipeline, accounts, products, salesTeams);
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [searchTerm, setSearchTerm] = useState('');

  // Filter active deals
  let activeDeals = dealScores.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  );

  // Apply filters
  if (filters.tier) {
    activeDeals = activeDeals.filter((d) => d.tier === filters.tier);
  }

  if (filters.sales_agent) {
    activeDeals = activeDeals.filter((d) => d.sales_agent === filters.sales_agent);
  }

  if (filters.region) {
    activeDeals = activeDeals.filter((d) => d.region === filters.region);
  }

  if (filters.manager) {
    activeDeals = activeDeals.filter((d) => d.manager === filters.manager);
  }

  if (filters.series) {
    activeDeals = activeDeals.filter((d) => d.series === filters.series);
  }

  // Apply search
  if (searchTerm) {
    activeDeals = activeDeals.filter((d) =>
      (d.account?.toLowerCase() || 'prospect').includes(searchTerm.toLowerCase()) ||
      d.product.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.sales_agent.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }

  // Apply sorting
  const sortedDeals = [...activeDeals].sort((a, b) => {
    let aVal: any, bVal: any;

    if (sortField === 'score') {
      aVal = a.score;
      bVal = b.score;
    } else if (sortField === 'days') {
      aVal = Math.floor(
        (new Date().getTime() - a.engage_date.getTime()) / (1000 * 60 * 60 * 24)
      );
      bVal = Math.floor(
        (new Date().getTime() - b.engage_date.getTime()) / (1000 * 60 * 60 * 24)
      );
    } else if (sortField === 'product') {
      aVal = a.product;
      bVal = b.product;
    } else if (sortField === 'account') {
      aVal = a.account || 'zzz';
      bVal = b.account || 'zzz';
    }

    const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    return sortOrder === 'desc' ? -comparison : comparison;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <div className="w-4 h-4" />;
    return sortOrder === 'desc' ? <ChevronDown size={16} /> : <ChevronUp size={16} />;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Search and Export */}
      <div className="flex gap-4">
        <div className="relative flex-1 group">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-hubspot-dark/40 group-focus-within:text-hubspot-orange transition-colors">🔍</span>
          <input
            type="text"
            placeholder="Buscar por conta, produto ou vendedor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white border-2 border-hubspot-gray-100 rounded-hb text-sm font-bold text-hubspot-black placeholder-hubspot-dark/30 focus:border-hubspot-orange transition-all outline-none shadow-sm"
          />
        </div>
        <button className="px-8 py-3 bg-white border-2 border-hubspot-gray-200 hover:border-hubspot-black rounded-hb text-[10px] font-black uppercase tracking-widest text-hubspot-black transition-all active:scale-95 shadow-sm">
          📥 Exportar
        </button>
      </div>

      {/* Summary */}
      <div className="text-[10px] font-black text-hubspot-dark/40 uppercase tracking-[0.2em] ml-1">
        Mostrando {sortedDeals.length} de {activeDeals.length} oportunidades
      </div>

      {/* Table */}
      <div className="bg-white rounded-hb border-2 border-hubspot-gray-200 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-hubspot-gray-100 border-b-2 border-hubspot-gray-200">
              <tr>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('score')}
                    className="flex items-center gap-2 text-[10px] font-black text-hubspot-black uppercase tracking-widest hover:text-hubspot-orange transition-colors"
                  >
                    Score <SortIcon field="score" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Tier</th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('account')}
                    className="flex items-center gap-2 text-[10px] font-black text-hubspot-black uppercase tracking-widest hover:text-hubspot-orange transition-colors"
                  >
                    Conta <SortIcon field="account" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('product')}
                    className="flex items-center gap-2 text-[10px] font-black text-hubspot-black uppercase tracking-widest hover:text-hubspot-orange transition-colors"
                  >
                    Produto <SortIcon field="product" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Estágio</th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('days')}
                    className="flex items-center gap-2 text-[10px] font-black text-hubspot-black uppercase tracking-widest hover:text-hubspot-orange transition-colors"
                  >
                    Retenção <SortIcon field="days" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Vendedor</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hubspot-gray-100">
              {sortedDeals.map((deal) => {
                const tierInfo = getTierInfo(deal.tier);
                const daysInPipeline = Math.floor(
                  (new Date().getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24)
                );

                return (
                  <tr key={deal.opportunity_id} className="hover:bg-hubspot-gray-100/50 transition-colors group cursor-pointer" onClick={() => onSelectDeal(deal)}>
                    <td className="px-6 py-5">
                      <span className="text-xl font-black text-hubspot-black tracking-tighter">{deal.score}</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="scale-90 origin-left">
                        {tierInfo.badge}
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <p className="font-bold text-hubspot-black truncate max-w-[150px]">{deal.account || '—'}</p>
                    </td>
                    <td className="px-6 py-5 text-hubspot-dark/60 font-bold uppercase tracking-widest text-[10px]">
                      {deal.product}
                    </td>
                    <td className="px-6 py-5">
                      <span className="px-2 py-1 bg-hubspot-gray-100 text-[9px] font-black text-hubspot-dark/50 rounded uppercase tracking-tighter">
                        {deal.deal_stage}
                      </span>
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-xs font-black text-hubspot-black">
                        {daysInPipeline}d <span className="text-[9px] text-hubspot-dark/30 font-bold ml-1 uppercase">no funil</span>
                      </span>
                    </td>
                    <td className="px-6 py-5 text-hubspot-dark/60 font-bold text-xs">
                      {deal.sales_agent}
                    </td>
                    <td className="px-6 py-5">
                      <button
                        className="p-2 w-8 h-8 rounded-full bg-hubspot-gray-100 text-hubspot-black hover:bg-hubspot-orange hover:text-white transition-all flex items-center justify-center font-black"
                      >
                        →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {sortedDeals.length === 0 && (
          <div className="py-20 text-center">
            <p className="text-hubspot-dark/30 font-black uppercase tracking-[0.3em] text-xs">Nenhum resultado estratégico</p>
          </div>
        )}
      </div>
    </div>
  );
}
