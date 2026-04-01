import { LayoutDashboard, Target, History, LogOut, Sun, Moon } from 'lucide-react'

interface Props {
  activePage: string
  onNavigate: (page: string) => void
  profile: { email: string; role: string }
  onSignOut: () => void
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'pipeline', label: 'Pipeline', icon: Target },
  { id: 'history', label: 'Histórico', icon: History },
]

export function Sidebar({ activePage, onNavigate, profile, onSignOut, theme, onToggleTheme }: Props) {
  return (
    <aside className="w-56 h-screen fixed left-0 top-0 bg-[var(--bg-sidebar)] flex flex-col z-40">
      <div className="p-5 border-b border-white/10">
        <h1 className="text-lg font-bold text-white tracking-tight">Lead Scorer</h1>
        <p className="text-[10px] text-white/40 mt-0.5 font-medium tracking-wider uppercase">Priorização Inteligente</p>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activePage === item.id
                  ? 'bg-[var(--g4-gold)]/20 text-[var(--g4-gold-light)]'
                  : 'text-white/50 hover:text-white/80 hover:bg-white/5'
              }`}
            >
              <Icon size={18} strokeWidth={1.8} />
              {item.label}
            </button>
          )
        })}
      </nav>

      <div className="p-4 border-t border-white/10 space-y-3">
        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors"
        >
          {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
          {theme === 'light' ? 'Modo escuro' : 'Modo claro'}
        </button>

        {/* User */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[var(--g4-gold)]/20 flex items-center justify-center text-xs font-bold text-[var(--g4-gold)]">
            {profile.email.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-white/80 truncate">{profile.email}</p>
            <p className="text-[10px] text-white/40 capitalize">{profile.role}</p>
          </div>
        </div>
        <button
          onClick={onSignOut}
          className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors border border-white/10"
        >
          <LogOut size={14} strokeWidth={1.8} />
          Sair
        </button>
      </div>
    </aside>
  )
}
