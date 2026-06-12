import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { opportunitiesApi } from '../api/client';

export const FilterBar = ({ onFiltersChange, onRefresh }) => {
  const { t } = useLanguage();
  const [filters, setFilters] = useState({
    sales_agent: '',
    deal_stage: '',
    product: '',
    account: '',
    min_score: '',
  });

  const [filterOptions, setFilterOptions] = useState({
    sales_agents: [],
    deal_stages: [],
    products: [],
    accounts: [],
  });

  const [loading, setLoading] = useState(true);

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
      min_score: '',
    };
    setFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Filter className="w-5 h-5" />
          {t('filters.title')}
        </h2>
        <button
          onClick={() => {
            handleReset();
            onRefresh();
          }}
          className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
        >
          <RefreshCw className="w-4 h-4" />
          {t('filters.reset')}
        </button>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded" />
          <div className="h-10 bg-gray-200 rounded" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Sales Agent Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('filters.salesAgent')}
            </label>
            <select
              value={filters.sales_agent}
              onChange={(e) => handleChange('sales_agent', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="">{t('filters.allAgents')}</option>
              {filterOptions.sales_agents?.map((agent) => (
                <option key={agent} value={agent}>
                  {agent}
                </option>
              ))}
            </select>
          </div>

          {/* Deal Stage Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('filters.dealStage')}
            </label>
            <select
              value={filters.deal_stage}
              onChange={(e) => handleChange('deal_stage', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="">{t('filters.allStages')}</option>
              {filterOptions.deal_stages?.map((stage) => (
                <option key={stage} value={stage}>
                  {stage}
                </option>
              ))}
            </select>
          </div>

          {/* Product Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('filters.product')}
            </label>
            <select
              value={filters.product}
              onChange={(e) => handleChange('product', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="">{t('filters.allProducts')}</option>
              {filterOptions.products?.map((product) => (
                <option key={product} value={product}>
                  {product}
                </option>
              ))}
            </select>
          </div>

          {/* Account Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('filters.account')}
            </label>
            <input
              type="text"
              placeholder={t('filters.searchAccount')}
              value={filters.account}
              onChange={(e) => handleChange('account', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Min Score Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('filters.minScore')}
            </label>
            <input
              type="number"
              min="0"
              max="100"
              placeholder={t('filters.minScorePlaceholder')}
              value={filters.min_score}
              onChange={(e) => handleChange('min_score', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
        </div>
      )}
    </div>
  );
};
