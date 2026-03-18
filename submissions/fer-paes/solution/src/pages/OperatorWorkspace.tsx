import { useState, useCallback } from 'react';
import { Headphones, MessageCircle, MonitorSpeaker } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { usePresence } from '../hooks/usePresence';
import TicketSidebar             from '../components/workspace/TicketSidebar';
import ConversationPanel         from '../components/workspace/ConversationPanel';
import CustomerPanel             from '../components/workspace/CustomerPanel';
import OperatorPresenceSelector  from '../components/workspace/OperatorPresenceSelector';
import type { WorkspaceTicket }  from '../services/workspaceService';

export default function OperatorWorkspace() {
  const { user, profile } = useAuth();
  const [selectedTicket, setSelectedTicket] = useState<WorkspaceTicket | null>(null);
  const [refreshKey,     setRefreshKey]     = useState(0);

  const userId = user?.id ?? '';
  const { status: presenceStatus, updateStatus } = usePresence(userId || undefined);

  const handleTicketUpdated = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  const handleSelect = useCallback((ticket: WorkspaceTicket) => {
    setSelectedTicket(ticket);
  }, []);

  return (
    <div className="flex flex-col h-full overflow-hidden bg-slate-950">
      {/* Barra superior */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 shrink-0 bg-slate-950/80 backdrop-blur-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-blue-600/15 flex items-center justify-center">
            <MonitorSpeaker className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-none">Área de Trabalho do Operador</h1>
            {profile?.full_name && (
              <p className="text-xs text-slate-600 mt-0.5">{profile.full_name}</p>
            )}
          </div>
        </div>

        <OperatorPresenceSelector
          status={presenceStatus}
          onChange={updateStatus}
        />
      </div>

      {/* Layout de três painéis */}
      <div className="flex flex-1 overflow-hidden">
        {/* Esquerda: lista de tickets */}
        <div className="w-72 shrink-0">
          <TicketSidebar
            key={refreshKey}
            userId={userId}
            selectedId={selectedTicket?.id ?? null}
            onSelect={handleSelect}
          />
        </div>

        {/* Centro: conversa */}
        <div className="flex-1 min-w-0">
          {selectedTicket ? (
            <ConversationPanel
              key={selectedTicket.id}
              ticket={selectedTicket}
              userId={userId}
              onUpdated={handleTicketUpdated}
            />
          ) : (
            <EmptyState presenceStatus={presenceStatus} />
          )}
        </div>

        {/* Direita: informações do cliente e ticket */}
        <div className="w-72 shrink-0">
          {selectedTicket ? (
            <CustomerPanel
              key={selectedTicket.id + refreshKey}
              ticket={selectedTicket}
            />
          ) : (
            <div className="h-full bg-slate-950 border-l border-white/5" />
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ presenceStatus }: { presenceStatus: string }) {
  const isUnavailable = presenceStatus === 'offline' || presenceStatus === 'away';

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8">
      <div className={`w-16 h-16 rounded-2xl border flex items-center justify-center ${
        isUnavailable ? 'bg-slate-900/60 border-white/5' : 'bg-blue-600/10 border-blue-500/20'
      }`}>
        <Headphones className={`w-7 h-7 ${isUnavailable ? 'text-slate-700' : 'text-blue-400'}`} />
      </div>
      <div className="text-center">
        <h3 className="text-sm font-semibold text-slate-400 mb-1">
          {isUnavailable ? 'Você está indisponível' : 'Nenhum ticket selecionado'}
        </h3>
        <p className="text-xs text-slate-700 leading-relaxed max-w-xs">
          {isUnavailable
            ? 'Altere seu status para Online para começar a receber e atender tickets.'
            : 'Escolha um ticket da lista à esquerda para iniciar uma conversa com o cliente.'
          }
        </p>
      </div>
      <div className="flex items-center gap-2 mt-2">
        <MessageCircle className="w-3.5 h-3.5 text-slate-700" />
        <span className="text-xs text-slate-700">Área de Trabalho do Operador</span>
      </div>
    </div>
  );
}
