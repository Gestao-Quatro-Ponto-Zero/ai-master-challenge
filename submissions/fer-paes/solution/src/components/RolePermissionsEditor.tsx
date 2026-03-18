import { useState, useEffect } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { getAllPermissions, getRolePermissions, assignPermissionsToRole } from '../services/roleService';
import type { Permission, Role } from '../types';

interface RolePermissionsEditorProps {
  role: Role;
  onClose: () => void;
  onSaved: () => void;
}

export default function RolePermissionsEditor({ role, onClose, onSaved }: RolePermissionsEditorProps) {
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      const [all, current] = await Promise.all([
        getAllPermissions(),
        getRolePermissions(role.id),
      ]);
      setAllPermissions(all);
      setSelected(new Set(current.map((p) => p.id)));
      setIsLoading(false);
    }
    load();
  }, [role.id]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSave() {
    setIsSaving(true);
    setError('');
    try {
      await assignPermissionsToRole(role.id, [...selected]);
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save permissions.');
    } finally {
      setIsSaving(false);
    }
  }

  const grouped = allPermissions.reduce<Record<string, Permission[]>>((acc, p) => {
    if (!acc[p.category]) acc[p.category] = [];
    acc[p.category].push(p);
    return acc;
  }, {});

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-gray-900">Edit Permissions</h2>
            <p className="text-sm text-gray-500 mt-0.5 capitalize">{role.name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {isLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-5">
              {Object.entries(grouped).map(([category, perms]) => (
                <div key={category}>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2.5 capitalize">{category}</p>
                  <div className="space-y-2">
                    {perms.map((perm) => (
                      <label
                        key={perm.id}
                        className="flex items-start gap-3 cursor-pointer group"
                      >
                        <div className="mt-0.5">
                          <input
                            type="checkbox"
                            checked={selected.has(perm.id)}
                            onChange={() => toggle(perm.id)}
                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                          />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors">
                            {perm.name}
                          </p>
                          <p className="text-xs text-gray-400">{perm.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-100">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-3">
          <span className="text-xs text-gray-400">{selected.size} permissions selected</span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || isLoading}
              className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
            >
              {isSaving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
