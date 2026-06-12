import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, X } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { opportunitiesApi } from '../api/client';
import { ScoreBadge, ScoreBreakdown, SuccessProbability } from './ScoreDisplay';
import { formatCurrency, formatDate, daysOnPipeline } from '../utils/formatting';

export const OpportunitiesTable = ({ filters, refreshTrigger, selectedDeal, onSelectDeal }) => {
  const { t } = useLanguage();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('total_score');
  const [sortDir, setSortDir] = useState('DESC');

  useEffect(() => {
    setLoading(true);
    opportunitiesApi.getAll({
      ...filters,
      sort_by: sortBy,
      sort_dir: sortDir,
      limit: 100,
    })
      .then(res => {
        setOpportunities(res.data || []);
        setError(null);
      })
      .catch(err => {
        setError(err.message);
        setOpportunities([]);
      })
      .finally(() => setLoading(false));
  }, [filters, sortBy, sortDir, refreshTrigger]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDir(sortDir === 'DESC' ? 'ASC' : 'DESC');
    } else {
      setSortBy(column);
      setSortDir('DESC');
    }
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return <div className="w-4 h-4" />;
    return sortDir === 'DESC' ? (
      <ChevronDown className="w-4 h-4" />
    ) : (
      <ChevronUp className="w-4 h-4" />
    );
  };

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
        ⚠️ Error loading opportunities: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">
          📋 {t('table.pipelineOpportunities')} ({opportunities.length})
        </h2>
        {loading && <span className="text-sm text-gray-600 animate-pulse">{t('table.loadingTable')}</span>}
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse bg-gray-200 h-12 rounded" />
          ))}
        </div>
      ) : opportunities.length === 0 ? (
        <div className="bg-gray-50 text-gray-600 p-8 rounded-lg text-center border border-gray-200">
          {t('table.noResults')}
        </div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('sales_agent')}
                    className="text-sm font-semibold text-gray-700 flex items-center gap-1 hover:text-gray-900"
                  >
                    {t('table.agent')}
                    <SortIcon column="sales_agent" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('account')}
                    className="text-sm font-semibold text-gray-700 flex items-center gap-1 hover:text-gray-900"
                  >
                    {t('table.account')}
                    <SortIcon column="account" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('product')}
                    className="text-sm font-semibold text-gray-700 flex items-center gap-1 hover:text-gray-900"
                  >
                    {t('table.product')}
                    <SortIcon column="product" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('deal_stage')}
                    className="text-sm font-semibold text-gray-700 flex items-center gap-1 hover:text-gray-900"
                  >
                    {t('table.stage')}
                    <SortIcon column="deal_stage" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <span className="text-sm font-semibold text-gray-700">{t('table.daysOnPipeline')}</span>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('total_score')}
                    className="text-sm font-semibold text-gray-700 flex items-center gap-1 hover:text-gray-900"
                  >
                    {t('table.score')}
                    <SortIcon column="total_score" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <span className="text-sm font-semibold text-gray-700">{t('table.successProbability')}</span>
                </th>
                <th className="px-4 py-3 text-left">
                  <span className="text-sm font-semibold text-gray-700">{t('table.action')}</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {opportunities.map((opp) => (
                <tr
                  key={opp.opportunity_id}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {opp.sales_agent}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900">{opp.account}</span>
                      <span className="text-xs text-gray-500">{opp.sector}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{opp.product}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {opp.deal_stage}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {daysOnPipeline(opp.engage_date)} {t('table.daysSuffix')}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onSelectDeal(opp)}
                      className="text-sm"
                    >
                      <ScoreBadge score={opp.total_score} />
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <SuccessProbability probability={opp.success_probability} />
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <button
                      onClick={() => onSelectDeal(opp)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {t('table.view')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export const DealDetailModal = ({ deal, onClose }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (deal) {
      opportunitiesApi.getById(deal.opportunity_id)
        .then(res => setDetails(res.data))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [deal]);

  if (!deal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg max-w-2xl w-full my-8">
        <div className="sticky top-0 border-b border-gray-200 bg-white p-6 flex items-center justify-between rounded-t-lg">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{deal.account}</h2>
            <p className="text-sm text-gray-600">{deal.opportunity_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-40 bg-gray-200 rounded" />
            </div>
          ) : details ? (
            <>
              {/* Score Breakdown */}
              <ScoreBreakdown
                stage_score={details.stage_score}
                account_score={details.account_score}
                seller_score={details.seller_score}
                product_score={details.product_score}
                time_score={details.time_score}
                total_score={details.total_score}
                success_probability={details.success_probability}
              />

              {/* Deal Information */}
              <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase">Sales Agent</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">{details.sales_agent}</p>
                  <p className="text-xs text-gray-600">Manager: {details.manager}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase">Region</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">{details.regional_office}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase">Deal Stage</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">{details.deal_stage}</p>
                  <p className="text-xs text-gray-600">Engaged: {formatDate(details.engage_date)}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase">Product</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">{details.product}</p>
                  <p className="text-xs text-gray-600">Price: {formatCurrency(details.sales_price)}</p>
                </div>
              </div>

              {/* Account Information */}
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-900 mb-3">Account Profile</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs font-medium text-gray-600">Sector</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">{details.sector}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-600">Established</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">{details.year_established}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-600">Revenue</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {formatCurrency(details.revenue * 1000000)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-600">Employees</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {formatNumber(details.employees)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Seller Performance */}
              {details.seller_metrics && (
                <div className="border-t pt-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Seller Performance</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-xs font-medium text-gray-600">Total Deals</p>
                      <p className="text-2xl font-bold text-blue-600 mt-1">
                        {details.seller_metrics.total_deals}
                      </p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-xs font-medium text-gray-600">Won Deals</p>
                      <p className="text-2xl font-bold text-green-600 mt-1">
                        {details.seller_metrics.won_deals}
                      </p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <p className="text-xs font-medium text-gray-600">Avg Score</p>
                      <p className="text-2xl font-bold text-purple-600 mt-1">
                        {details.seller_metrics.avg_deal_score?.toFixed(1) || '-'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Account History */}
              {details.account_history && details.account_history.length > 0 && (
                <div className="border-t pt-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Account Deal History</h3>
                  <div className="space-y-2">
                    {details.account_history.map((h) => (
                      <div key={h.opportunity_id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{h.product}</p>
                          <p className="text-xs text-gray-600">{h.deal_stage} • {formatDate(h.close_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-gray-900">{h.total_score?.toFixed(1)}</p>
                          <p className="text-xs text-gray-600">{formatCurrency(h.close_value)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        <div className="border-t border-gray-200 bg-gray-50 p-6 flex justify-end gap-2 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-100"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

function formatNumber(value) {
  if (!value) return '-';
  return value.toLocaleString();
}
