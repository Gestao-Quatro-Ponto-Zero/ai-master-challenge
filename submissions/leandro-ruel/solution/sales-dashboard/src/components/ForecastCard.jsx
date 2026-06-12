import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, DollarSign, Target, PieChart } from 'lucide-react';
import { motion } from 'framer-motion';
import { useLanguage } from '../i18n/LanguageContext';
import { dashboardApi } from '../api/client';
import { formatCurrency } from '../utils/formatting';

function formatNumber(value) {
  if (value == null) return '-';
  return Number(value).toLocaleString();
}

export const ForecastCard = () => {
  const { t } = useLanguage();
  const [months, setMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getMonths()
      .then(res => setMonths(res.data || []))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    setLoading(true);
    dashboardApi.getForecast(selectedMonth || undefined)
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedMonth]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
      >
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-48 bg-gray-200 rounded" />
          <div className="h-4 w-64 bg-gray-100 rounded" />
          <div className="grid grid-cols-4 gap-4 mt-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-20 bg-gray-100 rounded-lg" />
            ))}
          </div>
        </div>
      </motion.div>
    );
  }

  const forecast = data?.forecast;
  const actual = data?.actual;

  const metrics = [
    {
      label: t('forecast.weightedRevenue'),
      value: formatCurrency(forecast?.weighted_revenue || 0),
      icon: DollarSign,
      color: 'indigo',
    },
    {
      label: t('forecast.pipelineValue'),
      value: formatCurrency(forecast?.pipeline_value || 0),
      icon: TrendingUp,
      color: 'blue',
    },
    {
      label: t('forecast.openDeals'),
      value: formatNumber(forecast?.open_deals || 0),
      icon: Target,
      color: 'emerald',
    },
    {
      label: t('forecast.avgProbability'),
      value: forecast?.avg_probability ? `${Math.round(forecast.avg_probability * 100)}%` : '-',
      icon: PieChart,
      color: 'amber',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-indigo-600" aria-hidden="true" />
            </div>
            <h2 className="text-base font-bold text-gray-900">{t('forecast.title')}</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1 ml-10">{t('forecast.subtitle')}</p>
        </div>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" aria-hidden="true" />
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white appearance-none transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 cursor-pointer"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.25em 1.25em',
            }}
          >
            <option value="">{t('forecast.allMonths')}</option>
            {months.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {metrics.map((metric, i) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i }}
            className="bg-gray-50 rounded-xl p-4 border border-gray-100"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center bg-${metric.color}-50`}>
                <metric.icon className={`w-3.5 h-3.5 text-${metric.color}-600`} aria-hidden="true" />
              </div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">{metric.label}</p>
            </div>
            <p className="text-xl font-extrabold text-gray-900 tabular-nums">{metric.value}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{t('forecast.forecastRevenue')}</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-violet-50 to-transparent rounded-xl border border-violet-100">
              <span className="text-sm font-semibold text-gray-700">{t('forecast.prospecting')}</span>
              <span className="text-sm font-bold text-gray-900 tabular-nums">
                {formatCurrency(forecast?.prospecting_forecast || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-blue-50 to-transparent rounded-xl border border-blue-100">
              <span className="text-sm font-semibold text-gray-700">{t('forecast.engaging')}</span>
              <span className="text-sm font-bold text-gray-900 tabular-nums">
                {formatCurrency(forecast?.engaging_forecast || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-indigo-50 to-transparent rounded-xl border border-indigo-100 mt-2">
              <span className="text-sm font-bold text-gray-900">{t('forecast.weightedRevenue')}</span>
              <span className="text-base font-extrabold text-indigo-600 tabular-nums">
                {formatCurrency(forecast?.weighted_revenue || 0)}
              </span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{t('forecast.won')}</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-emerald-50 to-transparent rounded-xl border border-emerald-100">
              <span className="text-sm font-semibold text-gray-700">{t('forecast.closedRevenue')}</span>
              <span className="text-sm font-bold text-emerald-700 tabular-nums">
                {formatCurrency(actual?.closed_revenue || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-emerald-50/50 rounded-xl">
              <span className="text-sm font-semibold text-gray-700">{t('forecast.openDeals')}</span>
              <span className="text-sm font-bold text-gray-900 tabular-nums">
                {formatNumber(actual?.won_deals || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-emerald-50/50 rounded-xl">
              <span className="text-sm font-semibold text-gray-700">{t('forecast.avgDealValue')}</span>
              <span className="text-sm font-bold text-gray-900 tabular-nums">
                {formatCurrency(actual?.avg_deal_value || 0)}
              </span>
            </div>

            {forecast?.weighted_revenue > 0 && (
              <div className="flex justify-between items-center p-3 bg-amber-50 rounded-xl border border-amber-100 mt-2">
                <span className="text-xs font-semibold text-amber-700">{t('forecast.vs')}</span>
                <span className="text-sm font-bold text-amber-700 tabular-nums">
                  {actual?.closed_revenue > 0
                    ? `${Math.round((forecast.weighted_revenue / actual.closed_revenue) * 100)}%`
                    : '—'}
                </span>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};
