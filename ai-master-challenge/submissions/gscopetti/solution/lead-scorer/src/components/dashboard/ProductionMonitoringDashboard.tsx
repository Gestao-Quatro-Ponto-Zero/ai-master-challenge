import React, { useMemo } from 'react';
import { Card, Badge } from '@/components/ui';

interface MonitoringMetrics {
  byTier: {
    HOT: { total: number; won: number; lost: number; winRate: number; revenue: number };
    WARM: { total: number; won: number; lost: number; winRate: number; revenue: number };
    COOL: { total: number; won: number; lost: number; winRate: number; revenue: number };
    COLD: { total: number; won: number; lost: number; winRate: number; revenue: number };
  };
  baselineWinRate: number;
  lift: {
    hot: number;
    warm: number;
    combined: number;
  };
  roi: {
    topTierAttempts: number;
    topTierWins: number;
    topTierRevenue: number;
    revenuePerAttempt: number;
  };
}

interface ProductionMonitoringDashboardProps {
  metrics: MonitoringMetrics;
}

export function ProductionMonitoringDashboard({ metrics }: ProductionMonitoringDashboardProps) {
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'HOT':
        return 'from-red-500 to-red-600 text-white';
      case 'WARM':
        return 'from-orange-500 to-orange-600 text-white';
      case 'COOL':
        return 'from-blue-500 to-blue-600 text-white';
      case 'COLD':
        return 'from-gray-500 to-gray-600 text-white';
      default:
        return 'from-gray-500 to-gray-600 text-white';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'HOT':
        return '🔥';
      case 'WARM':
        return '🟡';
      case 'COOL':
        return '🔵';
      case 'COLD':
        return '⚪';
      default:
        return '📊';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <Card padding="lg" className="bg-gradient-to-r from-hubspot-dark to-hubspot-black text-white">
        <h2 className="text-3xl font-black tracking-tight mb-2">📊 Production Monitoring</h2>
        <p className="text-gray-300 text-sm">
          Real-time correlation between Scorer V2 predictions and actual Win/Loss rates
        </p>
      </Card>

      {/* Win Rates by Tier */}
      <div>
        <h3 className="text-xl font-bold text-hubspot-dark mb-4 uppercase tracking-tight">
          📈 Win Rates by Tier
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(metrics.byTier).map(([tier, data]) => (
            <Card
              key={tier}
              padding="lg"
              className={`bg-gradient-to-br ${getTierColor(tier)} relative overflow-hidden`}
            >
              <div className="absolute top-0 right-0 opacity-10 text-6xl font-black">
                {getTierIcon(tier)}
              </div>
              <div className="relative z-10">
                <p className="text-xs uppercase tracking-widest font-black opacity-90 mb-2">
                  {tier}
                </p>
                <div className="flex items-baseline gap-2 mb-4">
                  <p className="text-4xl font-black">{(data.winRate * 100).toFixed(1)}%</p>
                  <p className="text-xs opacity-80">Win Rate</p>
                </div>
                <div className="space-y-1 text-xs font-bold opacity-90">
                  <p>Deals: {data.total}</p>
                  <p>Won: {data.won} / Lost: {data.lost}</p>
                  <p>Revenue: {formatCurrency(data.revenue)}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Lift vs Random */}
      <Card padding="lg" className="border-l-4 border-l-blue-500">
        <h3 className="text-xl font-bold text-hubspot-dark mb-4 uppercase tracking-tight">
          🎯 Lift vs Random Selection
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600 uppercase tracking-widest font-bold mb-2">
              Baseline (Random)
            </p>
            <p className="text-4xl font-black text-hubspot-dark">
              {(metrics.baselineWinRate * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 uppercase tracking-widest font-bold mb-2">
              HOT Tier Lift
            </p>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-black text-red-600">
                {metrics.lift.hot.toFixed(2)}x
              </p>
              {metrics.lift.hot < 1.2 && (
                <Badge className="bg-yellow-100 text-yellow-900 text-xs">⚠️ Needs tuning</Badge>
              )}
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600 uppercase tracking-widest font-bold mb-2">
              WARM + HOT Lift
            </p>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-black text-orange-600">
                {metrics.lift.combined.toFixed(2)}x
              </p>
              {metrics.lift.combined >= 1.2 && (
                <Badge className="bg-green-100 text-green-900 text-xs">✅ Good</Badge>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* ROI Analysis */}
      <Card padding="lg" className="bg-green-50 border border-green-200">
        <h3 className="text-xl font-bold text-green-900 mb-4 uppercase tracking-tight">
          💰 ROI Analysis (HOT + WARM Focus)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-white rounded-lg border border-green-200">
            <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-2">
              Deals Attempted
            </p>
            <p className="text-3xl font-black text-green-600">{metrics.roi.topTierAttempts}</p>
          </div>
          <div className="text-center p-4 bg-white rounded-lg border border-green-200">
            <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-2">
              Deals Won
            </p>
            <p className="text-3xl font-black text-green-600">{metrics.roi.topTierWins}</p>
          </div>
          <div className="text-center p-4 bg-white rounded-lg border border-green-200">
            <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-2">
              Total Revenue
            </p>
            <p className="text-2xl font-black text-green-600">
              {formatCurrency(metrics.roi.topTierRevenue)}
            </p>
          </div>
          <div className="text-center p-4 bg-white rounded-lg border border-green-200">
            <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-2">
              Revenue / Attempt
            </p>
            <p className="text-2xl font-black text-green-600">
              {formatCurrency(metrics.roi.revenuePerAttempt)}
            </p>
          </div>
        </div>
      </Card>

      {/* Health Check */}
      <Card padding="lg" className="bg-blue-50 border border-blue-200">
        <h3 className="text-xl font-bold text-blue-900 mb-4 uppercase tracking-tight">
          ✅ Model Health Check
        </h3>
        <div className="space-y-2">
          {metrics.lift.hot >= 1.5 && (
            <div className="flex items-center gap-2 p-2 bg-white rounded border border-green-200">
              <span className="text-lg">✅</span>
              <p className="text-sm font-bold text-green-700">
                HOT tier has {metrics.lift.hot.toFixed(2)}x better win rate (Excellent)
              </p>
            </div>
          )}
          {metrics.lift.hot >= 1.2 && metrics.lift.hot < 1.5 && (
            <div className="flex items-center gap-2 p-2 bg-white rounded border border-green-200">
              <span className="text-lg">✅</span>
              <p className="text-sm font-bold text-green-700">
                HOT tier has {metrics.lift.hot.toFixed(2)}x better win rate (Good)
              </p>
            </div>
          )}
          {metrics.lift.hot < 1.2 && (
            <div className="flex items-center gap-2 p-2 bg-white rounded border border-yellow-200">
              <span className="text-lg">⚠️</span>
              <p className="text-sm font-bold text-yellow-700">
                HOT tier has only {metrics.lift.hot.toFixed(2)}x better win rate - needs tuning
              </p>
            </div>
          )}

          {metrics.lift.combined >= 1.2 && (
            <div className="flex items-center gap-2 p-2 bg-white rounded border border-green-200">
              <span className="text-lg">✅</span>
              <p className="text-sm font-bold text-green-700">
                HOT+WARM combined has {metrics.lift.combined.toFixed(2)}x lift - focusing on top tiers is effective
              </p>
            </div>
          )}

          {metrics.roi.revenuePerAttempt > 0 && (
            <div className="flex items-center gap-2 p-2 bg-white rounded border border-green-200">
              <span className="text-lg">✅</span>
              <p className="text-sm font-bold text-green-700">
                Positive ROI: {formatCurrency(metrics.roi.revenuePerAttempt)} per attempt
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Instructions */}
      <Card padding="lg">
        <h3 className="text-lg font-bold text-hubspot-dark mb-3 uppercase tracking-tight">
          📚 How to Interpret
        </h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>
            <strong>Win Rate:</strong> Percentage of deals in each tier that were actually won
          </li>
          <li>
            <strong>Lift:</strong> How much better the tier performs vs random selection (1.0x = same as baseline)
          </li>
          <li>
            <strong>ROI:</strong> Revenue generated per deal attempted when focusing on top tiers
          </li>
          <li>
            <strong>Lift > 1.2x:</strong> Model effectively separates winners from losers
          </li>
          <li>
            <strong>Revenue/Attempt > $0:</strong> Overall strategy is profitable
          </li>
        </ul>
      </Card>
    </div>
  );
}
