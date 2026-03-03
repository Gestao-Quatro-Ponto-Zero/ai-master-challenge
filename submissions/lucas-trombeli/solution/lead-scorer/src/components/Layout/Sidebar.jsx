import { Zap, LayoutDashboard, Table2, Users } from 'lucide-react';

const navItems = [
    { id: 'pipeline', label: 'Pipeline', icon: Table2 },
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'agents', label: 'Agents', icon: Users },
];

export function Sidebar({ currentView, onNavigate }) {
    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <Zap size={22} />
                <h1>LeadScore AI</h1>
            </div>
            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        className={`nav-item ${currentView === item.id ? 'active' : ''}`}
                        onClick={() => onNavigate(item.id)}
                    >
                        <item.icon />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>
            <div className="sidebar-footer">
                AI Master Challenge<br />
                G4 Educação — 2026
            </div>
        </aside>
    );
}
