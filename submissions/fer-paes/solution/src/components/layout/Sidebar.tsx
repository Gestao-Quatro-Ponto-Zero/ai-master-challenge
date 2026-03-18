import { useState, useRef, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, ShieldCheck, LogOut, Shield,
  CircleUser as UserCircle, ClipboardList, Ticket, Contact, Zap,
  MessageSquare, ChevronDown, Bot, BookOpen, Headphones, ListOrdered,
  Activity, MonitorSpeaker, BarChart2, Cpu, Database, DollarSign,
  Route, SlidersHorizontal, Wallet, TrendingUp, PieChart, Rss,
  Layers, Megaphone, Clock, Send, LineChart, ChevronRight, FileUp,
  Code2, Key,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { logout } from '../../services/authService';
import { PermissionGuard } from '../PermissionGuard';
import { PresenceDot, PRESENCE_OPTIONS } from '../PresenceBadge';
import { usePresence } from '../../hooks/usePresence';
import type { OperatorStatus } from '../../types';

interface NavItem {
  label:       string;
  to:          string;
  icon:        React.ComponentType<{ className?: string }>;
  permission?: string;
}

interface NavGroup {
  label:  string;
  accent: string;
  items:  NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label:  'Geral',
    accent: '#00aeff',
    items: [
      { label: 'Painel', to: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label:  'Atendimento',
    accent: '#3fffff',
    items: [
      { label: 'Área de Trabalho', to: '/workspace', icon: MonitorSpeaker, permission: 'tickets.handle' },
      { label: 'Tickets',          to: '/tickets',   icon: Ticket },
      { label: 'Clientes',         to: '/customers', icon: Contact },
    ],
  },
  {
    label:  'CRM & Campanhas',
    accent: '#6aff6b',
    items: [
      { label: 'Análise de Clientes', to: '/customer-analytics',  icon: PieChart,         permission: 'analytics.view'            },
      { label: 'Eventos',             to: '/events',               icon: Rss,              permission: 'events.view'               },
      { label: 'Segmentos',           to: '/segments',             icon: Layers,           permission: 'segments.manage'           },
      { label: 'Campanhas',           to: '/campaigns',            icon: Megaphone,        permission: 'campaigns.manage'          },
      { label: 'Agendador',           to: '/campaign-scheduler',   icon: Clock,            permission: 'campaign_scheduler.manage' },
      { label: 'Entregas',            to: '/campaign-deliveries',  icon: Send,             permission: 'campaigns.view'            },
      { label: 'Analytics',           to: '/campaign-analytics',   icon: LineChart,        permission: 'campaigns.analytics'       },
    ],
  },
  {
    label:  'Operações',
    accent: '#ffbc00',
    items: [
      { label: 'Operadores', to: '/operators',  icon: Headphones,  permission: 'operators.manage'   },
      { label: 'Filas',      to: '/queues',     icon: ListOrdered, permission: 'queues.manage'      },
      { label: 'Supervisor', to: '/supervisor', icon: Activity,    permission: 'operations.monitor' },
      { label: 'Métricas',   to: '/metrics',    icon: BarChart2,   permission: 'metrics.view'       },
    ],
  },
  {
    label:  'Inteligência IA',
    accent: '#3fffff',
    items: [
      { label: 'Agentes',      to: '/agents',       icon: Bot,               permission: 'agents.view'         },
      { label: 'Conhecimento', to: '/knowledge',    icon: BookOpen,          permission: 'knowledge.view'      },
      { label: 'Modelos LLM',  to: '/llm-models',   icon: Cpu,               permission: 'llm_models.manage'   },
      { label: 'Logs LLM',     to: '/llm-logs',     icon: Database,          permission: 'llm_logs.view'       },
      { label: 'Tokens',       to: '/token-usage',  icon: BarChart2,         permission: 'llm_usage.view'      },
      { label: 'Custos LLM',   to: '/llm-costs',    icon: DollarSign,        permission: 'llm_costs.view'      },
      { label: 'Roteador',     to: '/llm-router',   icon: Route,             permission: 'system.internal'     },
      { label: 'Políticas',    to: '/llm-policies', icon: SlidersHorizontal, permission: 'llm_policies.manage' },
      { label: 'Orçamentos',   to: '/llm-budgets',  icon: Wallet,            permission: 'llm_budget.manage'   },
      { label: 'Uso de IA',    to: '/ai-usage',     icon: TrendingUp,        permission: 'ai_usage.view'       },
    ],
  },
  {
    label:  'Integrações',
    accent: '#22c55e',
    items: [
      { label: 'Chaves de API',    to: '/integrations', icon: Key,   permission: 'integrations.manage' },
      { label: 'Documentação',     to: '/developers',   icon: Code2, permission: 'integrations.manage' },
    ],
  },
  {
    label:  'Configurações',
    accent: '#8a96ae',
    items: [
      { label: 'Usuários',         to: '/users',       icon: Users,         permission: 'users.manage' },
      { label: 'Perfis de Acesso', to: '/roles',       icon: ShieldCheck,   permission: 'roles.manage' },
      { label: 'Automações',       to: '/automations', icon: Zap,           permission: 'roles.manage' },
      { label: 'Macros',           to: '/macros',      icon: MessageSquare, permission: 'roles.manage' },
      { label: 'Auditoria',        to: '/audit',       icon: ClipboardList, permission: 'roles.manage' },
      { label: 'Importar CSV',     to: '/import',      icon: FileUp,        permission: 'roles.manage' },
    ],
  },
];

const STATUS_LABEL: Record<OperatorStatus, string> = {
  online:  'Online',
  away:    'Ausente',
  busy:    'Ocupado',
  offline: 'Offline',
};

function GroupSection({ group }: { group: NavGroup }) {
  const [open, setOpen] = useState(true);

  const items = group.items.map((item) => {
    const link = (
      <NavLink
        key={item.to}
        to={item.to}
        className={({ isActive }) =>
          `relative flex items-center gap-2.5 pl-4 pr-3 py-[7px] rounded-lg text-[13px] font-medium transition-all duration-150 ${
            isActive
              ? 'text-white'
              : 'text-slate-500 hover:text-slate-200 hover:bg-white/5'
          }`
        }
      >
        {({ isActive }) => (
          <>
            {isActive && (
              <span
                className="absolute inset-0 rounded-lg opacity-15"
                style={{ background: `linear-gradient(90deg, ${group.accent}44, transparent)` }}
              />
            )}
            {isActive && (
              <span
                className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4/5 rounded-full"
                style={{ background: group.accent, boxShadow: `0 0 8px ${group.accent}` }}
              />
            )}
            <item.icon
              className="w-3.5 h-3.5 shrink-0 relative z-10"
              style={isActive ? { color: group.accent } : undefined}
            />
            <span className="truncate relative z-10">{item.label}</span>
          </>
        )}
      </NavLink>
    );

    if (item.permission) {
      return (
        <PermissionGuard key={item.to} permission={item.permission} fallback={null}>
          {link}
        </PermissionGuard>
      );
    }
    return link;
  });

  return (
    <div className="mb-0.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-1.5 group rounded-md hover:bg-white/3 transition-colors"
      >
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0 opacity-70"
          style={{ background: group.accent }}
        />
        <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-600 group-hover:text-slate-500 transition-colors flex-1 text-left">
          {group.label}
        </span>
        <ChevronRight
          className={`w-3 h-3 text-slate-700 transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
        />
      </button>

      <div
        className={`overflow-hidden transition-all duration-200 ${open ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="space-y-0.5 pl-2 pb-1">
          {items}
        </div>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const { profile, roles, user } = useAuth();
  const navigate = useNavigate();
  const { status, updateStatus } = usePresence(user?.id);
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowStatusMenu(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  const displayName = profile?.full_name || profile?.email || 'Usuário';
  const roleName    = roles[0]?.name ?? '';

  return (
    <aside
      className="w-56 flex flex-col shrink-0 h-full"
      style={{
        background: 'linear-gradient(180deg, #0a0d16 0%, #0d1120 100%)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      <div className="px-4 py-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{
              background: 'linear-gradient(135deg, #00aeff, #3fffff)',
              boxShadow: '0 0 16px rgba(0,174,255,0.4)',
            }}
          >
            <Shield className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold text-sm tracking-tight">AccessControl</span>
        </div>
      </div>

      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-0.5">
        {navGroups.map((group) => (
          <GroupSection key={group.label} group={group} />
        ))}
      </nav>

      <div className="px-2 py-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 mb-1 rounded-lg transition-colors ${
              isActive ? 'bg-white/10' : 'hover:bg-white/5'
            }`
          }
        >
          <div className="relative w-7 h-7 shrink-0">
            <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: 'rgba(0,174,255,0.15)', border: '1px solid rgba(0,174,255,0.3)' }}>
              <UserCircle className="w-4 h-4" style={{ color: '#00aeff' }} />
            </div>
            <span className="absolute -bottom-0.5 -right-0.5">
              <PresenceDot status={status} size="sm" className="ring-2 ring-[#0a0d16]" />
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-white text-sm font-medium truncate">{displayName}</p>
            {roleName && (
              <span className="text-xs text-slate-500 capitalize">{roleName}</span>
            )}
          </div>
        </NavLink>

        <div className="relative px-3 mb-1" ref={menuRef}>
          <button
            onClick={() => setShowStatusMenu((v) => !v)}
            className="w-full flex items-center gap-2 py-1.5 text-slate-500 hover:text-slate-300 transition-colors group"
          >
            <PresenceDot status={status} size="sm" />
            <span className="text-xs font-medium flex-1 text-left">{STATUS_LABEL[status]}</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showStatusMenu ? 'rotate-180' : ''}`} />
          </button>

          {showStatusMenu && (
            <div
              className="absolute bottom-full left-0 right-0 mb-1 rounded-xl overflow-hidden z-50"
              style={{
                background: '#111827',
                border: '1px solid rgba(255,255,255,0.08)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
              }}
            >
              {PRESENCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { updateStatus(opt.value); setShowStatusMenu(false); }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-sm transition-colors ${
                    status === opt.value
                      ? 'bg-white/10 text-white'
                      : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <PresenceDot status={opt.value} size="sm" />
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          Sair
        </button>
      </div>
    </aside>
  );
}
