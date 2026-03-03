// Analytics — Aggregations and derived metrics for dashboard views

export function computeAnalytics(scoredDeals, allScoredDeals, salesTeams) {
    const activeDeals = scoredDeals;

    // KPI Cards
    const totalPipelineValue = activeDeals.reduce(
        (sum, d) => sum + (d.productValue || 0),
        0
    );
    const totalExpectedValue = activeDeals.reduce(
        (sum, d) => sum + (d.expectedValue || 0),
        0
    );
    const activeCount = activeDeals.length;
    const avgScore = activeCount > 0
        ? Math.round(activeDeals.reduce((s, d) => s + d.priorityScore, 0) / activeCount)
        : 0;
    const avgWinProb = activeCount > 0
        ? Math.round(activeDeals.reduce((s, d) => s + d.winProbability, 0) / activeCount)
        : 0;

    // Score distribution
    const scoreBuckets = [
        { label: 'Hot (80-100)', min: 80, max: 100, color: '#10b981', count: 0 },
        { label: 'Warm (60-79)', min: 60, max: 79, color: '#f59e0b', count: 0 },
        { label: 'Cool (40-59)', min: 40, max: 59, color: '#f97316', count: 0 },
        { label: 'Cold (0-39)', min: 0, max: 39, color: '#ef4444', count: 0 },
    ];
    activeDeals.forEach((d) => {
        const bucket = scoreBuckets.find(
            (b) => d.priorityScore >= b.min && d.priorityScore <= b.max
        );
        if (bucket) bucket.count++;
    });

    // Top 10 hottest deals
    const hottestDeals = [...activeDeals]
        .sort((a, b) => b.priorityScore - a.priorityScore)
        .slice(0, 10);

    // Stage breakdown
    const stageBreakdown = {};
    activeDeals.forEach((d) => {
        if (!stageBreakdown[d.deal_stage]) {
            stageBreakdown[d.deal_stage] = { count: 0, totalValue: 0, totalEV: 0, avgScore: 0 };
        }
        const sb = stageBreakdown[d.deal_stage];
        sb.count++;
        sb.totalValue += d.productValue || 0;
        sb.totalEV += d.expectedValue || 0;
    });
    Object.values(stageBreakdown).forEach((sb) => {
        sb.avgScore = sb.count > 0 ? Math.round(sb.totalEV / sb.count) : 0;
    });

    // Agent Leaderboard
    const agentMap = new Map();
    // Initialize with all agents from sales_teams
    salesTeams.forEach((t) => {
        agentMap.set(t.sales_agent, {
            agent: t.sales_agent,
            manager: t.manager,
            region: t.regional_office,
            activeDeals: 0,
            totalPipelineValue: 0,
            totalExpectedValue: 0,
            avgPriorityScore: 0,
            wonDeals: 0,
            lostDeals: 0,
            totalClosed: 0,
            winRate: 0,
            totalRevenue: 0,
            scores: [],
        });
    });

    // Fill with active deal data
    activeDeals.forEach((d) => {
        const agent = agentMap.get(d.sales_agent);
        if (agent) {
            agent.activeDeals++;
            agent.totalPipelineValue += d.productValue || 0;
            agent.totalExpectedValue += d.expectedValue || 0;
            agent.scores.push(d.priorityScore);
        }
    });

    // Fill with historical data
    allScoredDeals.forEach((d) => {
        const agent = agentMap.get(d.sales_agent);
        if (agent) {
            if (d.deal_stage === 'Won') {
                agent.wonDeals++;
                agent.totalRevenue += d.close_value || 0;
            }
            if (d.deal_stage === 'Lost') agent.lostDeals++;
            if (d.deal_stage === 'Won' || d.deal_stage === 'Lost') {
                agent.totalClosed++;
            }
        }
    });

    // Compute averages
    agentMap.forEach((agent) => {
        agent.winRate =
            agent.totalClosed > 0
                ? Math.round((agent.wonDeals / agent.totalClosed) * 100)
                : 0;
        agent.avgPriorityScore =
            agent.scores.length > 0
                ? Math.round(
                    agent.scores.reduce((s, v) => s + v, 0) / agent.scores.length
                )
                : 0;
    });

    const agentLeaderboard = [...agentMap.values()].sort(
        (a, b) => b.winRate - a.winRate
    );

    // Product breakdown
    const productBreakdown = {};
    activeDeals.forEach((d) => {
        const key = d.product;
        if (!productBreakdown[key]) {
            productBreakdown[key] = {
                product: key,
                count: 0,
                totalValue: 0,
                totalEV: 0,
                avgScore: 0,
                scores: [],
            };
        }
        const pb = productBreakdown[key];
        pb.count++;
        pb.totalValue += d.productValue || 0;
        pb.totalEV += d.expectedValue || 0;
        pb.scores.push(d.priorityScore);
    });
    Object.values(productBreakdown).forEach((pb) => {
        pb.avgScore =
            pb.scores.length > 0
                ? Math.round(pb.scores.reduce((s, v) => s + v, 0) / pb.scores.length)
                : 0;
    });

    return {
        kpis: {
            totalPipelineValue,
            totalExpectedValue,
            activeCount,
            avgScore,
            avgWinProb,
        },
        scoreBuckets,
        hottestDeals,
        stageBreakdown,
        agentLeaderboard,
        productBreakdown: Object.values(productBreakdown).sort(
            (a, b) => b.totalEV - a.totalEV
        ),
    };
}
