import { useState } from 'react';
import { X, Megaphone, Users, Calendar, Clock, CheckCircle2, Loader2, Play, Pause, Mail, MessageCircle, MessageSquare, Smartphone, CreditCard as Edit3 } from 'lucide-react';
import type { Campaign, CampaignChannel } from '../../services/campaignService';
import {
  CHANNEL_META, STATUS_META, TEMPLATE_VARS,
  activateCampaign, pauseCampaign, completeCampaign, updateCampaign,
} from '../../services/campaignService';
import CampaignStatusBadge from './CampaignStatusBadge';

const CHANNEL_ICONS: Record<CampaignChannel, React.ComponentType<{ className?: string }>> = {
  email:    Mail,
  whatsapp: MessageCircle,
  chat:     MessageSquare,
  sms:      Smartphone,
};

interface Props {
  campaign:  Campaign;
  onClose:   () => void;
  onRefresh: () => void;
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2.5 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-400 shrink-0 w-28">{label}</span>
      <div className="text-sm text-gray-700 text-right">{children}</div>
    </div>
  );
}

export default function CampaignDetails({ campaign, onClose, onRefresh }: Props) {
  const [acting,       setActing]       = useState<string | null>(null);
  const [editTemplate, setEditTemplate] = useState(false);
  const [newTemplate,  setNewTemplate]  = useState(campaign.message_template);
  const [savingTpl,    setSavingTpl]    = useState(false);

  const chanMeta  = CHANNEL_META[campaign.channel];
  const ChanIcon  = CHANNEL_ICONS[campaign.channel];

  async function handleActivate() {
    setActing('activate');
    try { await activateCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handlePause() {
    setActing('pause');
    try { await pauseCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handleComplete() {
    if (!confirm('Marcar esta campanha como concluída?')) return;
    setActing('complete');
    try { await completeCampaign(campaign.id); onRefresh(); }
    catch { /* noop */ }
    finally { setActing(null); }
  }

  async function handleSaveTemplate() {
    setSavingTpl(true);
    try {
      await updateCampaign(campaign.id, { message_template: newTemplate });
      setEditTemplate(false);
      onRefresh();
    } catch { /* noop */ }
    finally { setSavingTpl(false); }
  }

  const canActivate  = campaign.status === 'draft' || campaign.status === 'paused';
  const canPause     = campaign.status === 'running' || campaign.status === 'scheduled';
  const canComplete  = campaign.status === 'running' || campaign.status === 'scheduled';
  const canEditTpl   = campaign.status === 'draft' || campaign.status === 'paused';
  const statusMeta   = STATUS_META[campaign.status];

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden flex flex-col">
      {/* Header */}
      <div className={`px-5 py-4 border-b border-gray-100 ${statusMeta.bg}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-white/80 flex items-center justify-center shrink-0">
              <Megaphone className={`w-4 h-4 ${statusMeta.color}`} />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{campaign.name}</h3>
              {campaign.description && (
                <p className="text-xs text-gray-500 truncate">{campaign.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <CampaignStatusBadge status={campaign.status} />
            <button
              onClick={onClose}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-white/60 transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      {(canActivate || canPause || canComplete) && (
        <div className="px-5 py-3 flex items-center gap-2 border-b border-gray-100 bg-gray-50">
          {canActivate && (
            <button
              onClick={handleActivate}
              disabled={acting !== null}
              className="flex items-center gap-1.5 h-8 px-3 rounded-xl bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {acting === 'activate' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              Ativar
            </button>
          )}
          {canPause && (
            <button
              onClick={handlePause}
              disabled={acting !== null}
              className="flex items-center gap-1.5 h-8 px-3 rounded-xl bg-amber-500 text-white text-xs font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {acting === 'pause' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Pause className="w-3 h-3" />}
              Pausar
            </button>
          )}
          {canComplete && (
            <button
              onClick={handleComplete}
              disabled={acting !== null}
              className="flex items-center gap-1.5 h-8 px-3 rounded-xl bg-teal-600 text-white text-xs font-medium hover:bg-teal-700 disabled:opacity-50 transition-colors"
            >
              {acting === 'complete' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
              Concluir
            </button>
          )}
        </div>
      )}

      {/* Details */}
      <div className="flex-1 overflow-auto px-5 py-3 space-y-0">
        <InfoRow label="Segmento">
          <span className="flex items-center gap-1 justify-end">
            <Users className="w-3 h-3 text-gray-400" />
            <span className="font-medium">{campaign.segment_name}</span>
            <span className="text-gray-400">· {Number(campaign.member_count).toLocaleString('pt-BR')} membros</span>
          </span>
        </InfoRow>

        <InfoRow label="Canal">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${chanMeta.color} ${chanMeta.bg} ${chanMeta.border}`}>
            <ChanIcon className="w-3 h-3" />
            {chanMeta.label}
          </span>
        </InfoRow>

        <InfoRow label="Agendamento">
          <span className="flex items-center gap-1 justify-end text-gray-500">
            <Calendar className="w-3 h-3 text-gray-300" />
            {campaign.scheduled_at
              ? new Date(campaign.scheduled_at).toLocaleString('pt-BR')
              : <span className="text-gray-300 italic">Não agendado</span>}
          </span>
        </InfoRow>

        {campaign.started_at && (
          <InfoRow label="Iniciada em">
            <span className="flex items-center gap-1 justify-end text-gray-500">
              <Clock className="w-3 h-3 text-gray-300" />
              {new Date(campaign.started_at).toLocaleString('pt-BR')}
            </span>
          </InfoRow>
        )}

        {campaign.completed_at && (
          <InfoRow label="Concluída em">
            <span className="flex items-center gap-1 justify-end text-gray-500">
              <CheckCircle2 className="w-3 h-3 text-gray-300" />
              {new Date(campaign.completed_at).toLocaleString('pt-BR')}
            </span>
          </InfoRow>
        )}

        {campaign.creator_name && (
          <InfoRow label="Criada por">
            <span className="text-gray-600">{campaign.creator_name}</span>
          </InfoRow>
        )}

        <InfoRow label="Criada em">
          <span className="text-gray-500">
            {new Date(campaign.created_at).toLocaleDateString('pt-BR')}
          </span>
        </InfoRow>
      </div>

      {/* Template */}
      <div className="px-5 py-4 border-t border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-semibold text-gray-600">Template da Mensagem</p>
          {canEditTpl && !editTemplate && (
            <button
              onClick={() => { setNewTemplate(campaign.message_template); setEditTemplate(true); }}
              className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700 transition-colors"
            >
              <Edit3 className="w-3 h-3" />
              Editar
            </button>
          )}
        </div>

        {editTemplate ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1 mb-1">
              {TEMPLATE_VARS.map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setNewTemplate((p) => p + v)}
                  className="px-2 py-0.5 rounded-lg text-xs font-mono bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-600 transition-colors border border-gray-100"
                >
                  {v}
                </button>
              ))}
            </div>
            <textarea
              value={newTemplate}
              onChange={(e) => setNewTemplate(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm text-gray-700 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all resize-none"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setEditTemplate(false)}
                className="px-3 py-1.5 rounded-xl text-xs text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveTemplate}
                disabled={savingTpl}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue-600 text-white text-xs font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {savingTpl && <Loader2 className="w-3 h-3 animate-spin" />}
                Salvar
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
            {campaign.message_template ? (
              <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed text-xs">
                {campaign.message_template}
              </p>
            ) : (
              <p className="text-xs text-gray-300 italic">Sem template definido</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
