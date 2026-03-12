<script lang="ts">
	import { TrendingUp, Users, Target, AlertTriangle, BarChart3 } from 'lucide-svelte';
	import { role } from '$lib/stores/role';

	const kpis = [
		{ label: 'Pipeline total', value: 'R$ 3,36M', delta: '+6,2%', icon: TrendingUp },
		{ label: 'Win rate', value: '63%', delta: '+2,1%', icon: Target },
		{ label: 'Deals criticos', value: '22', delta: '+5', icon: AlertTriangle },
		{ label: 'Vendedores ativos', value: '35', delta: '+1', icon: Users }
	];

	const byRegion = [
		{ region: 'Central', value: 'R$ 1,42M', delta: '+12%' },
		{ region: 'East', value: 'R$ 980k', delta: '+4%' },
		{ region: 'West', value: 'R$ 960k', delta: '-3%' }
	];

	const byStage = [
		{ stage: 'Prospecting', value: '34%', note: 'Gargalo inicial' },
		{ stage: 'Engaging', value: '52%', note: 'Estavel' },
		{ stage: 'Closing', value: '14%', note: 'Abaixo da media' }
	];

	const topSellers = [
		{ name: 'Camila Torres', winRate: '70%', pipeline: 'R$ 420k', trend: '+8%' },
		{ name: 'Felipe Costa', winRate: '66%', pipeline: 'R$ 380k', trend: '+5%' },
		{ name: 'Rafael Dias', winRate: '62%', pipeline: 'R$ 310k', trend: '-2%' }
	];
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Relatorios do manager</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-4 md:px-6 pb-16 pt-6">
		{#if $role === 'manager'}
			<div class="max-w-6xl mx-auto space-y-8">
				<div class="flex flex-col gap-2">
					<h1 class="text-3xl font-bold tracking-tight text-foreground">Visao macro do time</h1>
					<p class="text-muted-foreground">Resumo executivo do pipeline por regiao, stage e performance.</p>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
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
					<div class="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-4">
						<div class="flex items-center gap-2 text-foreground font-semibold">
							<BarChart3 class="w-4 h-4 text-primary" />
							Pipeline por regiao
						</div>
						<div class="space-y-3">
							{#each byRegion as item}
								<div class="flex items-center justify-between text-sm">
									<div class="text-foreground">{item.region}</div>
									<div class="text-right">
										<div class="text-foreground font-medium">{item.value}</div>
										<div class="text-xs text-muted-foreground">{item.delta} vs mes passado</div>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<div class="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-4">
						<div class="flex items-center gap-2 text-foreground font-semibold">
							<TrendingUp class="w-4 h-4 text-primary" />
							Gargalos por stage
						</div>
						<div class="space-y-3">
							{#each byStage as item}
								<div class="flex items-center justify-between text-sm">
									<div class="text-foreground">{item.stage}</div>
									<div class="text-right">
										<div class="text-foreground font-medium">{item.value}</div>
										<div class="text-xs text-muted-foreground">{item.note}</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div class="p-6 rounded-2xl border border-border bg-card shadow-sm">
					<div class="flex items-center gap-2 text-foreground font-semibold mb-4">
						<Users class="w-4 h-4 text-primary" />
						Top vendedores
					</div>
					<div class="w-full overflow-x-auto">
						<table class="w-full text-sm">
							<thead>
								<tr class="text-xs uppercase tracking-wider text-muted-foreground border-b border-border">
									<th class="text-left py-3">Vendedor</th>
									<th class="text-left py-3">Win rate</th>
									<th class="text-left py-3">Pipeline</th>
									<th class="text-left py-3">Tendencia</th>
								</tr>
							</thead>
							<tbody>
								{#each topSellers as seller}
									<tr class="border-b border-border/60">
										<td class="py-3 text-foreground">{seller.name}</td>
										<td class="py-3 text-foreground">{seller.winRate}</td>
										<td class="py-3 text-foreground">{seller.pipeline}</td>
										<td class="py-3 text-emerald-600">{seller.trend}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		{:else}
			<div class="max-w-3xl mx-auto">
				<div class="p-6 rounded-2xl border border-border bg-card shadow-sm">
					<h1 class="text-2xl font-semibold text-foreground mb-2">Acesso restrito</h1>
					<p class="text-muted-foreground">Relatorios do time ficam disponiveis apenas para managers.</p>
				</div>
			</div>
		{/if}
	</div>
</div>
