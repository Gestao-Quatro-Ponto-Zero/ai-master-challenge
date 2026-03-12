<script lang="ts">
	import { ArrowUpRight, TrendingUp, AlertTriangle, CheckCircle2, Sparkles } from 'lucide-svelte';

	const deal = {
		name: 'Acme Logistica',
		score: 92,
		stage: 'Engaging',
		days: 18,
		value: 'R$ 420k',
		owner: 'Camila Torres',
		trend: '+12%'
	};

	const factors = [
		{ factor: 'Timing vs ciclo medio', impact: '+18', detail: '18 dias vs 52 dias', sentiment: 'positive' },
		{ factor: 'Stage atual', impact: '+12', detail: 'Engaging acima da media', sentiment: 'positive' },
		{ factor: 'Produto', impact: '+8', detail: 'Win rate historico 68%', sentiment: 'positive' },
		{ factor: 'Conta (setor)', impact: '+5', detail: 'Setor com crescimento', sentiment: 'positive' },
		{ factor: 'Ultima atividade', impact: '-6', detail: 'Sem toque ha 5 dias', sentiment: 'negative' },
		{ factor: 'Decay', impact: '-2', detail: 'Aproxima limite ideal', sentiment: 'negative' }
	];

	const nextActions = [
		'Agendar call de decisao com o sponsor',
		'Enviar proposta atualizada com ROI',
		'Validar proximo passo com o champion'
	];

	const sentimentColor = (sentiment: string) =>
		sentiment === 'positive'
			? 'text-emerald-600 bg-emerald-50 border-emerald-200'
			: 'text-amber-600 bg-amber-50 border-amber-200';

	const sentimentIcon = (sentiment: string) => (sentiment === 'positive' ? TrendingUp : AlertTriangle);
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Deal detail</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-6 pb-10 pt-8">
		<div class="max-w-6xl mx-auto space-y-8">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">{deal.name}</h1>
				<p class="text-muted-foreground">Entenda o score e o que fazer agora para acelerar o fechamento.</p>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-6">
				<div class="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-4">
					<div class="flex items-center justify-between">
						<div>
							<div class="text-xs uppercase tracking-wider text-muted-foreground">Resumo do deal</div>
							<div class="text-xl font-semibold text-foreground">{deal.value}</div>
						</div>
						<div class="text-right">
							<div class="text-xs text-muted-foreground">Owner</div>
							<div class="text-sm font-medium text-foreground">{deal.owner}</div>
						</div>
					</div>
					<div class="grid grid-cols-2 gap-3 text-sm text-muted-foreground">
						<div>Stage: <span class="text-foreground">{deal.stage}</span></div>
						<div>Dias no pipeline: <span class="text-foreground">{deal.days}</span></div>
						<div>Score atual: <span class="text-foreground">{deal.score}</span></div>
						<div>Tendencia: <span class="text-emerald-600">{deal.trend}</span></div>
					</div>
					<div class="flex items-center gap-3">
						<button class="px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm">Atualizar stage</button>
						<button class="px-4 py-2 rounded-full border border-border text-sm text-muted-foreground hover:text-foreground">Abrir CRM</button>
					</div>
				</div>

				<div class="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-4">
					<div class="flex items-center gap-2 text-foreground font-semibold">
						<Sparkles class="w-4 h-4 text-primary" />
						Proximas acoes sugeridas
					</div>
					<ul class="space-y-3 text-sm text-muted-foreground">
						{#each nextActions as action}
							<li class="flex items-start gap-3">
								<CheckCircle2 class="w-4 h-4 text-emerald-600 mt-0.5" />
								<span>{action}</span>
							</li>
						{/each}
					</ul>
					<button class="text-xs text-primary flex items-center gap-1">
						Gerar plano completo <ArrowUpRight class="w-3 h-3" />
					</button>
				</div>
			</div>

			<div class="p-6 rounded-2xl border border-border bg-card shadow-sm">
				<div class="flex items-center justify-between mb-4">
					<div class="text-foreground font-semibold">Fatores do score</div>
					<div class="text-xs text-muted-foreground">Explainability do Compass</div>
				</div>
				<div class="w-full overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="text-xs uppercase tracking-wider text-muted-foreground border-b border-border">
								<th class="text-left py-3">Fator</th>
								<th class="text-left py-3">Impacto</th>
								<th class="text-left py-3">Comparacao</th>
							</tr>
						</thead>
						<tbody>
							{#each factors as item}
								<tr class="border-b border-border/60">
									<td class="py-3 text-foreground">{item.factor}</td>
									<td class="py-3">
										<span class="px-2 py-1 rounded-full border text-xs {sentimentColor(item.sentiment)}">
											<svelte:component this={sentimentIcon(item.sentiment)} class="inline w-3 h-3 mr-1" />
											{item.impact}
										</span>
									</td>
									<td class="py-3 text-muted-foreground">{item.detail}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</div>
