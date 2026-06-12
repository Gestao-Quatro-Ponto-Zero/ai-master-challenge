import React, { useEffect, useState } from 'react';
import { TrendingUp, Users, Target, Award } from 'lucide-react';
import { motion } from 'framer-motion';
import { dashboardApi } from '../api/client';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { useLanguage } from '../i18n/LanguageContext';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

const MetricCard = ({ icon: Icon, label, value, color, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.25 }}
    className="kpi-card"
  >
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-extrabold text-gray-900 mt-1.5 tabular-nums">{value}</p>
      </div>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-${color}-50`}>
        <Icon className={`w-5 h-5 text-${color}-600`} aria-hidden="true" />
      </div>
    </div>
  </motion.div>
);

export const DashboardStats = () => {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    dashboardApi.getStats()
      .then(res => setStats(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div className="h-3 w-20 bg-gray-200 rounded mb-3" />
            <div className="h-8 w-16 bg-gray-100 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 text-rose-700 p-4 rounded-xl border border-rose-200 text-sm font-medium">
        Error loading stats: {error}
      </div>
    );
  }

  const { summary, top_deals, seller_performance } = stats;

  const metrics = [
    { icon: Target, label: t('dashboard.totalOpenDeals'), value: summary?.total_open_deals || 0, color: 'indigo' },
    { icon: Users, label: t('dashboard.totalAgents'), value: summary?.total_agents || 0, color: 'blue' },
    { icon: Award, label: t('dashboard.avgScore'), value: summary?.avg_score?.toFixed(1) || '0', color: 'emerald' },
    { icon: TrendingUp, label: t('dashboard.highestScore'), value: `${Math.round((summary?.avg_success_prob || 0) * 100)}%`, color: 'amber' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <MetricCard key={metric.label} {...metric} delay={i * 0.05} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
        >
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500" aria-hidden="true" />
            {t('dashboard.topDeals')}
          </h2>
          <div className="space-y-2">
            {top_deals?.map((deal, i) => (
              <motion.div
                key={deal.opportunity_id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.04 }}
                className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50/60 to-transparent rounded-xl border border-indigo-100"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 text-sm truncate">{deal.account}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{deal.product} &bull; {deal.sales_agent}</p>
                </div>
                <div className="text-right flex-shrink-0 ml-3">
                  <p className="text-xl font-extrabold text-indigo-600 tabular-nums">{deal.total_score?.toFixed(1)}</p>
                  <p className="text-xs text-gray-500 tabular-nums">{Math.round(deal.success_probability * 100)}% success</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
        >
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-500" aria-hidden="true" />
            {t('dashboard.topAgents')}
          </h2>
          <div className="space-y-2">
            {seller_performance?.map((seller, i) => (
              <motion.div
                key={seller.sales_agent}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.04 }}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 text-sm">{seller.sales_agent}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{seller.deals_count} open deals</p>
                </div>
                <div className="text-right flex-shrink-0 ml-3">
                  <p className="text-lg font-bold text-gray-900 tabular-nums">{seller.avg_score?.toFixed(1)}</p>
                  <p className="text-xs text-emerald-600 tabular-nums">{Math.round(seller.avg_success_prob * 100)}% avg success</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

const ChartCard = ({ title, icon: Icon, iconColor, children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.25 }}
    className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
  >
    <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
      <Icon className={`w-5 h-5 text-${iconColor}-500`} aria-hidden="true" />
      {title}
    </h2>
    {children}
  </motion.div>
);

export const TimeOnPipelineChart = () => {
  const { t } = useLanguage();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getTimeOnPipeline()
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded mb-6" />
      <div className="h-64 bg-gray-100 rounded" />
    </div>
  );

  return (
    <ChartCard title={t('dashboard.dealDuration')} icon={TrendingUp} iconColor="blue">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="time_range" tick={{ fontSize: 12, fill: '#64748b' }} />
          <YAxis yAxisId="left" tick={{ fontSize: 12, fill: '#64748b' }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
          />
          <Legend />
          <Bar yAxisId="left" dataKey="count" fill="#6366f1" name="Deal Count" radius={[4, 4, 0, 0]} />
          <Bar yAxisId="right" dataKey="avg_success_prob" fill="#10b981" name="Avg Success %" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 mt-3 text-center font-medium">
        {t('dashboard.dealDuration')} &mdash; optimal range: 100-120 days
      </p>
    </ChartCard>
  );
};

export const AccountSizeChart = () => {
  const { t } = useLanguage();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getAccountSize()
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded mb-6" />
      <div className="h-64 bg-gray-100 rounded" />
    </div>
  );

  return (
    <ChartCard title={t('dashboard.accountSize')} icon={Award} iconColor="violet" delay={0.05}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="size_category" angle={-35} textAnchor="end" height={80} tick={{ fontSize: 12, fill: '#64748b' }} />
          <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
          />
          <Legend />
          <Bar dataKey="count" fill="#8b5cf6" name="Deal Count" radius={[4, 4, 0, 0]} />
          <Bar dataKey="avg_success_prob" fill="#10b981" name="Avg Success %" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 mt-3 text-center font-medium">
        {t('dashboard.accountSize')} &mdash; larger accounts often have longer sales cycles
      </p>
    </ChartCard>
  );
};
