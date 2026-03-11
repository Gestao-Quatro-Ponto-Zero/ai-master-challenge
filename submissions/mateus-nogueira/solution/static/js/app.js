/**
 * Lead Scorer — Alpine.js application logic.
 * Handles state management, API calls, and utility functions.
 */

function app() {
    return {
        // Current view
        view: 'pipeline',

        // Filter options (loaded from API)
        filterOptions: { agents: [], managers: [], regions: [], stages: [] },

        // Pipeline state
        filters: { search: '', stage: '', agent: '', manager: '', region: '', alert_type: '', sort: 'score', order: 'desc' },
        pipelineData: { deals: [], total: 0 },

        // Deal detail
        showDealPanel: false,
        selectedDeal: null,

        // Monday state
        mondayFilters: { manager: '', region: '', agent: '' },
        mondayData: { fechar_agora: [], nutrir: [], repensar: [], summary: {} },

        // Dashboard state
        dashboardFilters: { region: '', manager: '' },
        dashboardData: {},
        dashboardReady: false,
        scoreDistChart: null,
        productWrChart: null,

        // Agents state
        agentsFilters: { manager: '', region: '' },
        agentsData: [],

        // Teams grid state
        teamsGrid: { regions: [], rows: [], totals: {} },

        async init() {
            // Load filter options
            const res = await fetch('/api/filters');
            this.filterOptions = await res.json();

            // Load initial pipeline
            await this.loadPipeline();

            // Watch for view changes to load data
            this.$watch('view', async (newView) => {
                if (newView === 'dashboard') await this.loadDashboard();
                if (newView === 'agents') { await this.loadAgents(); await this.loadTeamsGrid(); }
                if (newView === 'monday') await this.loadMonday();
            });
        },

        async loadPipeline() {
            const params = new URLSearchParams();
            if (this.filters.stage) params.set('stage', this.filters.stage);
            if (this.filters.agent) params.set('agent', this.filters.agent);
            if (this.filters.manager) params.set('manager', this.filters.manager);
            if (this.filters.region) params.set('region', this.filters.region);
            if (this.filters.search) params.set('search', this.filters.search);
            if (this.filters.alert_type) params.set('alert_type', this.filters.alert_type);
            params.set('sort', this.filters.sort);
            params.set('order', this.filters.order);

            const res = await fetch('/api/pipeline?' + params.toString());
            this.pipelineData = await res.json();
        },

        sortPipeline(field) {
            if (this.filters.sort === field) {
                this.filters.order = this.filters.order === 'desc' ? 'asc' : 'desc';
            } else {
                this.filters.sort = field;
                this.filters.order = 'desc';
            }
            this.loadPipeline();
        },

        async openDeal(opportunityId) {
            const res = await fetch('/api/deal/' + opportunityId);
            if (!res.ok) {
                this.selectedDeal = null;
                this.showDealPanel = false;
                return;
            }
            this.selectedDeal = await res.json();
            this.showDealPanel = true;
        },

        async loadMonday() {
            const params = new URLSearchParams();
            if (this.mondayFilters.manager) params.set('manager', this.mondayFilters.manager);
            if (this.mondayFilters.region) params.set('region', this.mondayFilters.region);
            if (this.mondayFilters.agent) params.set('agent', this.mondayFilters.agent);

            const res = await fetch('/api/monday?' + params.toString());
            this.mondayData = await res.json();
        },

        async loadDashboard() {
            this.dashboardReady = false;

            // Destroy old charts before fetching new data
            if (this.scoreDistChart) { this.scoreDistChart.destroy(); this.scoreDistChart = null; }
            if (this.productWrChart) { this.productWrChart.destroy(); this.productWrChart = null; }

            const params = new URLSearchParams();
            if (this.dashboardFilters.region) params.set('region', this.dashboardFilters.region);
            if (this.dashboardFilters.manager) params.set('manager', this.dashboardFilters.manager);
            const res = await fetch('/api/dashboard?' + params.toString());
            this.dashboardData = await res.json();

            // Data is ready — reveal content, then render charts
            this.dashboardReady = true;

            // Use requestAnimationFrame chain to ensure DOM is painted before Chart.js
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    this.renderScoreDistChart();
                    this.renderProductWrChart();
                });
            });
        },

        renderScoreDistChart() {
            const canvas = document.getElementById('scoreDistChart');
            if (!canvas || canvas.clientWidth === 0) return;

            const dist = this.dashboardData.score_distribution || {};
            this.scoreDistChart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(dist),
                    datasets: [{
                        data: Object.values(dist),
                        backgroundColor: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#059669'],
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        },

        renderProductWrChart() {
            const canvas = document.getElementById('productWrChart');
            if (!canvas || canvas.clientWidth === 0) return;

            const products = this.dashboardData.products_winrate || [];
            this.productWrChart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: products.map(p => p.product),
                    datasets: [{
                        label: 'Taxa de Conversão %',
                        data: products.map(p => p.win_rate),
                        backgroundColor: '#3b82f6',
                        borderRadius: 6,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, max: 100, grid: { color: '#f1f5f9' } },
                        y: { grid: { display: false } }
                    }
                }
            });
        },

        async loadAgents() {
            const params = new URLSearchParams();
            if (this.agentsFilters.manager) params.set('manager', this.agentsFilters.manager);
            if (this.agentsFilters.region) params.set('region', this.agentsFilters.region);

            const res = await fetch('/api/agents?' + params.toString());
            const data = await res.json();
            this.agentsData = data.agents || [];
        },

        // ── Teams grid helpers ──

        heatmapClasses(score) {
            if (score >= 65) return 'bg-emerald-500 text-white border-emerald-600';
            if (score >= 55) return 'bg-emerald-400 text-white border-emerald-500';
            if (score >= 45) return 'bg-amber-400 text-amber-950 border-amber-500';
            if (score >= 35) return 'bg-orange-400 text-orange-950 border-orange-500';
            return 'bg-red-400 text-white border-red-500';
        },

        gridMaxDeals() {
            let max = 1;
            for (const row of this.teamsGrid.rows || []) {
                for (const reg of this.teamsGrid.regions || []) {
                    const c = row.cells[reg];
                    if (c && c.deals_active > max) max = c.deals_active;
                }
            }
            return max;
        },

        gridMaxPipeline() {
            let max = 1;
            for (const row of this.teamsGrid.rows || []) {
                for (const reg of this.teamsGrid.regions || []) {
                    const c = row.cells[reg];
                    if (c && c.pipeline_value > max) max = c.pipeline_value;
                }
            }
            return max;
        },

        gridMaxPipelineTotal() {
            let max = 1;
            for (const row of this.teamsGrid.rows || []) {
                const c = row.cells['Total'];
                if (c && c.pipeline_value > max) max = c.pipeline_value;
            }
            return max;
        },

        async loadTeamsGrid() {
            const res = await fetch('/api/teams-grid');
            this.teamsGrid = await res.json();
        },

        // ── Utility functions ──

        formatCurrency(value) {
            if (value == null) return '$0';
            return '$' + Math.round(value).toLocaleString('en-US');
        },

        scoreLabelText(score) {
            if (score >= 75) return 'Quente';
            if (score >= 55) return 'Morno';
            if (score >= 35) return 'Frio';
            return 'Congelado';
        },

        scoreLabelIcon(label) {
            const map = {
                'Quente': '\uD83D\uDD25',
                'Morno': '\u2600\uFE0F',
                'Frio': '\u2744\uFE0F',
                'Congelado': '\uD83E\uDDCA',
            };
            return map[label] || '';
        },

        scoreClasses(score) {
            if (score >= 75) return 'bg-green-100 text-green-800';
            if (score >= 55) return 'bg-yellow-100 text-yellow-800';
            if (score >= 35) return 'bg-orange-100 text-orange-800';
            return 'bg-red-100 text-red-800';
        },

        scoreBgClass(score) {
            if (score >= 75) return 'bg-green-50';
            if (score >= 55) return 'bg-yellow-50';
            if (score >= 35) return 'bg-orange-50';
            return 'bg-red-50';
        },

        scoreTextClass(score) {
            if (score >= 75) return 'text-green-700';
            if (score >= 55) return 'text-yellow-700';
            if (score >= 35) return 'text-orange-700';
            return 'text-red-700';
        },

        scoreHex(score) {
            if (score >= 75) return '#059669';
            if (score >= 55) return '#d97706';
            if (score >= 35) return '#ea580c';
            return '#dc2626';
        },

        alertClasses(color) {
            const map = {
                green: 'bg-green-50 text-green-700',
                orange: 'bg-orange-50 text-orange-700',
                red: 'bg-red-50 text-red-700',
                blue: 'bg-blue-50 text-blue-700',
                gray: 'bg-slate-100 text-slate-600',
            };
            return map[color] || 'bg-slate-100 text-slate-600';
        },

        alertBannerClasses(color) {
            const map = {
                green: 'bg-green-50 border-green-200 text-green-800',
                orange: 'bg-orange-50 border-orange-200 text-orange-800',
                red: 'bg-red-50 border-red-200 text-red-800',
                blue: 'bg-blue-50 border-blue-200 text-blue-800',
                gray: 'bg-slate-50 border-slate-200 text-slate-700',
            };
            return map[color] || 'bg-slate-50 border-slate-200 text-slate-700';
        },

        alertIcon(icon) {
            const map = {
                flame: '\uD83D\uDD25',
                thermometer: '\u2744\uFE0F',
                'alert-triangle': '\u26A0\uFE0F',
                pause: '\uD83D\uDCA4',
                zap: '\u26A1',
            };
            return map[icon] || '';
        },

        actionIcon(icon) {
            const map = {
                flame: '\uD83D\uDD25',
                zap: '\u26A1',
                thermometer: '\u2744\uFE0F',
                pause: '\uD83D\uDCA4',
                'alert-triangle': '\u26A0\uFE0F',
                'arrow-up': '\uD83D\uDE80',
                message: '\uD83D\uDCAC',
                calendar: '\uD83D\uDCC5',
                search: '\uD83D\uDD0D',
                'x-circle': '\u274C',
            };
            return map[icon] || '\u25CF';
        },

        actionClasses(color) {
            const map = {
                green: 'bg-green-50 text-green-700 border-green-200',
                yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
                orange: 'bg-orange-50 text-orange-700 border-orange-200',
                red: 'bg-red-50 text-red-700 border-red-200',
                blue: 'bg-blue-50 text-blue-700 border-blue-200',
                gray: 'bg-slate-50 text-slate-600 border-slate-200',
            };
            return map[color] || 'bg-slate-50 text-slate-600 border-slate-200';
        },

        compBarColor(score, max) {
            const pct = score / max;
            if (pct >= 0.7) return 'bg-green-500';
            if (pct >= 0.4) return 'bg-yellow-500';
            return 'bg-red-400';
        },

        // ── Translation helpers ──

        translateRegion(region) {
            const map = {
                'West': 'Oeste',
                'East': 'Leste',
                'Central': 'Centro',
            };
            return map[region] || region || '—';
        },

        translateStage(stage) {
            const map = {
                'Prospecting': 'Prospectar',
                'Engaging': 'Engajar',
                'Nutrir': 'Nutrir',
                'Won': 'Ganho',
                'Lost': 'Perdido',
            };
            return map[stage] || stage || '—';
        },

        translateAlertType(type) {
            const map = {
                'hot': 'Oportunidade Quente',
                'cooling': 'Esfriando',
                'at_risk': 'Em Risco',
                'stale': 'Parado',
                'quick_win': 'Vitoria Rapida',
            };
            return map[type] || type || '—';
        },

        // ── Kanban drag & drop ──

        dragDeal: null,
        dragSourceBucket: null,

        onDragStart(event, deal, sourceBucket) {
            this.dragDeal = deal;
            this.dragSourceBucket = sourceBucket;
            event.dataTransfer.effectAllowed = 'move';
            event.target.classList.add('opacity-50');
        },

        onDragEnd(event) {
            event.target.classList.remove('opacity-50');
            this.dragDeal = null;
            this.dragSourceBucket = null;
        },

        onDragOver(event) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
        },

        onDragEnter(event) {
            event.preventDefault();
            event.currentTarget.classList.add('ring-2', 'ring-blue-400', 'ring-inset');
        },

        onDragLeave(event) {
            event.currentTarget.classList.remove('ring-2', 'ring-blue-400', 'ring-inset');
        },

        onDrop(event, targetBucket) {
            event.preventDefault();
            event.currentTarget.classList.remove('ring-2', 'ring-blue-400', 'ring-inset');
            if (!this.dragDeal || this.dragSourceBucket === targetBucket) return;

            // Remove from source
            const srcList = this.mondayData[this.dragSourceBucket];
            const idx = srcList.findIndex(d => d.opportunity_id === this.dragDeal.opportunity_id);
            if (idx !== -1) srcList.splice(idx, 1);

            // Add to target
            this.mondayData[targetBucket].push(this.dragDeal);

            // Resort target by score desc
            this.mondayData[targetBucket].sort((a, b) => b.score - a.score);

            // Update summary counts & values
            this.mondayData.summary.total_fechar = this.mondayData.fechar_agora.length;
            this.mondayData.summary.total_nutrir = this.mondayData.nutrir.length;
            this.mondayData.summary.total_repensar = this.mondayData.repensar.length;
            this.mondayData.summary.valor_fechar = this.mondayData.fechar_agora.reduce((s, d) => s + (d.estimated_value || 0), 0);
            this.mondayData.summary.valor_nutrir = this.mondayData.nutrir.reduce((s, d) => s + (d.estimated_value || 0), 0);
            this.mondayData.summary.valor_repensar = this.mondayData.repensar.reduce((s, d) => s + (d.estimated_value || 0), 0);

            this.dragDeal = null;
            this.dragSourceBucket = null;
        },
    };
}
