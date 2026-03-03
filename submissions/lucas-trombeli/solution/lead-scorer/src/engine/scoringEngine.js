// Scoring Engine — Two-layer scoring: Win Probability + Priority (Expected Value)

// ============================================================
// PIPELINE VELOCITY CURVE (Time Decay)
// ============================================================
// Based on data analysis:
// - Lost deals die fast: median 14 days
// - Won deals take longer: median 57 days
// - The "death zone" is 0-14 days
// - Sweet spot is 14-57 days
// - Deals stale after ~100 days

function pipelineVelocityScore(daysInPipeline) {
    if (daysInPipeline === null || daysInPipeline === undefined) return 50; // No data = neutral

    const d = daysInPipeline;

    if (d <= 0) return 10; // Just entered — too early to tell
    if (d <= 14) return 10 + (d / 14) * 50; // Ramp: 10 → 60 (surviving death zone)
    if (d <= 30) return 60 + ((d - 14) / 16) * 40; // Ramp to peak: 60 → 100
    if (d <= 57) return 100; // Peak zone — optimal closing window
    if (d <= 80) return 100 - ((d - 57) / 23) * 25; // Cooling: 100 → 75
    if (d <= 100) return 75 - ((d - 80) / 20) * 35; // Staling: 75 → 40
    if (d <= 120) return 40 - ((d - 100) / 20) * 25; // Zombie: 40 → 15
    return Math.max(5, 15 - (d - 120) * 0.5); // Deep zombie: slow bleed to 5
}

// ============================================================
// FACTOR SCORING FUNCTIONS
// ============================================================

function scoreAgentWinRate(agentWinRate, globalWinRate) {
    // Normalize agent win rate relative to global
    // Agent at global average = 50 points
    // Best agents (~70%) = 100 points
    // Worst agents (~55%) = 20 points
    const diff = agentWinRate - globalWinRate;
    const normalized = 50 + diff * 500; // ±10% = ±50 points
    return {
        score: Math.max(0, Math.min(100, normalized)),
        label: 'Agent Win Rate',
        detail: `${(agentWinRate * 100).toFixed(1)}% historical win rate`,
        value: agentWinRate,
    };
}

function scoreDealStage(stage) {
    const stageScores = {
        Engaging: 80,
        Prospecting: 35,
    };
    return {
        score: stageScores[stage] ?? 50,
        label: 'Deal Stage',
        detail:
            stage === 'Engaging'
                ? 'Actively engaged — closer to close'
                : 'Early prospecting — still building relationship',
        value: stage,
    };
}

function scorePipelineVelocity(daysInPipeline) {
    const score = pipelineVelocityScore(daysInPipeline);
    let detail;
    if (daysInPipeline === null) {
        detail = 'No engagement date available';
    } else if (daysInPipeline <= 14) {
        detail = `${daysInPipeline}d — early stage, surviving death zone`;
    } else if (daysInPipeline <= 57) {
        detail = `${daysInPipeline}d — peak closing window`;
    } else if (daysInPipeline <= 100) {
        detail = `${daysInPipeline}d — cooling, needs push`;
    } else {
        detail = `${daysInPipeline}d — stale deal, risk of zombie`;
    }
    return {
        score,
        label: 'Pipeline Velocity',
        detail,
        value: daysInPipeline,
    };
}

function scoreProductFactor(productWinRate, productValue, maxProductValue) {
    // Blend of product win rate (60%) and value tier (40%)
    const winRateScore = productWinRate * 100; // 0-100 range
    const valueTier =
        maxProductValue > 0 ? (productValue / maxProductValue) * 100 : 50;
    const score = winRateScore * 0.6 + valueTier * 0.4;
    return {
        score: Math.max(0, Math.min(100, score)),
        label: 'Product Factor',
        detail: `${productValue > 0 ? '$' + productValue.toLocaleString() : 'Unknown'
            } — ${(productWinRate * 100).toFixed(1)}% product win rate`,
        value: productValue,
    };
}

function scoreAccountSector(sectorWinRate, sector) {
    if (!sector || sectorWinRate === undefined) {
        return { score: 0, label: 'Account Sector', detail: 'No account linked', value: null };
    }
    const score = sectorWinRate * 100;
    return {
        score: Math.max(0, Math.min(100, score)),
        label: 'Account Sector',
        detail: `${sector} sector — ${(sectorWinRate * 100).toFixed(1)}% win rate`,
        value: sector,
    };
}

function scoreAccountSize(revenue, employees, maxRevenue, maxEmployees) {
    if (!revenue && !employees) {
        return { score: 0, label: 'Account Size', detail: 'No account linked', value: null };
    }
    const revScore = revenue && maxRevenue > 0 ? (revenue / maxRevenue) * 100 : 50;
    const empScore =
        employees && maxEmployees > 0 ? (employees / maxEmployees) * 100 : 50;
    const score = revScore * 0.5 + empScore * 0.5;
    return {
        score: Math.max(0, Math.min(100, score)),
        label: 'Account Size',
        detail: `${employees ? employees.toLocaleString() + ' employees' : 'Unknown size'}${revenue ? ' · $' + revenue.toFixed(1) + 'M revenue' : ''
            }`,
        value: { revenue, employees },
    };
}

