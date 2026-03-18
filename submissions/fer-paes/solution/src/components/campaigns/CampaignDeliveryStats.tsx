import { Loader2, Send, CheckCircle2, XCircle, Clock, SkipForward, TrendingUp } from 'lucide-react';
import type { DeliveryStats } from '../../services/campaignDeliveryService';

interface StatItemProps {
  label:  string;
  value:  number | string;
  icon:   React.ComponentType<{ className?: string }>;
  color:  string;
  bg:     string;
}

function StatItem({ label, value, icon: Icon, color, bg }: StatItemProps) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3.5 rounded-xl border ${bg} border-opacity-60`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${bg} ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className={`text-xl font-bold tabular-nums ${color}`}>{value}</p>
      </div>
    </div>
  );
}

interface Props {
  stats:   DeliveryStats | null;
  loading: boolean;
}

export default function CampaignDeliveryStats({ stats, loading }: Props) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        Carregando estatísticas...
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-4">
      {/* delivery rate */}
      <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-500" />
            <span className="text-sm font-semibold text-gray-700">Taxa de entrega</span>
          </div>
          <span className="text-xl font-bold text-emerald-600 tabular-nums">{stats.delivery_rate}%</span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${stats.delivery_rate}%` }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-1.5">{stats.total} destinatários no total</p>
      </div>

      {/* counters grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <StatItem label="Pendentes"  value={stats.pending}   icon={Clock}        color="text-gray-500"    bg="bg-gray-50"    />
        <StatItem label="Enviados"   value={stats.sent}      icon={Send}         color="text-sky-600"     bg="bg-sky-50"     />
        <StatItem label="Entregues"  value={stats.delivered} icon={CheckCircle2} color="text-emerald-600" bg="bg-emerald-50" />
        <StatItem label="Falharam"   value={stats.failed}    icon={XCircle}      color="text-red-500"     bg="bg-red-50"     />
        <StatItem label="Ignorados"  value={stats.skipped}   icon={SkipForward}  color="text-gray-400"    bg="bg-gray-50"    />
      </div>
    </div>
  );
}
