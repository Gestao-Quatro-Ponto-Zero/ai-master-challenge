import type { SalesTeam, Product, FilterOptions } from '@/types';
import { useState } from 'react';

interface HeaderProps {
  salesTeams: SalesTeam[];
  products: Product[];
  filters: FilterOptions;
  onFilterChange: (filters: FilterOptions) => void;
}

export function Header({
  salesTeams,
  products,
  filters,
  onFilterChange,
}: HeaderProps) {
  const [showFilters, setShowFilters] = useState(false);

  // Get unique values
  const regions = [...new Set(salesTeams.map((t) => t.regional_office))];
  const managers = [...new Set(salesTeams.map((t) => t.manager))];
  const agents = [...new Set(salesTeams.map((t) => t.sales_agent))];
  const series = [...new Set(products.map((p) => p.series))];

  const handleFilterChange = (key: keyof FilterOptions, value: string | undefined) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-hubspot-gray-200 p-6 sticky top-0 z-20 shadow-sm">
      <div className="flex justify-between items-center max-w-[1400px] mx-auto">
        <div className="flex items-center gap-6">
          <div className="p-3 bg-hubspot-gray-100 rounded-hb border border-hubspot-gray-200">
            <span className="text-xl">🔍</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-hubspot-black tracking-tight flex items-center gap-2">
              Filtros Estratégicos
              <span className="px-2 py-0.5 bg-hubspot-peach/30 text-[10px] font-black text-hubspot-orange rounded-full uppercase tracking-widest border border-hubspot-orange/20">Globais</span>
            </h2>
            <p className="text-xs font-medium text-hubspot-dark/50 mt-1 italic">Personalize sua visão do pipeline em tempo real</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-6 py-2.5 rounded-hb text-sm font-bold tracking-wide transition-all duration-200 flex items-center gap-2 shadow-sm active:scale-95 ${showFilters
                ? 'bg-hubspot-dark text-white ring-4 ring-hubspot-dark/10'
                : 'bg-white border-2 border-hubspot-orange text-hubspot-orange hover:bg-hubspot-peach/10'
              }`}
          >
            {showFilters ? '✕ Ocultar Painel' : '⚙️ Ajustar Filtros'}
          </button>

          <div className="w-10 h-10 rounded-full border-2 border-hubspot-gray-200 bg-hubspot-gray-100 flex items-center justify-center overflow-hidden cursor-help hover:border-hubspot-orange transition-colors" title="Usuário Logado">
            <span className="text-xs font-black text-hubspot-dark/40">ADM</span>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 max-w-[1400px] mx-auto animate-in fade-in slide-in-from-top-4 duration-300">
          {[
            { label: 'Regional', key: 'region', options: regions, icon: '📍' },
            { label: 'Gerente', key: 'manager', options: managers, icon: '👨‍💼' },
            { label: 'Vendedor', key: 'sales_agent', options: agents, icon: '🤝' },
            { label: 'Série', key: 'series', options: series, icon: '📦' }
          ].map((filter) => (
            <div key={filter.key} className="relative group">
              <label className="text-[10px] font-black text-hubspot-dark/40 uppercase tracking-widest ml-1 mb-1.5 block flex items-center gap-1">
                {filter.icon} {filter.label}
              </label>
              <select
                value={(filters as any)[filter.key] || ''}
                onChange={(e) => handleFilterChange(filter.key as any, e.target.value || undefined)}
                className="w-full px-4 py-3 bg-hubspot-gray-100 border-2 border-transparent rounded-hb text-sm font-bold text-hubspot-black hover:bg-white hover:border-hubspot-gray-200 focus:bg-white focus:border-hubspot-orange focus:ring-4 focus:ring-hubspot-orange/10 focus:outline-none transition-all cursor-pointer appearance-none"
              >
                <option value="">Todos</option>
                {filter.options.sort().map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          ))}

          <div className="relative group">
            <label className="text-[10px] font-black text-hubspot-dark/40 uppercase tracking-widest ml-1 mb-1.5 block flex items-center gap-1">
              🔥 Prioridade
            </label>
            <select
              value={filters.tier || ''}
              onChange={(e) => handleFilterChange('tier', (e.target.value as any) || undefined)}
              className="w-full px-4 py-3 bg-hubspot-orange/5 border-2 border-transparent rounded-hb text-sm font-bold text-hubspot-orange hover:bg-white hover:border-hubspot-orange/20 focus:bg-white focus:border-hubspot-orange focus:ring-4 focus:ring-hubspot-orange/10 focus:outline-none transition-all cursor-pointer appearance-none"
            >
              <option value="">Todos os Tiers</option>
              <option value="HOT">🔥 HOT LEADS</option>
              <option value="WARM">🟡 WARM LEADS</option>
              <option value="COOL">🔵 COOL LEADS</option>
              <option value="COLD">⚪ COLD LEADS</option>
            </select>
          </div>
        </div>
      )}

      {/* Active Filters Display */}
      {(filters.region || filters.manager || filters.sales_agent || filters.series || filters.tier) && (
        <div className="mt-8 flex flex-wrap gap-2 max-w-[1400px] mx-auto pt-4 border-t border-hubspot-gray-100">
          <span className="text-[10px] font-black text-hubspot-dark/30 uppercase tracking-widest mr-2 flex items-center">Ativos:</span>
          {Object.entries(filters).map(([key, value]) => value && (
            <span key={key} className="text-[11px] font-bold bg-hubspot-dark text-white px-4 py-1.5 rounded-full flex items-center gap-2 group cursor-default shadow-sm hover:scale-105 transition-all">
              <span className="opacity-50 uppercase tracking-tighter text-[9px]">{key}:</span> {value}
              <button
                onClick={() => handleFilterChange(key as any, undefined)}
                className="hover:text-hubspot-orange ml-1 transition-colors"
              >✕</button>
            </span>
          ))}
          <button
            onClick={() => onFilterChange({})}
            className="text-[10px] font-black text-hubspot-orange uppercase tracking-widest hover:underline ml-auto"
          >Limpar Tudo</button>
        </div>
      )}
    </header>
  );
}
