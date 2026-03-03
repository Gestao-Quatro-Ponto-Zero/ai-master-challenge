import { DollarSign, TrendingUp, Target, Zap } from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    PieChart,
    Pie,
} from 'recharts';

function KpiCards({ kpis }) {
    if (!kpis) return null;

    const cards = [
        {
            label: 'Pipeline Value',
            value: `$${(kpis.totalPipelineValue / 1000).toFixed(0)}K`,
            icon: DollarSign,
            iconClass: 'green',
        },
        {
            label: 'Expected Value',
            value: `$${(kpis.totalExpectedValue / 1000).toFixed(0)}K`,
            icon: TrendingUp,
            iconClass: 'amber',
        },
        {
            label: 'Active Deals',
            value: kpis.activeCount.toLocaleString(),
            icon: Target,
            iconClass: 'blue',
        },
        {
            label: 'AVG Priority Score',
            value: kpis.avgScore,
            icon: Zap,
            iconClass: 'red',
        },
    ];

    return (
        <div className="kpi-grid">
            {cards.map((card) => (
                <div className="kpi-card" key={card.label}>
                    <div>
                        <div className="kpi-value">{card.value}</div>
                        <div className="kpi-label">{card.label}</div>
                    </div>
                    <div className={`kpi-icon ${card.iconClass}`}>
                        <card.icon />
                    </div>
                </div>
            ))}
        </div>
    );
}

function ScoreDistribution({ buckets }) {
    if (!buckets) return null;

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Score Distribution</span>
            </div>
            <div className="card-body">
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={buckets} layout="vertical">
                        <XAxis type="number" hide />
                        <YAxis
                            type="category"
                            dataKey="label"
                            width={120}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip
                            contentStyle={{
                                background: '#1e293b',
                                border: '1px solid rgba(148,163,184,0.15)',
                                borderRadius: 8,
                                color: '#f1f5f9',
                                fontSize: 13,
                            }}
                            formatter={(value) => [`${value} deals`, 'Count']}
                        />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={28}>
                            {buckets.map((entry, idx) => (
                                <Cell key={idx} fill={entry.color} fillOpacity={0.85} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

function TopDeals({ deals }) {
    if (!deals || !deals.length) return null;

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">🔥 Top 10 Priority Deals</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
                <table className="pipeline-table">
                    <thead>
                        <tr>
                            <th>Score</th>
                            <th>Account</th>
                            <th>Product</th>
                            <th>Agent</th>
                            <th>EV</th>
                        </tr>
                    </thead>
                    <tbody>
                        {deals.map((deal) => (
                            <tr key={deal.opportunity_id}>
                                <td>
                                    <span
                                        className={`score-badge ${deal.label.toLowerCase()}`}
                                    >
                                        {deal.priorityScore}
                                    </span>
                                </td>
                                <td className="truncate">
                                    {deal.account || '—'}
                                </td>
                                <td>{deal.product}</td>
                                <td className="truncate">{deal.sales_agent}</td>
                                <td className="text-green font-mono">
                                    ${deal.expectedValue.toLocaleString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function ProductBreakdown({ products }) {
    if (!products || !products.length) return null;

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Product Pipeline</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
                <table className="pipeline-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Deals</th>
                            <th>Avg Score</th>
                            <th>Total EV</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products.map((p) => (
                            <tr key={p.product}>
                                <td>{p.product}</td>
                                <td>{p.count}</td>
                                <td>{p.avgScore}</td>
                                <td className="text-green font-mono">
                                    ${p.totalEV.toLocaleString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function StageBreakdown({ stages }) {
    if (!stages) return null;

    const data = Object.entries(stages).map(([stage, info]) => ({
        stage,
        ...info,
    }));

    const colors = {
        Engaging: '#818cf8',
        Prospecting: '#94a3b8',
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Stage Breakdown</span>
            </div>
            <div className="card-body">
                <div style={{ display: 'flex', justifyContent: 'center', gap: 40 }}>
                    <ResponsiveContainer width={160} height={160}>
                        <PieChart>
                            <Pie
                                data={data}
                                dataKey="count"
                                nameKey="stage"
                                cx="50%"
                                cy="50%"
                                innerRadius={40}
                                outerRadius={70}
                            >
                                {data.map((entry) => (
                                    <Cell
                                        key={entry.stage}
                                        fill={colors[entry.stage] || '#64748b'}
                                        stroke="transparent"
                                    />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    background: '#1e293b',
                                    border: '1px solid rgba(148,163,184,0.15)',
                                    borderRadius: 8,
                                    color: '#f1f5f9',
                                    fontSize: 13,
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 12 }}>
                        {data.map((d) => (
                            <div key={d.stage}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                                    <div
                                        style={{
                                            width: 10,
                                            height: 10,
                                            borderRadius: 3,
                                            background: colors[d.stage] || '#64748b',
                                        }}
                                    />
                                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                                        {d.stage}
                                    </span>
                                </div>
                                <span className="text-muted" style={{ fontSize: '0.78rem', marginLeft: 18 }}>
                                    {d.count} deals · EV ${d.totalEV.toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export function Dashboard({ analytics }) {
    if (!analytics) return <div className="empty-state">No data available</div>;

    return (
        <>
            <KpiCards kpis={analytics.kpis} />
            <div className="dashboard-grid">
                <ScoreDistribution buckets={analytics.scoreBuckets} />
                <StageBreakdown stages={analytics.stageBreakdown} />
                <TopDeals deals={analytics.hottestDeals} />
                <ProductBreakdown products={analytics.productBreakdown} />
            </div>
        </>
    );
}