// ============================================================
// MAIN SCORING FUNCTION
// ============================================================

export function scoreDeal(deal, stats) {
    const {
        agentWinRates,
        productWinRates,
        sectorWinRates,
        globalWinRate,
        maxProductValue,
        maxRevenue,
        maxEmployees,
    } = stats;

    // Get individual factor scores
    const agentWR = agentWinRates.get(deal.sales_agent) ?? globalWinRate;
    const productWR = productWinRates.get(deal.product) ?? globalWinRate;
    const sectorWR = deal.sector ? (sectorWinRates.get(deal.sector) ?? globalWinRate) : null;

    const factors = {
        agent: scoreAgentWinRate(agentWR, globalWinRate),
        stage: scoreDealStage(deal.deal_stage),
        velocity: scorePipelineVelocity(deal.daysInPipeline),
        product: scoreProductFactor(productWR, deal.productValue, maxProductValue),
        sector: scoreAccountSector(sectorWR, deal.sector),
        accountSize: scoreAccountSize(
            deal.revenue,
            deal.employees,
            maxRevenue,
            maxEmployees
        ),
    };

    // Dynamic weights based on data availability (Cold Start handling)
    let weights;
    if (deal.hasAccount) {
        weights = {
            agent: 0.25,
            stage: 0.20,
            velocity: 0.20,
            product: 0.15,
            sector: 0.10,
            accountSize: 0.10,
        };
    } else {
        // No account → redistribute sector/size weight to agent, product, stage
        weights = {
            agent: 0.35,
            stage: 0.25,
            velocity: 0.20,
            product: 0.20,
            sector: 0,
            accountSize: 0,
        };
    }

    // Calculate weighted win probability
    let winProbability = 0;
    const breakdown = [];

    for (const [key, weight] of Object.entries(weights)) {
        const factor = factors[key];
        const contribution = factor.score * weight;
        winProbability += contribution;
        breakdown.push({
            factor: factor.label,
            score: Math.round(factor.score),
            weight: Math.round(weight * 100),
            contribution: Math.round(contribution),
            detail: factor.detail,
            rawValue: factor.value,
        });
    }

    winProbability = Math.max(0, Math.min(100, Math.round(winProbability)));

    // Layer 2: Priority Score (Expected Value)
    // Use LOG SCALE for value normalization to prevent GTK 500 ($26K)
    // from crushing all other products ($55-$5K range).
    // Log scale: $55→0.45, $550→0.65, $1K→0.72, $5K→0.87, $27K→1.0
    const logValue = deal.productValue > 0 ? Math.log(deal.productValue) : 0;
    const logMax = maxProductValue > 0 ? Math.log(maxProductValue) : 1;
    const valueNormalized = logMax > 0 ? logValue / logMax : 0;

    // Priority Score: Blend of Win Probability with value-adjusted boost
    // - Base: 55% win probability (the core signal)
    // - Value boost: 45% of (probability × log-value weight)
    // This ensures high-value deals rise but low-value deals aren't zeroed out
    const priorityScore = Math.round(
        winProbability * 0.55 + winProbability * valueNormalized * 0.45
    );

    // Expected monetary value
    const expectedValue = Math.round(
        (winProbability / 100) * deal.productValue
    );

    // Score label
    let label, color, action;
    if (priorityScore >= 80) {
        label = 'Hot';
        color = '#10b981';
        action = 'Prioritize now — high EV deal';
    } else if (priorityScore >= 60) {
        label = 'Warm';
        color = '#f59e0b';
        action = 'Nurture — good potential, needs attention';
    } else if (priorityScore >= 40) {
        label = 'Cool';
        color = '#f97316';
        action = 'Monitor — moderate EV, don\'t over-invest';
    } else {
        label = 'Cold';
        color = '#ef4444';
        action = 'Deprioritize — low EV, review if worth keeping';
    }

    return {
        ...deal,
        winProbability,
        priorityScore,
        expectedValue,
        label,
        color,
        action,
        breakdown,
        hasAccount: deal.hasAccount,
    };
}

// Score all active deals in the pipeline
export function scoreActivePipeline(pipeline, stats) {
    const activeDeals = pipeline.filter(
        (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
    );

    return activeDeals
        .map((deal) => scoreDeal(deal, stats))
        .sort((a, b) => b.priorityScore - a.priorityScore);
}

// Score ALL deals (including Won/Lost for historical context)
export function scoreAllDeals(pipeline, stats) {
    return pipeline
        .map((deal) => scoreDeal(deal, stats))
        .sort((a, b) => b.priorityScore - a.priorityScore);
}
