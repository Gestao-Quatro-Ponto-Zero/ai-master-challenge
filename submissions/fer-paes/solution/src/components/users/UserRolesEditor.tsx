import { useState, useEffect } from 'react';
import { X, ShieldCheck } from 'lucide-react';
import { getRoles } from '../../services/roleService';
import { assignRoles } from '../../services/userService';
import { useAuth } from '../../contexts/AuthContext';
import type { UserWithProfile, Role } from '../../types';

interface Props {
  targetUser: UserWithProfile;
  onClose: () => void;
  onUpdated: () => void;
}

export default function UserRolesEditor({ targetUser, onClose, onUpdated }: Props) {
  const { user } = useAuth();
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>(
    targetUser.roles.map((r) => r.id)
  );
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getRoles()
      .then(setAllRoles)
      .catch(() => {})
      .finally(() => setFetching(false));
  }, []);

  function toggleRole(roleId: string) {
    setSelectedRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    );
  }

  async function handleSave() {
    setLoading(true);
    setError('');
    try {
      await assignRoles(targetUser.id, selectedRoleIds, user!.id);
      onUpdated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update roles');
      setLoading(false);
    }
  }

  const displayName = targetUser.profile?.full_name || targetUser.email;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Manage Roles</h2>
              <p className="text-xs text-gray-400 truncate max-w-[180px]">{displayName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-5">
          {fetching ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-14 rounded-xl bg-gray-100 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {allRoles.map((role) => (
                <label
                  key={role.id}
                  className="flex items-start gap-3 p-3.5 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/40 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={selectedRoleIds.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                    className="mt-0.5 w-4 h-4 rounded text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 capitalize">{role.name}</p>
                    {role.description && (
                      <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">
                        {role.description}
                      </p>
                    )}
                  </div>
                </label>
              ))}
            </div>
          )}

          {error && (
            <div className="mt-4 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="flex gap-3 mt-5">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading || fetching}
              className="flex-1 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving...' : 'Save Roles'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
