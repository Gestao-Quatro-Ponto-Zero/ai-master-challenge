import { useState, useEffect } from 'react';
import { UserCheck, Search, X, Loader2 } from 'lucide-react';
import { getUsers } from '../../services/userService';
import { getAllPresence, resolveStatus } from '../../services/presenceService';
import type { TicketWithRelations, UserWithProfile, OperatorPresence } from '../../types';
import { shortId } from './ticketConfig';
import { PresenceDot } from '../PresenceBadge';

interface Props {
  ticket: TicketWithRelations;
  currentUserId: string;
  onConfirm: (userId: string) => void;
  onClose: () => void;
  loading?: boolean;
}

export default function AssignTicketModal({ ticket, currentUserId, onConfirm, onClose, loading }: Props) {
  const [users, setUsers] = useState<UserWithProfile[]>([]);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string>(currentUserId);
  const [presenceMap, setPresenceMap] = useState<Record<string, OperatorPresence>>({});

  useEffect(() => {
    Promise.all([getUsers({ status: 'active' }), getAllPresence()]).then(([usrs, presenceList]) => {
      setUsers(usrs);
      const map: Record<string, OperatorPresence> = {};
      presenceList.forEach((p) => { map[p.user_id] = p; });
      setPresenceMap(map);
    }).finally(() => setFetching(false));
  }, []);

  const filtered = users.filter((u) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (u.profile?.full_name || '').toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q)
    );
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 flex flex-col overflow-hidden"
        style={{ maxHeight: '85vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
              <UserCheck className="w-4.5 h-4.5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Assign Ticket</h2>
              <p className="text-xs text-gray-400">#{shortId(ticket.id)}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 pt-3.5 pb-2 border-b border-gray-50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search operators..."
              className="w-full pl-8 pr-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400/30 focus:border-blue-300 transition-all"
              style={{ paddingLeft: '2rem' }}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2 min-h-0">
          {fetching ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-400">No operators found</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {filtered.map((u) => {
                const isSelected = selected === u.id;
                const isCurrentUser = u.id === currentUserId;
                const name = u.profile?.full_name || u.email;
                const initials = name[0].toUpperCase();
                const presence = resolveStatus(presenceMap[u.id]);

                return (
                  <button
                    key={u.id}
                    onClick={() => setSelected(u.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                      isSelected
                        ? 'bg-blue-50 border border-blue-100'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <div className="relative shrink-0">
                      <div
                        className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold ${
                          isSelected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {initials}
                      </div>
                      <span className="absolute -bottom-0.5 -right-0.5">
                        <PresenceDot status={presence} size="sm" className="ring-2 ring-white" />
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-800 truncate">{name}</p>
                        {isCurrentUser && (
                          <span className="text-xs px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-600 font-medium shrink-0">
                            me
                          </span>
                        )}
                      </div>
                      {u.profile?.full_name && (
                        <p className="text-xs text-gray-400 truncate">{u.email}</p>
                      )}
                      {u.profile?.department && (
                        <p className="text-xs text-gray-400">{u.profile.department}</p>
                      )}
                    </div>
                    {isSelected && (
                      <div className="w-4.5 h-4.5 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                        <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 px-5 py-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(selected)}
            disabled={loading || fetching}
            className="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <UserCheck className="w-4 h-4" />
            )}
            Assign
          </button>
        </div>
      </div>
    </div>
  );
}
