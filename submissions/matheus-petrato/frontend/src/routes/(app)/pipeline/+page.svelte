<script lang="ts">
	import { Flame, AlertTriangle, Timer, TrendingUp, ArrowUpRight } from 'lucide-svelte';

	const filters = [
		{ label: 'Todos', key: 'all' },
		{ label: 'Quentes', key: 'hot' },
		{ label: 'Em risco', key: 'risk' },
		{ label: 'Estagnados', key: 'stalled' }
	];

	let activeFilter = $state('all');

	const deals = [
		{
			name: 'Acme Logistica',
			score: 92,
			stage: 'Engaging',
			days: 18,
			value: 'R$ 420k',
			trend: '+12%',
			status: 'hot',
			action: 'Agendar call final'
		},
		{
			name: 'Northwind Tech',
			score: 88,
			stage: 'Engaging',
			days: 26,
			value: 'R$ 310k',
			trend: '+9%',
			status: 'hot',
			action: 'Confirmar decisor'
		},
		{
			name: 'Umbrella Foods',
			score: 42,
			stage: 'Engaging',
			days: 74,
			value: 'R$ 260k',
			trend: '-8%',
			status: 'risk',
			action: 'Reengajar sponsor'
		},
		{
			name: 'Pineapple Retail',
			score: 39,
			stage: 'Prospecting',
			days: 61,
			value: 'R$ 140k',
			trend: '-12%',
			status: 'stalled',
			action: 'Revisar proxima etapa'
		},
		{
			name: 'Helios Energy',
			score: 35,
			stage: 'Engaging',
			days: 89,
			value: 'R$ 520k',
			trend: '-15%',
			status: 'risk',
			action: 'Escalar com manager'
		}
	];

	const filteredDeals = $derived(
		activeFilter === 'all' ? deals : deals.filter((deal) => deal.status === activeFilter)
	);

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

	<div class="flex-1 overflow-y-auto px-6 pb-10 pt-8">
		<div class="max-w-6xl mx-auto space-y-6">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Pipeline priorizado</h1>
				<p class="text-muted-foreground">Deals ordenados por score, com sugestoes de acao para cada etapa.</p>
			</div>

			<div class="flex flex-wrap gap-2">
				{#each filters as filter}
					<button
						class="px-4 py-2 rounded-full text-sm border transition-colors {activeFilter === filter.key ? 'bg-primary text-primary-foreground border-primary' : 'bg-card text-muted-foreground border-border hover:text-foreground'}"
						onclick={() => (activeFilter = filter.key)}
					>
						{filter.label}
					</button>
				{/each}
			</div>

			<div class="grid grid-cols-1 gap-4">
				{#each filteredDeals as deal}
					<div class="p-5 rounded-2xl border border-border bg-card shadow-sm flex flex-col gap-4">
						<div class="flex items-start justify-between gap-4">
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									<span class="text-lg font-semibold text-foreground">{deal.name}</span>
									<span class="text-xs uppercase tracking-wider px-2 py-1 rounded-full border {statusColor(deal.status)}">
										<svelte:component this={statusIcon(deal.status)} class="inline w-3 h-3 mr-1" />
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
									{deal.trend} vs media
								</div>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<div class="text-xs text-muted-foreground">Ultima atividade: ha {Math.max(1, Math.floor(deal.days / 3))} dias</div>
							<button class="text-xs text-primary flex items-center gap-1">
								Abrir deal <ArrowUpRight class="w-3 h-3" />
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>
