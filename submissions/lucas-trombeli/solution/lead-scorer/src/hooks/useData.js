// useData hook — Central data management for the app
import { useState, useEffect, useMemo, useCallback } from 'react';
import { loadAllData, computeHistoricalStats } from '../engine/dataLoader';
import { scoreActivePipeline, scoreAllDeals } from '../engine/scoringEngine';
import { computeAnalytics } from '../engine/analytics';

export function useData() {
    const [rawData, setRawData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filters
    const [filters, setFilters] = useState({
        agent: 'all',
        manager: 'all',
        region: 'all',
        stage: 'all',
        scoreRange: 'all', // 'hot', 'warm', 'cool', 'cold', 'all'
        search: '',
    });

    // Load data on mount
    useEffect(() => {
        loadAllData()
            .then((data) => {
                setRawData(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error('Failed to load data:', err);
                setError(err.message);
                setLoading(false);
            });
    }, []);

    // Compute historical stats and scores
    const { scoredDeals, allScoredDeals, stats } = useMemo(() => {
        if (!rawData) return { scoredDeals: [], allScoredDeals: [], stats: null };

        const stats = computeHistoricalStats(rawData.pipeline);
        const scoredDeals = scoreActivePipeline(rawData.pipeline, stats);
        const allScoredDeals = scoreAllDeals(rawData.pipeline, stats);

        return { scoredDeals, allScoredDeals, stats };
    }, [rawData]);

    // Apply filters
    const filteredDeals = useMemo(() => {
        if (!scoredDeals.length) return [];

        return scoredDeals.filter((deal) => {
            if (filters.agent !== 'all' && deal.sales_agent !== filters.agent)
                return false;
            if (filters.manager !== 'all' && deal.manager !== filters.manager)
                return false;
            if (filters.region !== 'all' && deal.regionalOffice !== filters.region)
                return false;
            if (filters.stage !== 'all' && deal.deal_stage !== filters.stage)
                return false;

            if (filters.scoreRange !== 'all') {
                const ranges = {
                    hot: [80, 100],
                    warm: [60, 79],
                    cool: [40, 59],
                    cold: [0, 39],
                };
                const [min, max] = ranges[filters.scoreRange] || [0, 100];
                if (deal.priorityScore < min || deal.priorityScore > max) return false;
            }

            if (filters.search) {
                const search = filters.search.toLowerCase();
                const searchable = [
                    deal.account,
                    deal.sales_agent,
                    deal.product,
                    deal.opportunity_id,
                    deal.sector,
                ]
                    .filter(Boolean)
                    .join(' ')
                    .toLowerCase();
                if (!searchable.includes(search)) return false;
            }

            return true;
        });
    }, [scoredDeals, filters]);

    // Filter options
    const filterOptions = useMemo(() => {
        if (!rawData) return { agents: [], managers: [], regions: [], stages: [] };

        const agents = [
            ...new Set(rawData.salesTeams.map((t) => t.sales_agent)),
        ].sort();
        const managers = [
            ...new Set(rawData.salesTeams.map((t) => t.manager)),
        ].sort();
        const regions = [
            ...new Set(rawData.salesTeams.map((t) => t.regional_office)),
        ].sort();
        const stages = ['Engaging', 'Prospecting'];

        return { agents, managers, regions, stages };
    }, [rawData]);

    // Analytics computed from filtered deals
    const analytics = useMemo(() => {
        if (!rawData || !scoredDeals.length) return null;
        return computeAnalytics(filteredDeals, allScoredDeals, rawData.salesTeams);
    }, [filteredDeals, allScoredDeals, rawData]);

    const updateFilter = useCallback((key, value) => {
        setFilters((prev) => ({ ...prev, [key]: value }));
    }, []);

    const resetFilters = useCallback(() => {
        setFilters({
            agent: 'all',
            manager: 'all',
            region: 'all',
            stage: 'all',
            scoreRange: 'all',
            search: '',
        });
    }, []);

    return {
        loading,
        error,
        rawData,
        scoredDeals,
        filteredDeals,
        allScoredDeals,
        stats,
        analytics,
        filters,
        filterOptions,
        updateFilter,
        resetFilters,
    };
}
