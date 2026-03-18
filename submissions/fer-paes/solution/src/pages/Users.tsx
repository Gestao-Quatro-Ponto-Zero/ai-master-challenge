import { useState, useEffect, useCallback } from 'react';
import {
  Users as UsersIcon,
  Plus,
  Search,
  Pencil,
  ShieldCheck,
  Ban,
  RotateCcw,
  ChevronDown,
} from 'lucide-react';
import { getUsers, changeUserStatus } from '../services/userService';
import { getAllPresence, resolveStatus } from '../services/presenceService';
import { supabase } from '../lib/supabaseClient';
import { useAuth } from '../contexts/AuthContext';
import type { UserWithProfile, UserStatus, OperatorPresence } from '../types';
import UserCreateModal from '../components/users/UserCreateModal';
import UserEditModal from '../components/users/UserEditModal';
import UserRolesEditor from '../components/users/UserRolesEditor';
import { PresenceBadge, PresenceDot } from '../components/PresenceBadge';

type ModalState =
  | { type: 'none' }
  | { type: 'create' }
  | { type: 'edit'; target: UserWithProfile }
  | { type: 'roles'; target: UserWithProfile };

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-50 text-green-700 border-green-100',
  suspended: 'bg-red-50 text-red-700 border-red-100',
  invited: 'bg-amber-50 text-amber-700 border-amber-100',
};

