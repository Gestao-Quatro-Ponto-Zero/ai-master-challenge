import React, { useEffect, useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { dashboardApi } from '../api/client';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export const DashboardStats = () => {
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
    return <div className="animate-pulse bg-gray-200 h-20 rounded" />;
  }

  if (error) {
    return <div className="bg-red-50 text-red-700 p-4 rounded">Error loading stats: {error}</div>;
  }

  const { summary, top_deals, seller_performance } = stats;

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm font-medium">Open Deals</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {summary?.total_open_deals || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm font-medium">Sales Agents</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {summary?.total_agents || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm font-medium">Avg Deal Score</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {summary?.avg_score?.toFixed(1) || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm font-medium">Avg Success Rate</p>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {Math.round((summary?.avg_success_prob || 0) * 100)}%
          </p>
        </div>
      </div>

      {/* Top Deals Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">🔥 Top Scoring Deals</h2>
        <div className="space-y-3">
          {top_deals?.map((deal) => (
            <div
              key={deal.opportunity_id}
              className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-transparent rounded-lg border border-blue-200"
            >
              <div>
                <p className="font-semibold text-gray-900">{deal.account}</p>
                <p className="text-xs text-gray-600">{deal.product} • {deal.sales_agent}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-600">{deal.total_score?.toFixed(1)}</p>
                <p className="text-xs text-gray-600">{Math.round(deal.success_probability * 100)}% success</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Seller Performance */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">👥 Top Sales Agents</h2>
        <div className="space-y-2">
          {seller_performance?.map((seller) => (
            <div
              key={seller.sales_agent}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="font-semibold text-gray-900">{seller.sales_agent}</p>
                <p className="text-xs text-gray-600">{seller.deals_count} open deals</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-gray-900">{seller.avg_score?.toFixed(1)}</p>
                <p className="text-xs text-green-600">{Math.round(seller.avg_success_prob * 100)}% avg success</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export const TimeOnPipelineChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getTimeOnPipeline()
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse bg-gray-200 h-64 rounded" />;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-bold text-gray-900 mb-4">⏱️ Deal Duration Impact</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time_range" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Deal Count" />
          <Bar yAxisId="right" dataKey="avg_success_prob" fill="#10b981" name="Avg Success %" />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-600 mt-2">
        💡 Shows how deal duration affects success probability. Optimal range: 100-120 days
      </p>
    </div>
  );
};

export const AccountSizeChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getAccountSize()
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse bg-gray-200 h-64 rounded" />;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-bold text-gray-900 mb-4">🏢 Company Size Impact</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="size_category" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#8b5cf6" name="Deal Count" />
          <Bar dataKey="avg_success_prob" fill="#10b981" name="Avg Success %" />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-600 mt-2">
        💡 Success rate by company size. Larger accounts often have longer sales cycles
      </p>
    </div>
  );
};
