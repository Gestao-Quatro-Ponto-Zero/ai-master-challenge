import { Trophy, TrendingUp, Target } from 'lucide-react';

export function AgentLeaderboard({ agents }) {
    if (!agents || !agents.length) {
        return <div className="empty-state">No agent data available</div>;
    }

    return (
        <div className="agent-grid">
            {agents.map((agent, idx) => {
                const winColor =
                    agent.winRate >= 67
                        ? 'var(--hot)'
                        : agent.winRate >= 62
                            ? 'var(--warm)'
                            : 'var(--cold)';

                return (
                    <div className="agent-card" key={agent.agent}>
                        <div className="agent-card-header">
                            <div>
                                <div className="agent-name">
                                    {idx < 3 && (
                                        <Trophy
                                            size={14}
                                            style={{
                                                color:
                                                    idx === 0
                                                        ? '#fbbf24'
                                                        : idx === 1
                                                            ? '#94a3b8'
                                                            : '#cd7f32',
                                                marginRight: 6,
                                                verticalAlign: 'middle',
                                            }}
                                        />
                                    )}
                                    {agent.agent}
                                </div>
                                <div className="agent-meta">
                                    {agent.manager} · {agent.region}
                                </div>
                            </div>
                            <span
                                style={{
                                    fontSize: '1.5rem',
                                    fontWeight: 800,
                                    color: winColor,
                                }}
                            >
                                {agent.winRate}%
                            </span>
                        </div>
                        <div className="agent-stats">
                            <div className="agent-stat">
                                <div className="agent-stat-value text-accent">
                                    {agent.activeDeals}
                                </div>
                                <div className="agent-stat-label">Active</div>
                            </div>
                            <div className="agent-stat">
                                <div className="agent-stat-value text-green">
                                    {agent.wonDeals}
                                </div>
                                <div className="agent-stat-label">Won</div>
                            </div>
                            <div className="agent-stat">
                                <div className="agent-stat-value">
                                    ${(agent.totalExpectedValue / 1000).toFixed(1)}K
                                </div>
                                <div className="agent-stat-label">Pipeline EV</div>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
