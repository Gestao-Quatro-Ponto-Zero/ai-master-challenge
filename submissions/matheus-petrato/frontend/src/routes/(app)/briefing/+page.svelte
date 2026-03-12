<script lang="ts">
	import {
		TrendingUp,
		AlertTriangle,
		Flame,
		Sparkles,
		Target,
		Calendar,
		ArrowUpRight,
		Users
	} from 'lucide-svelte';
	import { role } from '$lib/stores/role';

	const kpis = [
		{ label: 'Pipeline total', value: 'R$ 3,36M', delta: '+6,2%', icon: TrendingUp },
		{ label: 'Deals em risco', value: '18', delta: '+4', icon: AlertTriangle },
		{ label: 'Win rate', value: '63%', delta: '+2,1%', icon: Target },
		{ label: 'Ciclo medio', value: '52 dias', delta: '-3 dias', icon: Calendar }
	];

	const hotDeals = [
		{ name: 'Acme Logistica', score: 92, stage: 'Engaging', value: 'R$ 420k', days: 18, action: 'Agendar call final' },
		{ name: 'Northwind Tech', score: 88, stage: 'Engaging', value: 'R$ 310k', days: 26, action: 'Confirmar decisor' },
		{ name: 'Atlas Health', score: 84, stage: 'Prospecting', value: 'R$ 180k', days: 11, action: 'Enviar proposta' }
	];

	const riskDeals = [
		{ name: 'Umbrella Foods', score: 42, stage: 'Engaging', value: 'R$ 260k', days: 74, action: 'Reengajar sponsor' },
		{ name: 'Pineapple Retail', score: 39, stage: 'Prospecting', value: 'R$ 140k', days: 61, action: 'Revisar proxima etapa' },
		{ name: 'Helios Energy', score: 35, stage: 'Engaging', value: 'R$ 520k', days: 89, action: 'Escalar com manager' }
	];

	const insights = [
		'3 deals entraram na janela ideal de fechamento esta semana.',
		'Deals acima de 70 dias estao com perda acelerada. Priorize follow-up.',
		'Sua taxa de ganho no stage Engaging esta 8% acima da media do time.'
	];

	const teamSnapshot = [
		{ label: 'Vendedores ativos', value: '35', icon: Users },
		{ label: 'Deals criticos', value: '22', icon: AlertTriangle },
		{ label: 'Pipeline por regiao', value: 'Central +12%', icon: TrendingUp }
	];
</script>

<div class="flex-1 flex flex-col h-full bg-background relative overflow-hidden text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white z-10">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Briefing semanal</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-4 md:px-6 pb-16 pt-6">
		<div class="max-w-6xl mx-auto space-y-8">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Seu briefing do dia</h1>
				<p class="text-muted-foreground">Prioridades, alertas e proximos passos recomendados pelo Compass.</p>
			</div>

			{#if $role === 'manager'}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each teamSnapshot as item}
					<div class="p-4 rounded-2xl border border-border bg-card shadow-sm flex items-center gap-3">
							<div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
								<item.icon class="w-5 h-5" />
							</div>
							<div>
								<div class="text-xs uppercase tracking-wider text-muted-foreground">{item.label}</div>
								<div class="text-lg font-semibold text-foreground">{item.value}</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				{#each kpis as kpi}
					<div class="p-4 rounded-2xl border border-border bg-card shadow-sm">
						<div class="flex items-center justify-between">
							<div class="text-xs uppercase tracking-wider text-muted-foreground">{kpi.label}</div>
							<kpi.icon class="w-4 h-4 text-primary" />
						</div>
						<div class="mt-3 text-2xl font-semibold text-foreground">{kpi.value}</div>
						<div class="text-xs text-emerald-600 mt-1">{kpi.delta} vs semana passada</div>
					</div>
				{/each}
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2 text-foreground font-semibold">
							<Flame class="w-4 h-4 text-primary" />
							Deals quentes
						</div>
						<button class="text-xs text-primary flex items-center gap-1">
							Ver pipeline <ArrowUpRight class="w-3 h-3" />
						</button>
					</div>
					<div class="space-y-3">
						{#each hotDeals as deal}
							<div class="p-4 rounded-2xl border border-border bg-card shadow-sm flex items-center justify-between">
								<div class="space-y-1">
									<div class="font-semibold text-foreground">{deal.name}</div>
									<div class="text-xs text-muted-foreground">{deal.stage} · {deal.days} dias · {deal.value}</div>
									<div class="text-xs text-primary">{deal.action}</div>
								</div>
								<div class="text-right">
									<div class="text-sm font-semibold text-foreground">{deal.score}</div>
									<div class="text-[10px] uppercase tracking-wider text-muted-foreground">score</div>
								</div>
							</div>
						{/each}
					</div>
				</div>

				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2 text-foreground font-semibold">
							<AlertTriangle class="w-4 h-4 text-amber-500" />
							Em risco
						</div>
						<button class="text-xs text-primary flex items-center gap-1">
							Ver alertas <ArrowUpRight class="w-3 h-3" />
						</button>
					</div>
					<div class="space-y-3">
						{#each riskDeals as deal}
							<div class="p-4 rounded-2xl border border-border bg-card shadow-sm flex items-center justify-between">
								<div class="space-y-1">
									<div class="font-semibold text-foreground">{deal.name}</div>
									<div class="text-xs text-muted-foreground">{deal.stage} · {deal.days} dias · {deal.value}</div>
									<div class="text-xs text-amber-600">{deal.action}</div>
								</div>
								<div class="text-right">
									<div class="text-sm font-semibold text-foreground">{deal.score}</div>
									<div class="text-[10px] uppercase tracking-wider text-muted-foreground">score</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<div class="p-6 rounded-2xl border border-border bg-card shadow-sm">
				<div class="flex items-center gap-2 text-foreground font-semibold mb-3">
					<Sparkles class="w-4 h-4 text-primary" />
					Insight do Compass
				</div>
				<ul class="space-y-2 text-sm text-muted-foreground">
					{#each insights as item}
						<li class="flex items-start gap-2">
							<span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary/70"></span>
							<span>{item}</span>
						</li>
					{/each}
				</ul>
			</div>
		</div>
	</div>
</div>
