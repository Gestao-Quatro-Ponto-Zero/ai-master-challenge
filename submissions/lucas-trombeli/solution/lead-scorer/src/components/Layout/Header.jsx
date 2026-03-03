import { Search, RotateCcw } from 'lucide-react';

const viewTitles = {
    pipeline: { title: 'Pipeline', subtitle: 'All active deals sorted by priority' },
    dashboard: { title: 'Overview', subtitle: 'KPIs and pipeline health at a glance' },
    agents: { title: 'Agent Performance', subtitle: 'Win rates and pipeline by sales agent' },
};

export function Header({
    currentView,
    filters,
    filterOptions,
    onFilterChange,
    onResetFilters,
    totalDeals,
    filteredCount,
}) {
    const { title, subtitle } = viewTitles[currentView] || {};
    const hasActiveFilter = Object.entries(filters).some(
        ([k, v]) => k !== 'search' && v !== 'all'
    ) || filters.search;

    return (
        <div className="page-header">
            <div>
                <h2 className="page-title">{title}</h2>
                <p className="page-subtitle">
                    {subtitle}
                    {filteredCount !== totalDeals && (
                        <span className="text-accent">
                            {' '}· Showing {filteredCount} of {totalDeals} deals
                        </span>
                    )}
                </p>
            </div>
            <div className="filter-bar">
                <div style={{ position: 'relative' }}>
                    <Search
                        size={14}
                        style={{
                            position: 'absolute',
                            left: 10,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            color: 'var(--text-muted)',
                        }}
                    />
                    <input
                        className="filter-input"
                        type="text"
                        placeholder="Search deals..."
                        value={filters.search}
                        onChange={(e) => onFilterChange('search', e.target.value)}
                        style={{ paddingLeft: 30 }}
                    />
                </div>
                <select
                    className="filter-select"
                    value={filters.region}
                    onChange={(e) => onFilterChange('region', e.target.value)}
                >
                    <option value="all">All Regions</option>
                    {filterOptions.regions.map((r) => (
                        <option key={r} value={r}>{r}</option>
                    ))}
                </select>
                <select
                    className="filter-select"
                    value={filters.manager}
                    onChange={(e) => onFilterChange('manager', e.target.value)}
                >
                    <option value="all">All Managers</option>
                    {filterOptions.managers.map((m) => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>
                <select
                    className="filter-select"
                    value={filters.agent}
                    onChange={(e) => onFilterChange('agent', e.target.value)}
                >
                    <option value="all">All Agents</option>
                    {filterOptions.agents.map((a) => (
                        <option key={a} value={a}>{a}</option>
                    ))}
                </select>
                <select
                    className="filter-select"
                    value={filters.stage}
                    onChange={(e) => onFilterChange('stage', e.target.value)}
                >
                    <option value="all">All Stages</option>
                    {filterOptions.stages.map((s) => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
                <select
                    className="filter-select"
                    value={filters.scoreRange}
                    onChange={(e) => onFilterChange('scoreRange', e.target.value)}
                >
                    <option value="all">All Scores</option>
                    <option value="hot">🔥 Hot (80-100)</option>
                    <option value="warm">🟡 Warm (60-79)</option>
                    <option value="cool">🟠 Cool (40-59)</option>
                    <option value="cold">❄️ Cold (0-39)</option>
                </select>
                {hasActiveFilter && (
                    <button className="filter-reset" onClick={onResetFilters}>
                        <RotateCcw size={12} /> Reset
                    </button>
                )}
            </div>
        </div>
    );
}
