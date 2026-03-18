import { useState } from 'react';
import {
  Loader2, Megaphone, Play, Pause, Trash2, ChevronRight, Users, Mail,
  MessageCircle, MessageSquare, Smartphone,
} from 'lucide-react';
import type { Campaign } from '../../services/campaignService';
import {
  CHANNEL_META, activateCampaign, pauseCampaign, deleteCampaign,
} from '../../services/campaignService';
import CampaignStatusBadge from './CampaignStatusBadge';

const CHANNEL_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  email:    Mail,
  whatsapp: MessageCircle,
  chat:     MessageSquare,
  sms:      Smartphone,
};

interface Props {
  campaigns:   Campaign[];
  loading:     boolean;
  selectedId?: string;
  onSelect:    (c: Campaign) => void;
  onRefresh:   () => void;
}

function CampaignRow({
  campaign,
  isSelected,
  onSelect,
  onRefresh,
}: {
  campaign:   Campaign;
  isSelected: boolean;
  onSelect:   () => void;
  onRefresh:  () => void;
}) {
  const [acting, setActing] = useState<string | null>(null);
  const meta   = CHANNEL_META[campaign.channel];
  const Icon   = CHANNEL_ICONS[campaign.channel] ?? Mail;

  async function handleActivate(e: React.MouseEvent) {
    e.stopPropagation();
    setActing('activate');
    try { await activateCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handlePause(e: React.MouseEvent) {
    e.stopPropagation();
    setActing('pause');
    try { await pauseCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm('Excluir esta campanha em rascunho?')) return;
    setActing('delete');
    try { await deleteCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  const canActivate = campaign.status === 'draft' || campaign.status === 'paused';
  const canPause    = campaign.status === 'running' || campaign.status === 'scheduled';
  const canDelete   = campaign.status === 'draft';

  return (
    <tr
      onClick={onSelect}
      className={`cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-50/60 hover:bg-blue-50/80' : 'hover:bg-gray-50/50'
      }`}
    >
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
            <Megaphone className="w-3.5 h-3.5 text-blue-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{campaign.name}</p>
            {campaign.description && (
              <p className="text-xs text-gray-400 truncate max-w-[180px]">{campaign.description}</p>
            )}
          </div>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5">
          <Users className="w-3 h-3 text-gray-300" />
          <div>
            <p className="text-xs font-medium text-gray-600 truncate max-w-[140px]">
              {campaign.segment_name}
            </p>
            <p className="text-xs text-gray-400 tabular-nums">
              {Number(campaign.member_count).toLocaleString('pt-BR')} membros
            </p>
          </div>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${meta.color} ${meta.bg} ${meta.border}`}>
          <Icon className="w-3 h-3" />
          {meta.label}
        </span>
      </td>
      <td className="px-5 py-3.5">
        <CampaignStatusBadge status={campaign.status} />
      </td>
      <td className="px-5 py-3.5 text-xs text-gray-400 tabular-nums whitespace-nowrap">
        {campaign.scheduled_at
          ? new Date(campaign.scheduled_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
          : '—'}
      </td>
      <td className="px-5 py-3.5 text-xs text-gray-400 tabular-nums whitespace-nowrap">
        {new Date(campaign.created_at).toLocaleDateString('pt-BR')}
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {canActivate && (
            <button
              onClick={handleActivate}
              disabled={acting !== null}
              title="Ativar campanha"
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 disabled:opacity-40 transition-colors"
            >
              {acting === 'activate'
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                : <Play className="w-3.5 h-3.5" />
              }
            </button>
          )}
          {canPause && (
            <button
              onClick={handlePause}
              disabled={acting !== null}
              title="Pausar campanha"
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 disabled:opacity-40 transition-colors"
            >
              {acting === 'pause'
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                : <Pause className="w-3.5 h-3.5" />
              }
            </button>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              disabled={acting !== null}
              title="Excluir rascunho"
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 disabled:opacity-40 transition-colors"
            >
              {acting === 'delete'
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                : <Trash2 className="w-3.5 h-3.5" />
              }
            </button>
          )}
          <button
            onClick={onSelect}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function CampaignsTable({ campaigns, loading, selectedId, onSelect, onRefresh }: Props) {
  if (loading && campaigns.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && campaigns.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <Megaphone className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhuma campanha criada</p>
        <p className="text-xs text-gray-300">Crie uma campanha para engajar seus clientes</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            {['Campanha', 'Segmento', 'Canal', 'Status', 'Agendamento', 'Criada em', 'Ações'].map((h) => (
              <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {campaigns.map((c) => (
            <CampaignRow
              key={c.id}
              campaign={c}
              isSelected={c.id === selectedId}
              onSelect={() => onSelect(c)}
              onRefresh={onRefresh}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