function UserAvatar({ name, email }: { name?: string; email: string }) {
  const initials = name
    ? name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : email[0].toUpperCase();

  const colors = [
    'bg-blue-100 text-blue-700',
    'bg-teal-100 text-teal-700',
    'bg-orange-100 text-orange-700',
    'bg-rose-100 text-rose-700',
    'bg-violet-100 text-violet-700',
  ];
  const color = colors[email.charCodeAt(0) % colors.length];

  return (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${color}`}
    >
      {initials}
    </div>
  );
}

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserWithProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [presenceFilter, setPresenceFilter] = useState('');
  const [modal, setModal] = useState<ModalState>({ type: 'none' });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [presenceMap, setPresenceMap] = useState<Record<string, OperatorPresence>>({});

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const [data, presenceList] = await Promise.all([
        getUsers({ email: search || undefined, status: statusFilter || undefined }),
        getAllPresence(),
      ]);
      setUsers(data);
      const map: Record<string, OperatorPresence> = {};
      presenceList.forEach((p) => { map[p.user_id] = p; });
      setPresenceMap(map);
    } catch {
      /* no-op */
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    const channel = supabase
      .channel('presence-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'operator_presence' },
        (payload) => {
          const record = (payload.new ?? payload.old) as OperatorPresence;
          if (!record?.user_id) return;
          setPresenceMap((prev) => ({ ...prev, [record.user_id]: record }));
        },
      )
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, []);

  async function handleStatusChange(targetUser: UserWithProfile, newStatus: UserStatus) {
    setActionLoading(targetUser.id);
    try {
      await changeUserStatus(targetUser.id, newStatus, user!.id);
      await loadUsers();
    } catch {
      /* no-op */
    } finally {
      setActionLoading(null);
    }
  }

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    const matchesSearch =
      u.email.toLowerCase().includes(q) ||
      (u.profile?.full_name || '').toLowerCase().includes(q);
    const matchesPresence = !presenceFilter ||
      resolveStatus(presenceMap[u.id]) === presenceFilter;
    return matchesSearch && matchesPresence;
  });

  return (
    <div className="flex flex-col h-full">
      <div className="px-8 py-6 border-b border-gray-100 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <UsersIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Usuários</h1>
              <p className="text-sm text-gray-400">Gerencie membros e seus acessos</p>
            </div>
          </div>
          <button
            onClick={() => setModal({ type: 'create' })}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 active:scale-95 transition-all shadow-sm shadow-blue-200"
          >
            <Plus className="w-4 h-4" />
            Criar Usuário
          </button>
        </div>

        <div className="flex items-center gap-3 mt-5">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nome ou e-mail..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
            />
          </div>

          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="appearance-none pl-3.5 pr-8 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white cursor-pointer"
            >
              <option value="">Todos os Status</option>
              <option value="active">Ativo</option>
              <option value="invited">Convidado</option>
              <option value="suspended">Suspenso</option>
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          </div>

          <div className="relative">
            <select
              value={presenceFilter}
              onChange={(e) => setPresenceFilter(e.target.value)}
              className="appearance-none pl-3.5 pr-8 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white cursor-pointer"
            >
              <option value="">Toda Presença</option>
              <option value="online">Online</option>
              <option value="away">Ausente</option>
              <option value="busy">Ocupado</option>
              <option value="offline">Offline</option>
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-8 py-6">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-gray-100 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
              <UsersIcon className="w-7 h-7 text-gray-400" />
            </div>
            <p className="text-gray-600 font-medium">Nenhum usuário encontrado</p>
            <p className="text-gray-400 text-sm mt-1">
              {search || statusFilter ? 'Tente ajustar os filtros' : 'Crie o primeiro usuário para começar'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Usuário
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Presença
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Perfis
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Status
                  </th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Departamento
                  </th>
                  <th className="px-5 py-3.5" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((u) => {
                  const isCurrentUser = u.id === user?.id;
                  const isLoading = actionLoading === u.id;
                  const presence = resolveStatus(presenceMap[u.id]);

                  return (
                    <tr key={u.id} className="group hover:bg-gray-50/60 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="relative shrink-0">
                            <UserAvatar
                              name={u.profile?.full_name}
                              email={u.email}
                            />
                            <span className="absolute -bottom-0.5 -right-0.5">
                              <PresenceDot status={presence} size="sm" className="ring-2 ring-white" />
                            </span>
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {u.profile?.full_name || '—'}
                            </p>
                            <p className="text-xs text-gray-400 truncate">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <PresenceBadge status={presence} showLabel size="sm" />
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {u.roles.length === 0 ? (
                            <span className="text-xs text-gray-400">Sem perfis</span>
                          ) : (
                            u.roles.map((r) => (
                              <span
                                key={r.id}
                                className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium capitalize"
                              >
                                {r.name}
                              </span>
                            ))
                          )}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border capitalize ${
                            STATUS_COLORS[u.status] || 'bg-gray-50 text-gray-700 border-gray-100'
                          }`}
                        >
                          {u.status}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <span className="text-sm text-gray-500">
                          {u.profile?.department || '—'}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => setModal({ type: 'edit', target: u })}
                            title="Editar usuário"
                            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => setModal({ type: 'roles', target: u })}
                            title="Gerenciar perfis"
                            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          >
                            <ShieldCheck className="w-4 h-4" />
                          </button>

                          {!isCurrentUser && (
                            u.status === 'suspended' ? (
                              <button
                                onClick={() => handleStatusChange(u, 'active')}
                                disabled={isLoading}
                                title="Reativar usuário"
                                className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-green-600 hover:bg-green-50 transition-colors disabled:opacity-40"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </button>
                            ) : (
                              <button
                                onClick={() => handleStatusChange(u, 'suspended')}
                                disabled={isLoading}
                                title="Suspender usuário"
                                className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-40"
                              >
                                <Ban className="w-4 h-4" />
                              </button>
                            )
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div className="px-5 py-3.5 border-t border-gray-100 bg-gray-50/50">
              <p className="text-xs text-gray-400">
                {filtered.length} usuário{filtered.length !== 1 ? 's' : ''}
                {(search || statusFilter) ? ' correspondendo aos filtros' : ' no total'}
              </p>
            </div>
          </div>
        )}
      </div>

      {modal.type === 'create' && (
        <UserCreateModal
          onClose={() => setModal({ type: 'none' })}
          onCreated={loadUsers}
        />
      )}

      {modal.type === 'edit' && (
        <UserEditModal
          targetUser={modal.target}
          onClose={() => setModal({ type: 'none' })}
          onUpdated={loadUsers}
        />
      )}

      {modal.type === 'roles' && (
        <UserRolesEditor
          targetUser={modal.target}
          onClose={() => setModal({ type: 'none' })}
          onUpdated={loadUsers}
        />
      )}
    </div>
  );
}
