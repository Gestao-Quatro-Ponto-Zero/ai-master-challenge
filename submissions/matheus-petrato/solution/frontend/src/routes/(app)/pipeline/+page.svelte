<script lang="ts">
	import { Flame, AlertTriangle, Timer, TrendingUp, ArrowUpRight, X, ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { page } from '$app/state';
	import { api } from '$lib/services/api';

	const filters = [
		{ label: 'Todos', key: 'all' },
		{ label: 'Quentes', key: 'hot' },
		{ label: 'Em risco', key: 'risk' },
		{ label: 'Estagnados', key: 'stalled' }
	];

	const PAGE_SIZE = 20;

	let activeFilter = $state('all');
	let deals = $state<any[]>([]);
	let total = $state(0);
	let currentPage = $state(1);
	let loading = $state(false);
	let modalDealId = $state<string | null>(null);
	let modalDeal = $state<any>(null);
	let modalLoading = $state(false);

	// Open modal from URL ?deal=id
	$effect(() => {
		const dealId = page.url.searchParams.get('deal');
		if (dealId) {
			modalDealId = dealId;
			openDealModal(dealId);
			// Clear from URL without reload
			window.history.replaceState({}, '', '/pipeline');
		}
	});

	const formatValue = (value: any) => (typeof value === 'number' ? value.toLocaleString('pt-BR') : value ?? '-');
	const formatTrend = (value: any) => {
		if (typeof value === 'number') {
			const sign = value >= 0 ? '+' : '';
			return `${sign}${(value * 100).toFixed(1)}%`;
		}
		return value ?? '-';
	};

	const mapDeals = (items: any[] = []) =>
		items.map((deal) => ({
			id: deal.id ?? deal.ID,
			name: deal.name ?? deal.Name,
			score: deal.score ?? deal.Score ?? 0,
			stage: deal.stage ?? deal.Stage ?? '-',
			days: deal.days ?? deal.Days ?? '-',
			value: formatValue(deal.value ?? deal.Value),
			trend: formatTrend(deal.trend ?? deal.Trend ?? 0),
			status: deal.status ?? deal.Status ?? 'stalled',
			action: deal.action ?? deal.Action ?? ''
		}));

	const loadDeals = async () => {
		loading = true;
		try {
			const status = activeFilter === 'all' ? undefined : activeFilter;
			const data = await api.deals.list({
				status,
				limit: PAGE_SIZE,
				offset: (currentPage - 1) * PAGE_SIZE
			});
			const items = Array.isArray(data) ? data : data?.items ?? [];
			deals = mapDeals(items);
			total = typeof data?.total === 'number' ? data.total : items.length;
		} catch (err) {
			console.warn('Falha ao carregar deals:', err);
			deals = [];
			total = 0;
		} finally {
			loading = false;
		}
	};

	const openDealModal = async (id: string) => {
		modalDealId = id;
		modalLoading = true;
		modalDeal = null;
		try {
			modalDeal = await api.deals.get(id);
		} catch (err) {
			console.warn('Falha ao carregar deal:', err);
			modalDeal = null;
		} finally {
			modalLoading = false;
		}
	};

	const closeModal = () => {
		modalDealId = null;
		modalDeal = null;
	};

	$effect(() => {
		loadDeals();
	});

	const statusIcon = (status: string) => {
		if (status === 'hot') return Flame;
		if (status === 'risk') return AlertTriangle;
		return Timer;
	};

	const statusColor = (status: string) => {
		if (status === 'hot') return 'text-emerald-600 bg-emerald-50 border-emerald-200';
		if (status === 'risk') return 'text-amber-600 bg-amber-50 border-amber-200';
		return 'text-slate-500 bg-slate-50 border-slate-200';
	};

	const sentimentColor = (sentiment: string) =>
		sentiment === 'positive' ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : 'text-amber-600 bg-amber-50 border-amber-200';
	const sentimentIcon = (sentiment: string) => (sentiment === 'positive' ? TrendingUp : AlertTriangle);

	const totalPages = $derived(Math.max(1, Math.ceil(total / PAGE_SIZE)));
	const hasNext = $derived(currentPage < totalPages);
	const hasPrev = $derived(currentPage > 1);
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Pipeline priorizado</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-4 md:px-6 pb-16 pt-6">
		<div class="max-w-6xl mx-auto space-y-6">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Pipeline priorizado</h1>
				<p class="text-muted-foreground">Deals ordenados por score, com sugestões de ação para cada etapa.</p>
			</div>

			<div class="flex flex-wrap gap-2">
				{#each filters as filter}
					<button
						class="px-4 py-2 rounded-full text-sm border transition-colors {activeFilter === filter.key ? 'bg-primary text-primary-foreground border-primary' : 'bg-card text-muted-foreground border-border hover:text-foreground'}"
						onclick={() => { activeFilter = filter.key; currentPage = 1; }}
					>
						{filter.label}
					</button>
				{/each}
			</div>

			<div class="grid grid-cols-1 gap-4">
				{#if loading}
					<div class="text-sm text-muted-foreground">Carregando deals...</div>
				{:else}
					{#each deals as deal}
					{@const StatusIcon = statusIcon(deal.status)}
					<div class="p-4 md:p-5 rounded-2xl border border-border bg-card shadow-sm flex flex-col gap-4">
						<div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									<span class="text-lg font-semibold text-foreground">{deal.name}</span>
									<span class="text-xs uppercase tracking-wider px-2 py-1 rounded-full border {statusColor(deal.status)}">
										<StatusIcon class="inline w-3 h-3 mr-1" />
										{deal.status === 'hot' ? 'Quente' : deal.status === 'risk' ? 'Em risco' : 'Estagnado'}
									</span>
								</div>
								<div class="text-sm text-muted-foreground">
									Stage: {deal.stage} · {deal.days} dias · {deal.value}
								</div>
								<div class="text-sm text-primary">{deal.action}</div>
							</div>
							<div class="text-right space-y-1">
								<div class="text-2xl font-semibold text-foreground">{deal.score}</div>
								<div class="text-xs uppercase tracking-wider text-muted-foreground">score</div>
								<div class="text-xs text-emerald-600 flex items-center gap-1">
									<TrendingUp class="w-3 h-3" />
									{deal.trend} vs média
								</div>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<div class="text-xs text-muted-foreground">
								Última atividade: há {typeof deal.days === 'number' ? Math.max(1, Math.floor(deal.days / 3)) : '-'} dias
							</div>
							<button
								class="text-xs text-primary flex items-center gap-1"
								onclick={() => openDealModal(deal.id)}
							>
								Abrir deal <ArrowUpRight class="w-3 h-3" />
							</button>
						</div>
					</div>
					{/each}
				{/if}
			</div>

			{#if total > 0}
			<div class="flex items-center justify-between pt-4 border-t border-border">
				<div class="text-sm text-muted-foreground">
					{total} deal(s) · Página {currentPage} de {totalPages}
				</div>
				<div class="flex items-center gap-2">
					<button
						class="px-3 py-1.5 rounded-lg border border-border text-sm disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={!hasPrev}
						onclick={() => { currentPage--; }}
					>
						<ChevronLeft class="w-4 h-4 inline" /> Anterior
					</button>
					<button
						class="px-3 py-1.5 rounded-lg border border-border text-sm disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={!hasNext}
						onclick={() => { currentPage++; }}
					>
						Próxima <ChevronRight class="w-4 h-4 inline" />
					</button>
				</div>
			</div>
			{/if}
		</div>
	</div>

	<!-- Deal Detail Modal -->
	{#if modalDealId}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
			role="dialog"
			aria-modal="true"
			tabindex="-1"
			onclick={(e) => e.target === e.currentTarget && closeModal()}
			onkeydown={(e) => e.key === 'Escape' && closeModal()}
		>
			<div class="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border bg-card shadow-xl text-foreground" role="document" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()}>
				<button
					class="absolute top-4 right-4 w-8 h-8 rounded-full bg-background/80 flex items-center justify-center hover:bg-background"
					onclick={closeModal}
					aria-label="Fechar"
				>
					<X class="w-4 h-4" />
				</button>

				{#if modalLoading}
					<div class="p-8 text-center text-muted-foreground">Carregando...</div>
				{:else if modalDeal}
					<div class="p-6 space-y-6">
						<div>
							<h2 class="text-2xl font-bold text-foreground">{modalDeal.name ?? modalDeal.Name ?? '-'}</h2>
							<p class="text-sm text-muted-foreground">Detalhes do deal e fatores do score</p>
						</div>

						<div class="grid grid-cols-2 gap-4 text-sm">
							<div>
								<div class="text-xs text-muted-foreground">Valor</div>
								<div class="font-semibold">{typeof modalDeal.value === 'number' ? modalDeal.value.toLocaleString('pt-BR') : modalDeal.value ?? '-'}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Owner</div>
								<div class="font-medium">{modalDeal.owner ?? modalDeal.Owner ?? '-'}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Stage</div>
								<div>{modalDeal.stage ?? modalDeal.Stage ?? '-'}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Dias no pipeline</div>
								<div>{modalDeal.days ?? modalDeal.Days ?? '-'}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Score</div>
								<div class="font-semibold">{modalDeal.score ?? modalDeal.Score ?? '-'}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Tendência</div>
								<div class="text-emerald-600">{formatTrend(modalDeal.trend ?? modalDeal.Trend ?? 0)}</div>
							</div>
						</div>

						{#if (modalDeal.next_actions ?? modalDeal.nextActions ?? []).length > 0}
						<div>
							<div class="font-semibold mb-2">Próximas ações sugeridas</div>
							<ul class="space-y-2 text-sm text-muted-foreground">
								{#each modalDeal.next_actions ?? modalDeal.nextActions ?? [] as action}
									<li class="flex items-start gap-2">• {action}</li>
								{/each}
							</ul>
						</div>
						{/if}

						{#if (modalDeal.factors ?? modalDeal.Factors ?? []).length > 0}
						<div>
							<div class="font-semibold mb-2">Fatores do score</div>
							<table class="w-full text-sm">
								<thead>
									<tr class="text-xs uppercase tracking-wider text-muted-foreground border-b border-border">
										<th class="text-left py-2">Fator</th>
										<th class="text-left py-2">Impacto</th>
										<th class="text-left py-2">Detalhe</th>
									</tr>
								</thead>
								<tbody>
									{#each modalDeal.factors ?? modalDeal.Factors ?? [] as f}
										<tr class="border-b border-border/60">
											<td class="py-2">{f.factor ?? f.Name ?? '-'}</td>
											<td class="py-2">
												<span class="px-2 py-0.5 rounded text-xs {sentimentColor(f.sentiment ?? 'neutral')}">
													{f.impact ?? f.Impact ?? 0}
												</span>
											</td>
											<td class="py-2 text-muted-foreground">{f.detail ?? f.Detail ?? '-'}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						{/if}
					</div>
				{:else}
					<div class="p-8 text-center text-muted-foreground">Deal não encontrado</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<svelte:window onkeydown={(e) => { if (modalDealId && e.key === 'Escape') closeModal(); }} />
