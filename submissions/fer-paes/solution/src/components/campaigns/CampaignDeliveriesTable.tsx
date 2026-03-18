import { useState } from 'react';
import {
  Loader2, Send, Mail, MessageCircle, Phone, Smartphone,
  ChevronDown, ChevronUp, AlertCircle,
} from 'lucide-react';
import type { CampaignDelivery, DeliveryChannel } from '../../services/campaignDeliveryService';
import { CHANNEL_META } from '../../services/campaignDeliveryService';
import CampaignDeliveryStatusBadge from './CampaignDeliveryStatusBadge';

const CHANNEL_ICONS: Record<DeliveryChannel, React.ComponentType<{ className?: string }>> = {
  email:    Mail,
  whatsapp: Phone,
  chat:     MessageCircle,
  sms:      Smartphone,
};

function DeliveryRow({ delivery }: { delivery: CampaignDelivery }) {
  const [expanded, setExpanded] = useState(false);
  const meta   = CHANNEL_META[delivery.channel];
  const CIcon  = CHANNEL_ICONS[delivery.channel] ?? Mail;
  const hasMeta = delivery.error_message || delivery.message_body;

  return (
    <>
      <tr
        className={`hover:bg-gray-50/50 transition-colors ${hasMeta ? 'cursor-pointer' : ''}`}
        onClick={() => hasMeta && setExpanded((v) => !v)}
      >
        {/* Campaign */}
        <td className="px-5 py-3.5">
          <p className="text-sm font-medium text-gray-800 truncate max-w-[160px]">{delivery.campaign_name}</p>
        </td>

        {/* Customer */}
        <td className="px-5 py-3.5">
          <p className="text-sm text-gray-700">{delivery.customer_name}</p>
          <p className="text-xs text-gray-400 truncate max-w-[160px]">{delivery.customer_email}</p>
        </td>

        {/* Channel */}
        <td className="px-5 py-3.5">
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${meta.color} ${meta.bg}`}>
            <CIcon className="w-3 h-3" />
            {meta.label}
          </span>
        </td>

        {/* Status */}
        <td className="px-5 py-3.5">
          <CampaignDeliveryStatusBadge status={delivery.status} />
        </td>

        {/* Sent at */}
        <td className="px-5 py-3.5 text-xs text-gray-400 whitespace-nowrap tabular-nums">
          {delivery.sent_at
            ? new Date(delivery.sent_at).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
            : '—'}
        </td>

        {/* Delivered at */}
        <td className="px-5 py-3.5 text-xs text-gray-400 whitespace-nowrap tabular-nums">
          {delivery.delivered_at
            ? new Date(delivery.delivered_at).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
            : '—'}
        </td>

        {/* Retries */}
        <td className="px-5 py-3.5">
          {delivery.retry_count > 0
            ? <span className="text-xs text-amber-500 font-medium">{delivery.retry_count}x</span>
            : <span className="text-xs text-gray-300">—</span>
          }
        </td>

        {/* Expand toggle */}
        <td className="px-5 py-3.5">
          {hasMeta && (
            <button className="text-gray-300 hover:text-gray-500 transition-colors">
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </td>
      </tr>

      {/* expanded detail row */}
      {expanded && hasMeta && (
        <tr className="bg-gray-50/60">
          <td colSpan={8} className="px-5 pb-4 pt-2">
            <div className="space-y-2">
              {delivery.error_message && (
                <div className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-100 rounded-xl text-xs text-red-600">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>{delivery.error_message}</span>
                </div>
              )}
              {delivery.message_body && (
                <div className="px-3 py-2 bg-white border border-gray-100 rounded-xl text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">
                  {delivery.message_body}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

interface Props {
  deliveries: CampaignDelivery[];
  loading:    boolean;
}

export default function CampaignDeliveriesTable({ deliveries, loading }: Props) {
  if (loading && deliveries.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
      </div>
    );
  }

  if (!loading && deliveries.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
          <Send className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm text-gray-400">Nenhuma entrega encontrada</p>
        <p className="text-xs text-gray-300">Execute uma campanha para gerar registros de entrega</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            {['Campanha','Cliente','Canal','Status','Enviado em','Entregue em','Tentativas',''].map((h, i) => (
              <th key={i} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {deliveries.map((d) => (
            <DeliveryRow key={d.id} delivery={d} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
