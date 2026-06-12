import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { useLanguage } from '../i18n/LanguageContext';
import { opportunitiesApi } from '../api/client';

export const FilterBar = ({ onFiltersChange, onRefresh }) => {
  const { t } = useLanguage();
  const [filters, setFilters] = useState({
    sales_agent: '',
    deal_stage: '',
    product: '',
    account: '',
    region: '',
    manager: '',
    min_score: '',
  });

  const [filterOptions, setFilterOptions] = useState({
    sales_agents: [],
    deal_stages: [],
    products: [],
    accounts: [],
    regions: [],
    managers: [],
  });

  const [loading, setLoading] = useState(true);
  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  useEffect(() => {
    opportunitiesApi.getFilters()
      .then(res => setFilterOptions(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (field, value) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleReset = () => {
    const emptyFilters = {
      sales_agent: '',
      deal_stage: '',
      product: '',
      account: '',
      region: '',
      manager: '',
      min_score: '',
    };
    setFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
            <Filter className="w-4 h-4 text-indigo-600" aria-hidden="true" />
          </div>
          <h2 className="text-base font-bold text-gray-900">{t('filters.title')}</h2>
          {hasActiveFilters && (
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse-light" />
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={handleReset}
              className="btn-secondary text-xs px-3 py-1.5"
            >
              <X className="w-3 h-3" aria-hidden="true" />
              {t('filters.reset')}
            </button>
          )}
          <button
            onClick={onRefresh}
            className="btn-secondary text-xs px-3 py-1.5"
            aria-label="Refresh data"
          >
            <RefreshCw className="w-3 h-3" aria-hidden="true" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="animate-pulse space-y-2">
              <div className="h-3 w-20 bg-gray-200 rounded" />
              <div className="h-10 bg-gray-100 rounded-lg" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-agent">
              {t('filters.salesAgent')}
            </label>
            <select
              id="filter-agent"
              value={filters.sales_agent}
              onChange={(e) => handleChange('sales_agent', e.target.value)}
              className="select-field"
            >
              <option value="">{t('filters.allAgents')}</option>
              {filterOptions.sales_agents?.map((agent) => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-stage">
              {t('filters.dealStage')}
            </label>
            <select
              id="filter-stage"
              value={filters.deal_stage}
              onChange={(e) => handleChange('deal_stage', e.target.value)}
              className="select-field"
            >
              <option value="">{t('filters.allStages')}</option>
              {filterOptions.deal_stages?.map((stage) => (
                <option key={stage} value={stage}>{t('stages.' + stage) || stage}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-region">
              {t('filters.region')}
            </label>
            <select
              id="filter-region"
              value={filters.region}
              onChange={(e) => handleChange('region', e.target.value)}
              className="select-field"
            >
              <option value="">{t('filters.allRegions')}</option>
              {filterOptions.regions?.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-manager">
              {t('filters.manager')}
            </label>
            <select
              id="filter-manager"
              value={filters.manager}
              onChange={(e) => handleChange('manager', e.target.value)}
              className="select-field"
            >
              <option value="">{t('filters.allManagers')}</option>
              {filterOptions.managers?.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-product">
              {t('filters.product')}
            </label>
            <select
              id="filter-product"
              value={filters.product}
              onChange={(e) => handleChange('product', e.target.value)}
              className="select-field"
            >
              <option value="">{t('filters.allProducts')}</option>
              {filterOptions.products?.map((product) => (
                <option key={product} value={product}>{product}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-account">
              {t('filters.account')}
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" aria-hidden="true" />
              <input
                id="filter-account"
                type="text"
                placeholder={t('filters.searchAccount')}
                value={filters.account}
                onChange={(e) => handleChange('account', e.target.value)}
                className="input-field pl-9"
                autoComplete="off"
                spellCheck={false}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5" htmlFor="filter-score">
              {t('filters.minScore')}
            </label>
            <input
              id="filter-score"
              type="number"
              min="0"
              max="100"
              placeholder={t('filters.minScorePlaceholder')}
              value={filters.min_score}
              onChange={(e) => handleChange('min_score', e.target.value)}
              className="input-field tabular-nums"
              autoComplete="off"
            />
          </div>
        </div>
      )}
    </motion.div>
  );
};
