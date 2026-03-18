import { useState } from 'react';
import { Phone, PhoneIncoming, FileText, MessageSquarePlus, Clock, User, Send, ChevronUp } from 'lucide-react';
import type { MessageWithAttachments } from '../../services/messageService';
import type { TicketWithRelations } from '../../types';
import ResolutionPanel from './ResolutionPanel';

function formatCallDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatCallTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function formatNoteDate(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  const timeStr = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

  if (date.toDateString() === today.toDateString()) return `Hoje, ${timeStr}`;
  if (date.toDateString() === yesterday.toDateString()) return `Ontem, ${timeStr}`;
  return date.toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface PhoneCallViewProps {
  ticket: TicketWithRelations;
  messages: MessageWithAttachments[];
  hasMore: boolean;
  onLoadMore: () => void;
  loadingMore?: boolean;
  onAddNote: (text: string) => Promise<void>;
  readonly?: boolean;
  onResolutionSaved?: (notes: string) => void;
}

export default function PhoneCallView({
  ticket,
  messages,
  hasMore,
  onLoadMore,
  loadingMore,
  onAddNote,
  readonly = false,
  onResolutionSaved,
}: PhoneCallViewProps) {
  const [noteText, setNoteText] = useState('');
  const [sendingNote, setSendingNote] = useState(false);

  const operatorNotes = messages.filter(
    (m) => m.sender_type === 'operator' || m.sender_type === 'agent',
  );
  const initialDescription = ticket.description;

  async function handleSendNote() {
    const trimmed = noteText.trim();
    if (!trimmed || sendingNote) return;
    setSendingNote(true);
    try {
      await onAddNote(trimmed);
      setNoteText('');
    } finally {
      setSendingNote(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendNote();
    }
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-6 space-y-5">
      <div className="max-w-2xl mx-auto space-y-5">

        <div className="rounded-2xl bg-white border border-gray-200 overflow-hidden shadow-sm">
          <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-5 py-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center shrink-0">
              <PhoneIncoming className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold text-base">
                {ticket.customer?.name || 'Cliente desconhecido'}
              </p>
              {ticket.customer?.phone ? (
                <p className="text-slate-300 text-sm mt-0.5 flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5" />
                  {ticket.customer.phone}
                </p>
              ) : (
                <p className="text-slate-400 text-sm mt-0.5">Número não registrado</p>
              )}
            </div>
            <div className="text-right shrink-0">
              <p className="text-slate-300 text-xs">{formatCallDate(ticket.created_at)}</p>
              <p className="text-white font-semibold text-sm mt-0.5 flex items-center gap-1 justify-end">
                <Clock className="w-3.5 h-3.5 text-slate-300" />
                {formatCallTime(ticket.created_at)}
              </p>
            </div>
          </div>

          <div className="px-5 py-4 grid grid-cols-2 gap-4 border-b border-gray-100">
            <div>
              <p className="text-xs text-gray-400 mb-1">Canal</p>
              <p className="text-sm font-medium text-gray-700">{ticket.channel?.name ?? 'Telefone'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Assunto</p>
              <p className="text-sm font-medium text-gray-700 truncate">{ticket.subject || '—'}</p>
            </div>
            {ticket.customer?.email && (
              <div className="col-span-2">
                <p className="text-xs text-gray-400 mb-1">E-mail do cliente</p>
                <p className="text-sm text-gray-600">{ticket.customer.email}</p>
              </div>
            )}
          </div>

          {initialDescription && (
            <div className="px-5 py-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                </div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Motivo do Contato</p>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap pl-8">
                {initialDescription}
              </p>
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-white border border-gray-200 overflow-hidden shadow-sm">
          <div className="px-5 py-3.5 border-b border-gray-100 flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
              <FileText className="w-3.5 h-3.5 text-amber-600" />
            </div>
            <p className="text-sm font-semibold text-gray-700">Tratativas</p>
            <span className="ml-auto text-xs text-gray-400 font-medium tabular-nums">
              {operatorNotes.length} {operatorNotes.length === 1 ? 'nota' : 'notas'}
            </span>
          </div>

          {hasMore && (
            <div className="flex justify-center py-3 border-b border-gray-50">
              <button
                onClick={onLoadMore}
                disabled={loadingMore}
                className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-gray-100 text-xs text-gray-500 hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                <ChevronUp className="w-3.5 h-3.5" />
                {loadingMore ? 'Carregando...' : 'Carregar notas anteriores'}
              </button>
            </div>
          )}

          {operatorNotes.length === 0 ? (
            <div className="px-5 py-8 text-center">
              <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
                <MessageSquarePlus className="w-5 h-5 text-gray-400" />
              </div>
              <p className="text-sm font-medium text-gray-500">Nenhuma tratativa registrada</p>
              <p className="text-xs text-gray-400 mt-1">
                Use o campo abaixo para registrar o que foi tratado durante a ligação
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {operatorNotes.map((note) => (
                <div key={note.id} className="px-5 py-4">
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700 shrink-0 mt-0.5">
                      O
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-semibold text-gray-600">
                          {note.sender_type === 'agent' ? 'Agente IA' : 'Operador'}
                        </span>
                        <span className="text-xs text-gray-400 shrink-0">{formatNoteDate(note.created_at)}</span>
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {note.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!readonly && (
            <div className="px-5 py-4 border-t border-gray-100 bg-gray-50/50">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700 shrink-0 mt-1">
                  O
                </div>
                <div className="flex-1">
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={sendingNote}
                    placeholder="Registre o que foi tratado durante a ligação... (Enter para salvar)"
                    rows={3}
                    className="w-full text-sm text-gray-700 bg-white border border-gray-200 rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-300 placeholder:text-gray-400 leading-relaxed transition-all disabled:opacity-60"
                  />
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-xs text-gray-400">Enter para registrar · Shift+Enter para nova linha</p>
                    <button
                      onClick={handleSendNote}
                      disabled={!noteText.trim() || sendingNote}
                      className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-sm font-medium transition-all ${
                        noteText.trim() && !sendingNote
                          ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-100'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {sendingNote ? (
                        <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                      ) : (
                        <Send className="w-3.5 h-3.5" />
                      )}
                      Registrar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <ResolutionPanel
          ticketId={ticket.id}
          initialNotes={ticket.resolution_notes}
          readonly={readonly}
          onSaved={onResolutionSaved}
        />

        <div className="pb-4" />
      </div>
    </div>
  );
}
