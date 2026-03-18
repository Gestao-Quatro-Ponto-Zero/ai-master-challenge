import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2, RefreshCw, Loader2, Ticket as TicketIcon, CheckCircle2, Clock, TrendingUp, AlertCircle, Save,
} from 'lucide-react';
import {
  getAllOperatorsMetrics, computeOverview, saveOperatorMetricsSnapshot, formatDuration, formatPeriodLabel,
  type OperatorMetricRow, type MetricPeriod,
} from '../services/metricsService';
import OperatorMetricsTable       from '../components/metrics/OperatorMetricsTable';
import OperatorMetricsCard        from '../components/metrics/OperatorMetricsCard';
import OperatorPerformanceChart   from '../components/metrics/OperatorPerformanceChart';

const PERIODS: MetricPeriod[] = ['today', '7d', '30d', '90d', 'all'];

const CHART_METRICS: { key: OperatorPerformanceChartMetric; label: string }[] = [
  { key: 'tickets_handled',         label: 'Atendidos'         },
  { key: 'tickets_resolved',        label: 'Resolvidos'        },
  { key: 'avg_first_response_time', label: 'Tempo de Resposta' },
  { key: 'avg_resolution_time',     label: 'Resolução'         },
  { key: 'resolution_rate',         label: 'Taxa'              },
];

type OperatorPerformanceChartMetric = 'tickets_handled' | 'tickets_resolved' | 'avg_first_response_time' | 'avg_resolution_time' | 'resolution_rate';

export default function OperatorMetrics() {
  const [period,       setPeriod]       = useState<MetricPeriod>('30d');
  const [rows,         setRows]         = useState<OperatorMetricRow[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [saving,       setSaving]       = useState(false);
  const [selectedOp,   setSelectedOp]   = useState<OperatorMetricRow | null>(null);
  const [chartMetric,  setChartMetric]  = useState<OperatorPerformanceChartMetric>('tickets_handled');
  const [activeView,   setActiveView]   = useState<'table' | 'chart'>('table');

  const load = useCallback(async (p: MetricPeriod) => {
    setLoading(true);
    setSelectedOp(null);
    try {
      const data = await getAllOperatorsMetrics(p);
      setRows(data);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(period); }, [load, period]);

  async function handleSaveSnapshot() {
    setSaving(true);
    try { await saveOperatorMetricsSnapshot(rows, period); } catch { } finally { setSaving(false); }
  }

  function handleSelectOperator(row: OperatorMetricRow) {
    setSelectedOp((prev) => prev?.operator_id === row.operator_id ? null : row);
  }

  const overview = computeOverview(rows);
  const active   = rows.filter((r) => r.tickets_handled > 0);

  const overviewCards = [
    {
      label: 'Total de Tickets Atendidos',
      value: overview.total_tickets_handled,
      icon:  TicketIcon,
      color: 'text-blue-400',
      bg:    'bg-blue-500/8 border-blue-500/12',
    },
    {
      label: 'Total de Tickets Resolvidos',
      value: overview.total_tickets_resolved,
      icon:  CheckCircle2,
      color: 'text-emerald-400',
      bg:    'bg-emerald-500/8 border-emerald-500/12',
    },
    {
      label: 'Média de Primeiro Atendimento',
      value: formatDuration(overview.avg_response_time_minutes),
      icon:  Clock,
      color: overview.avg_response_time_minutes === 0 ? 'text-slate-600'
        : overview.avg_response_time_minutes <= 10  ? 'text-emerald-400'
        : overview.avg_response_time_minutes <= 30  ? 'text-amber-400'
        : 'text-rose-400',
      bg: 'bg-slate-800/60 border-white/5',
    },
    {
      label: 'Taxa Geral de Resolução',
      value: `${overview.overall_resolution_rate}%`,
      icon:  TrendingUp,
      color: overview.overall_resolution_rate >= 80 ? 'text-emerald-400'
        : overview.overall_resolution_rate >= 50 ? 'text-amber-400'
        : 'text-rose-400',
      bg: 'bg-slate-800/60 border-white/5',
    },
  ];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/5 shrink-0">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-600/15 flex items-center justify-center">
              <BarChart2 className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Métricas de Operadores</h1>
              <p className="text-xs text-slate-300">Análises de desempenho e KPIs</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Period selector */}
            <div className="flex items-center gap-0.5 bg-slate-800/60 border border-white/6 rounded-xl p-0.5">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    period === p ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {formatPeriodLabel(p) === 'Today' ? 'Hoje'
                    : formatPeriodLabel(p).replace('Last ', '').replace(' days', 'd').replace(' time', '')}
                </button>
              ))}
            </div>

            <button
              onClick={() => load(period)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={handleSaveSnapshot}
              disabled={saving || rows.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors border border-white/6"
              title="Salvar instantâneo no banco de dados"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              {saving ? 'Salvando…' : 'Salvar Instantâneo'}
            </button>
          </div>
        </div>

        {/* Overview cards */}
        <div className="grid grid-cols-4 gap-3">
          {overviewCards.map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className={`flex items-center gap-3 border rounded-2xl px-4 py-3 ${bg}`}>
              <Icon className={`w-4 h-4 shrink-0 ${color}`} />
              <div>
                <p className={`text-xl font-bold tabular-nums ${color}`}>{value}</p>
                <p className="text-xs text-slate-400">{label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main content */}
      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      ) : rows.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 gap-3">
          <AlertCircle className="w-10 h-10 text-slate-600" />
          <p className="text-sm font-medium text-slate-300">Nenhum operador encontrado</p>
          <p className="text-xs text-slate-500">Crie operadores nas configurações de Operadores para ver as métricas aqui.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-auto px-6 py-5 space-y-4">
          {/* View toggle + period label */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              {active.length} de {rows.length} operadores ativos em <span className="text-slate-200">{formatPeriodLabel(period)}</span>
            </p>
            <div className="flex items-center gap-1 bg-slate-800/60 border border-white/6 rounded-xl p-0.5">
              <button
                onClick={() => setActiveView('table')}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${activeView === 'table' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}
              >
                Tabela
              </button>
              <button
                onClick={() => setActiveView('chart')}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${activeView === 'chart' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}
              >
                Gráficos
              </button>
            </div>
          </div>

          {activeView === 'table' ? (
            <div className="space-y-4">
              <OperatorMetricsTable
                rows={rows}
                selectedId={selectedOp?.operator_id ?? null}
                onSelectOperator={handleSelectOperator}
              />
              {selectedOp && (
                <OperatorMetricsCard
                  operator={selectedOp}
                  onClose={() => setSelectedOp(null)}
                />
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Chart metric selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Métrica:</span>
                <div className="flex items-center gap-0.5 bg-slate-800/60 border border-white/6 rounded-xl p-0.5">
                  {CHART_METRICS.map((m) => (
                    <button
                      key={m.key}
                      onClick={() => setChartMetric(m.key)}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        chartMetric === m.key ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-slate-900/60 border border-white/6 rounded-2xl p-5">
                <OperatorPerformanceChart rows={rows.filter((r) => r.tickets_handled > 0 || chartMetric === 'resolution_rate')} metric={chartMetric} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
