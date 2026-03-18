import { useState, useEffect, useCallback } from 'react';
import { Plus, Pencil, ShieldCheck, Loader2, AlertCircle, X, Check } from 'lucide-react';
import { getRolesWithPermissions, createRole, updateRole } from '../services/roleService';
import RolePermissionsEditor from '../components/RolePermissionsEditor';
import type { RoleWithPermissions, Role } from '../types';

function RoleFormModal({
  role,
  onClose,
  onSaved,
}: {
  role?: Role;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(role?.name || '');
  const [description, setDescription] = useState(role?.description || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!name.trim()) {
      setError('O nome do perfil é obrigatório.');
      return;
    }
    setIsSaving(true);
    setError('');
    try {
      if (role) {
        await updateRole(role.id, { name: name.trim(), description: description.trim() });
      } else {
        await createRole(name.trim(), description.trim());
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar perfil.');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">{role ? 'Editar Perfil' : 'Novo Perfil'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Nome</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ex: supervisor"
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Descrição</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva o que este perfil pode fazer..."
              rows={3}
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors">
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
          >
            {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}

function PermissionBadge({ name }: { name: string }) {
  const cat = name.split('.')[0];
  const colorMap: Record<string, string> = {
    users: 'bg-blue-50 text-blue-700',
    roles: 'bg-emerald-50 text-emerald-700',
    tickets: 'bg-amber-50 text-amber-700',
    reports: 'bg-sky-50 text-sky-700',
    settings: 'bg-red-50 text-red-700',
  };
  const color = colorMap[cat] || 'bg-gray-50 text-gray-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium ${color}`}>{name}</span>
  );
}

export default function Roles() {
  const [roles, setRoles] = useState<RoleWithPermissions[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingRole, setEditingRole] = useState<Role | undefined>();
  const [editingPermsRole, setEditingPermsRole] = useState<Role | undefined>();
  const [showNewModal, setShowNewModal] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getRolesWithPermissions();
      setRoles(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar perfis.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Perfis de Acesso</h1>
          <p className="text-gray-500 mt-1 text-sm">Gerencie perfis e suas permissões associadas.</p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Novo Perfil
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2.5 bg-red-50 border border-red-100 rounded-xl px-4 py-3 mb-6">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">Perfil</th>
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">Descrição</th>
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">Permissões</th>
                <th className="text-right px-6 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">Ações</th>
              </tr>
            </thead>
            <tbody>
              {roles.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-sm text-gray-400">Nenhum perfil encontrado.</td>
                </tr>
              ) : (
                roles.map((role, idx) => (
                  <tr key={role.id} className={idx < roles.length - 1 ? 'border-b border-gray-50' : ''}>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                          <ShieldCheck className="w-4 h-4 text-slate-500" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900 capitalize">{role.name}</p>
                          {role.is_system && (
                            <span className="text-xs text-gray-400">Perfil do sistema</span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-500 max-w-xs">{role.description || '—'}</p>
                    </td>
                    <td className="px-6 py-4">
                      {role.permissions.length === 0 ? (
                        <span className="text-xs text-gray-400">Nenhuma</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5 max-w-xs">
                          {role.permissions.slice(0, 4).map((p) => (
                            <PermissionBadge key={p.id} name={p.name} />
                          ))}
                          {role.permissions.length > 4 && (
                            <span className="text-xs text-gray-400 self-center">+{role.permissions.length - 4} mais</span>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setEditingRole(role)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-lg transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                          Editar
                        </button>
                        <button
                          onClick={() => setEditingPermsRole(role)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Permissões
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showNewModal && (
        <RoleFormModal
          onClose={() => setShowNewModal(false)}
          onSaved={load}
        />
      )}

      {editingRole && (
        <RoleFormModal
          role={editingRole}
          onClose={() => setEditingRole(undefined)}
          onSaved={load}
        />
      )}

      {editingPermsRole && (
        <RolePermissionsEditor
          role={editingPermsRole}
          onClose={() => setEditingPermsRole(undefined)}
          onSaved={load}
        />
      )}
    </div>
  );
}
