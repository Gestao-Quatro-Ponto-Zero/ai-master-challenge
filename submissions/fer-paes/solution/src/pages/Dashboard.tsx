import { useAuth } from '../contexts/AuthContext';
import { useAuthorization } from '../hooks/useAuthorization';
import { User, ShieldCheck, Key, Clock, TrendingUp } from 'lucide-react';
import TicketStats from '../components/dashboard/TicketStats';
import type { Permission, Role } from '../types';

interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  accent: string;
  glow: string;
}

function StatCard({ icon: Icon, label, value, accent, glow }: StatCardProps) {
  return (
    <div
      className="rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden group transition-all duration-200"
      style={{
        background: 'rgba(20,27,45,0.7)',
        border: `1px solid ${accent}22`,
        boxShadow: `0 0 0 1px rgba(255,255,255,0.04)`,
      }}
    >
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ background: `radial-gradient(ellipse at left, ${glow} 0%, transparent 60%)` }}
      />
      <div
        className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 relative z-10"
        style={{ background: `${accent}18`, border: `1px solid ${accent}30` }}
      >
        <Icon className="w-5 h-5" style={{ color: accent }} />
      </div>
      <div className="relative z-10">
        <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
        <p className="text-sm mt-0.5" style={{ color: '#68748e' }}>{label}</p>
      </div>
      <div
        className="absolute right-0 top-0 bottom-0 w-1 rounded-r-2xl"
        style={{ background: `linear-gradient(180deg, ${accent}, transparent)`, opacity: 0.5 }}
      />
    </div>
  );
}

function RoleBadge({ role }: { role: Role }) {
  const map: Record<string, { bg: string; color: string; glow: string }> = {
    admin:      { bg: 'rgba(255,80,80,0.1)',  color: '#ff5050', glow: '#ff5050' },
    supervisor: { bg: 'rgba(255,188,0,0.1)',  color: '#ffbc00', glow: '#ffbc00' },
    operator:   { bg: 'rgba(0,174,255,0.1)',  color: '#00aeff', glow: '#00aeff' },
    viewer:     { bg: 'rgba(138,150,174,0.1)', color: '#8a96ae', glow: '#8a96ae' },
  };
  const s = map[role.name] || map.viewer;

  return (
    <span
      className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold capitalize"
      style={{ background: s.bg, color: s.color, border: `1px solid ${s.glow}28`, boxShadow: `0 0 8px ${s.glow}18` }}
    >
      {role.name}
    </span>
  );
}

function PermissionTag({ permission }: { permission: Permission }) {
  const map: Record<string, string> = {
    users:    '#00aeff',
    roles:    '#6aff6b',
    tickets:  '#ffbc00',
    reports:  '#3fffff',
    settings: '#ff5050',
  };
  const color = map[permission.category] || '#8a96ae';

  return (
    <span
      className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium"
      style={{ background: `${color}12`, color, border: `1px solid ${color}20` }}
    >
      {permission.name}
    </span>
  );
}

export default function Dashboard() {
  const { user, profile, roles, permissions } = useAuth();
  const { hasPermission } = useAuthorization();
  const canViewAnalytics = hasPermission('analytics.view');

  const displayName = profile?.full_name || user?.email || 'Usuário';
  const joinedDate = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('pt-BR', { month: 'short', day: 'numeric', year: 'numeric' })
    : '—';

  const grouped = permissions.reduce<Record<string, Permission[]>>((acc, p) => {
    if (!acc[p.category]) acc[p.category] = [];
    acc[p.category].push(p);
    return acc;
  }, {});

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <TrendingUp className="w-4 h-4" style={{ color: '#00aeff' }} />
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#4d5a72' }}>Visão Geral</span>
        </div>
        <h1 className="text-2xl font-bold text-white">
          Bem-vindo de volta, <span style={{ color: '#00aeff' }}>{displayName.split(' ')[0]}</span>
        </h1>
        <p className="mt-1 text-sm" style={{ color: '#68748e' }}>Resumo da sua conta e nível de acesso.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard icon={User}       label="Status da conta"    value={profile?.status || 'Ativo'} accent="#00aeff" glow="rgba(0,174,255,0.1)"   />
        <StatCard icon={ShieldCheck} label="Perfis atribuídos" value={roles.length}                accent="#6aff6b" glow="rgba(106,255,107,0.1)" />
        <StatCard icon={Key}         label="Permissões"        value={permissions.length}          accent="#ffbc00" glow="rgba(255,188,0,0.1)"   />
      </div>

      {canViewAnalytics && (
        <TicketStats className="mb-8" />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div
          className="rounded-2xl p-6"
          style={{
            background: 'rgba(20,27,45,0.7)',
            border: '1px solid rgba(0,174,255,0.1)',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.04)',
          }}
        >
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <User className="w-4 h-4" style={{ color: '#00aeff' }} />
            Informações da Conta
          </h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: '#4d5a72' }}>E-mail</dt>
              <dd className="text-sm" style={{ color: '#cdd6e8' }}>{user?.email || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: '#4d5a72' }}>Nome Completo</dt>
              <dd className="text-sm" style={{ color: '#cdd6e8' }}>{profile?.full_name || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: '#4d5a72' }}>Status</dt>
              <dd>
                <span className="inline-flex items-center gap-1.5 text-sm">
                  <span className="w-2 h-2 rounded-full" style={{ background: '#6aff6b', boxShadow: '0 0 6px rgba(106,255,107,0.6)' }} />
                  <span style={{ color: '#cdd6e8' }} className="capitalize">{profile?.status || 'ativo'}</span>
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide mb-0.5 flex items-center gap-1" style={{ color: '#4d5a72' }}>
                <Clock className="w-3 h-3" /> Membro desde
              </dt>
              <dd className="text-sm" style={{ color: '#cdd6e8' }}>{joinedDate}</dd>
            </div>
          </dl>
        </div>

        <div
          className="rounded-2xl p-6"
          style={{
            background: 'rgba(20,27,45,0.7)',
            border: '1px solid rgba(106,255,107,0.1)',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.04)',
          }}
        >
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" style={{ color: '#6aff6b' }} />
            Perfis Atribuídos
          </h2>
          {roles.length === 0 ? (
            <p className="text-sm" style={{ color: '#4d5a72' }}>Nenhum perfil atribuído.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {roles.map((r) => <RoleBadge key={r.id} role={r} />)}
            </div>
          )}
        </div>

        <div
          className="rounded-2xl p-6 lg:col-span-2"
          style={{
            background: 'rgba(20,27,45,0.7)',
            border: '1px solid rgba(255,188,0,0.1)',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.04)',
          }}
        >
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Key className="w-4 h-4" style={{ color: '#ffbc00' }} />
            Permissões
          </h2>
          {permissions.length === 0 ? (
            <p className="text-sm" style={{ color: '#4d5a72' }}>Nenhuma permissão atribuída.</p>
          ) : (
            <div className="space-y-4">
              {Object.entries(grouped).map(([category, perms]) => (
                <div key={category}>
                  <p
                    className="text-xs font-semibold uppercase tracking-wide mb-2 capitalize"
                    style={{ color: '#4d5a72' }}
                  >
                    {category}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {perms.map((p) => <PermissionTag key={p.id} permission={p} />)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
