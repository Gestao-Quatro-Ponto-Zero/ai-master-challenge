import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, X, Building2, User, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage } from '../i18n/LanguageContext';
import { opportunitiesApi } from '../api/client';
import { ScoreBadge, ScoreBreakdown, SuccessProbability } from './ScoreDisplay';
import { formatCurrency, formatDate, daysOnPipeline } from '../utils/formatting';

const SortIcon = ({ column, sortBy, sortDir }) => {
  if (sortBy !== column) return <div className="w-4 h-4 opacity-0 group-hover:opacity-30 transition-opacity" />;
  return sortDir === 'DESC'
    ? <ChevronDown className="w-4 h-4 text-indigo-500" aria-hidden="true" />
    : <ChevronUp className="w-4 h-4 text-indigo-500" aria-hidden="true" />;
};

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
      setSortDir(prev => prev === 'DESC' ? 'ASC' : 'DESC');
    } else {
      setSortBy(column);
      setSortDir('DESC');
    }
  };

  if (error) {
    return (
      <div className="bg-rose-50 text-rose-700 p-4 rounded-xl border border-rose-200 text-sm font-medium">
        Error loading opportunities: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-indigo-500" aria-hidden="true" />
          <h2 className="text-lg font-bold text-gray-900">
            {t('table.pipelineOpportunities')}
          </h2>
          <span className="text-sm font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-md tabular-nums">
            {opportunities.length}
          </span>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            {t('table.loadingTable')}
          </div>
        )}
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse flex gap-4">
                <div className="h-4 bg-gray-100 rounded w-1/4" />
                <div className="h-4 bg-gray-100 rounded w-1/4" />
                <div className="h-4 bg-gray-100 rounded w-1/6" />
                <div className="h-4 bg-gray-100 rounded w-1/6" />
                <div className="h-4 bg-gray-100 rounded w-16" />
              </div>
            ))}
          </div>
        </div>
      ) : opportunities.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-gray-200 p-12 text-center"
        >
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Building2 className="w-6 h-6 text-gray-400" aria-hidden="true" />
          </div>
          <p className="text-gray-600 font-medium">{t('table.noResults')}</p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="table-header-cell">
                    <button
                      onClick={() => handleSort('sales_agent')}
                      className="group inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {t('table.agent')}
                      <SortIcon column="sales_agent" sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                  <th className="table-header-cell">
                    <button
                      onClick={() => handleSort('account')}
                      className="group inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {t('table.account')}
                      <SortIcon column="account" sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                  <th className="table-header-cell">
                    <button
                      onClick={() => handleSort('product')}
                      className="group inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {t('table.product')}
                      <SortIcon column="product" sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                  <th className="table-header-cell">
                    <button
                      onClick={() => handleSort('deal_stage')}
                      className="group inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {t('table.stage')}
                      <SortIcon column="deal_stage" sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                  <th className="table-header-cell">{t('table.daysOnPipeline')}</th>
                  <th className="table-header-cell">
                    <button
                      onClick={() => handleSort('total_score')}
                      className="group inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {t('table.score')}
                      <SortIcon column="total_score" sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                  <th className="table-header-cell">{t('table.successProbability')}</th>
                  <th className="table-header-cell">{t('table.action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <AnimatePresence>
                  {opportunities.map((opp, i) => (
                    <motion.tr
                      key={opp.opportunity_id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ delay: i * 0.015, duration: 0.2 }}
                      className="group hover:bg-indigo-50/40 transition-colors cursor-default"
                    >
                      <td className="table-body-cell">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <User className="w-3.5 h-3.5 text-indigo-600" aria-hidden="true" />
                          </div>
                          <span className="font-semibold text-gray-900">{opp.sales_agent}</span>
                        </div>
                      </td>
                      <td className="table-body-cell">
                        <div className="flex flex-col">
                          <span className="font-medium text-gray-900">{opp.account}</span>
                          <span className="text-xs text-gray-500">{opp.sector}</span>
                        </div>
                      </td>
                      <td className="table-body-cell text-gray-700 font-medium">{opp.product}</td>
                      <td className="table-body-cell">
                        <span className="stage-badge bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200">
                          {opp.deal_stage}
                        </span>
                      </td>
                      <td className="table-body-cell tabular-nums text-gray-500">
                        {daysOnPipeline(opp.engage_date)}
                        <span className="text-gray-400 ml-0.5">{t('table.daysSuffix')}</span>
                      </td>
                      <td className="table-body-cell">
                        <ScoreBadge
                          score={opp.total_score}
                          onClick={() => onSelectDeal(opp)}
                          size="sm"
                        />
                      </td>
                      <td className="table-body-cell">
                        <SuccessProbability probability={opp.success_probability} />
                      </td>
                      <td className="table-body-cell">
                        <button
                          onClick={() => onSelectDeal(opp)}
                          className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg transition-all"
                        >
                          {t('table.view')}
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export const DealDetailModal = ({ deal, onClose }) => {
  const { t } = useLanguage();
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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-[8vh] pb-8 overflow-y-auto"
      style={{ overscrollBehavior: 'contain' }}
      onClick={onClose}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 20 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="bg-white rounded-2xl shadow-modal max-w-2xl w-full"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={t('dealDetail.title')}
      >
        <div className="sticky top-0 z-10 border-b border-gray-100 bg-white p-6 flex items-start justify-between rounded-t-2xl">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{deal.account}</h2>
            <p className="text-sm text-gray-500 font-mono mt-0.5">{deal.opportunity_id}</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-32 bg-gray-100 rounded-xl" />
                </div>
              ))}
            </div>
          ) : details ? (
            <>
              <ScoreBreakdown
                stage_score={details.stage_score}
                account_score={details.account_score}
                seller_score={details.seller_score}
                product_score={details.product_score}
                time_score={details.time_score}
                total_score={details.total_score}
                success_probability={details.success_probability}
              />

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="grid grid-cols-2 gap-4 bg-gradient-to-br from-gray-50 to-white rounded-xl p-5 border border-gray-200"
              >
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{t('dealDetail.salesAgent')}</p>
                  <div className="flex items-center gap-2 mt-1.5 min-w-0">
                    <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-indigo-600" aria-hidden="true" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-gray-900 truncate">{details.sales_agent}</p>
                      <p className="text-xs text-gray-500 truncate">{t('dealDetail.manager')}: {details.manager}</p>
                    </div>
                  </div>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{t('dealDetail.region')}</p>
                  <p className="text-sm font-bold text-gray-900 mt-1.5 truncate">{details.regional_office}</p>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{t('dealDetail.stage')}</p>
                  <p className="text-sm font-bold text-gray-900 mt-1.5 truncate">{details.deal_stage}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{t('dealDetail.engaged')}: {formatDate(details.engage_date)}</p>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{t('dealDetail.product')}</p>
                  <p className="text-sm font-bold text-gray-900 mt-1.5 truncate">{details.product}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{t('dealDetail.price')}: {formatCurrency(details.sales_price)}</p>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-xl border border-gray-200 p-5"
              >
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-indigo-500" aria-hidden="true" />
                  {t('dealDetail.accountProfile')}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: t('dealDetail.sector'), value: details.sector },
                    { label: t('dealDetail.established'), value: details.year_established },
                    { label: t('dealDetail.revenue'), value: formatCurrency(details.revenue * 1000000) },
                    { label: t('dealDetail.employees'), value: formatNumber(details.employees) },
                  ].map((item) => (
                    <div key={item.label} className="bg-gray-50 rounded-lg p-3 min-w-0">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{item.label}</p>
                      <p className="text-sm font-bold text-gray-900 mt-1 tabular-nums truncate">{item.value}</p>
                    </div>
                  ))}
                </div>
              </motion.div>

              {details.seller_metrics && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                  className="rounded-xl border border-gray-200 p-5"
                >
                  <h3 className="font-bold text-gray-900 mb-4">{t('dealDetail.sellerMetrics')}</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl p-4 border border-blue-200">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('dealDetail.totalDeals')}</p>
                      <p className="text-2xl font-extrabold text-blue-600 mt-1 tabular-nums">
                        {details.seller_metrics.total_deals}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-emerald-50 to-white rounded-xl p-4 border border-emerald-200">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('dealDetail.wonDeals')}</p>
                      <p className="text-2xl font-extrabold text-emerald-600 mt-1 tabular-nums">
                        {details.seller_metrics.won_deals}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-violet-50 to-white rounded-xl p-4 border border-violet-200">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('dealDetail.avgScore')}</p>
                      <p className="text-2xl font-extrabold text-violet-600 mt-1 tabular-nums">
                        {details.seller_metrics.avg_deal_score?.toFixed(1) || '-'}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              {details.account_history && details.account_history.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="rounded-xl border border-gray-200 p-5"
                >
                  <h3 className="font-bold text-gray-900 mb-4">{t('dealDetail.accountHistory')}</h3>
                  <div className="space-y-2">
                    {details.account_history.map((h, i) => (
                      <motion.div
                        key={h.opportunity_id}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + i * 0.05 }}
                        className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-gray-900 truncate">{h.product}</p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            <span className="stage-badge bg-indigo-50 text-indigo-700 text-[10px] mr-1.5">
                              {h.deal_stage}
                            </span>
                            {formatDate(h.close_date)}
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0 ml-4">
                          <p className="text-sm font-bold text-gray-900 tabular-nums">{h.total_score?.toFixed(1)}</p>
                          <p className="text-xs text-gray-500 tabular-nums">{formatCurrency(h.close_value)}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </>
          ) : null}
        </div>

        <div className="border-t border-gray-100 bg-gray-50/80 p-6 flex justify-end rounded-b-2xl">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            {t('dealDetail.close')}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

function formatNumber(value) {
  if (!value) return '-';
  return value.toLocaleString();
}
