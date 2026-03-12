<script lang="ts">
	import { Bell, AlertTriangle, Clock, ArrowUpRight, CheckCircle2 } from 'lucide-svelte';

	const todayAlerts = [
		{
			title: 'Deal entrou na janela ideal',
			deal: 'Acme Logistica',
			time: '09:12',
			type: 'positive',
			action: 'Agendar call final'
		},
		{
			title: 'Deal estagnado acima do ciclo medio',
			deal: 'Umbrella Foods',
			time: '11:40',
			type: 'risk',
			action: 'Reengajar sponsor'
		}
	];

	const weekAlerts = [
		{
			title: 'Briefing semanal enviado',
			deal: 'Resumo do pipeline',
			time: 'Seg, 08:00',
			type: 'info',
			action: 'Abrir briefing'
		},
		{
			title: 'Deal em risco sem atividade',
			deal: 'Helios Energy',
			time: 'Ter, 16:30',
			type: 'risk',
			action: 'Escalar com manager'
		},
		{
			title: 'Deal acelerou para stage final',
			deal: 'Northwind Tech',
			time: 'Qua, 10:05',
			type: 'positive',
			action: 'Confirmar decisor'
		}
	];

	const badgeStyle = (type: string) => {
		if (type === 'positive') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
		if (type === 'risk') return 'bg-amber-50 text-amber-700 border-amber-200';
		return 'bg-slate-50 text-slate-600 border-slate-200';
	};

	const iconFor = (type: string) => (type === 'risk' ? AlertTriangle : CheckCircle2);
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Alertas</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-4 md:px-6 pb-16 pt-6">
		<div class="max-w-5xl mx-auto space-y-8">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
					<Bell class="w-5 h-5" />
				</div>
				<div>
					<h1 class="text-3xl font-bold tracking-tight text-foreground">Alertas proativos</h1>
					<p class="text-muted-foreground">Recomendacoes e sinais criticos do seu pipeline.</p>
				</div>
			</div>

			<div class="space-y-4">
				<div class="flex items-center justify-between">
					<div class="text-sm font-semibold text-foreground">Hoje</div>
					<button class="text-xs text-primary flex items-center gap-1">
						Marcar tudo como lido <ArrowUpRight class="w-3 h-3" />
					</button>
				</div>
				<div class="space-y-3">
					{#each todayAlerts as alert}
						<div class="p-4 rounded-2xl border border-border bg-card shadow-sm flex items-center justify-between gap-4">
							<div class="flex items-start gap-3">
								<div class="w-9 h-9 rounded-lg border {badgeStyle(alert.type)} flex items-center justify-center">
									<svelte:component this={iconFor(alert.type)} class="w-4 h-4" />
								</div>
								<div class="space-y-1">
									<div class="text-sm font-semibold text-foreground">{alert.title}</div>
									<div class="text-xs text-muted-foreground">{alert.deal}</div>
									<div class="text-xs text-primary">{alert.action}</div>
								</div>
							</div>
							<div class="text-xs text-muted-foreground flex items-center gap-1">
								<Clock class="w-3 h-3" />
								{alert.time}
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="space-y-4">
				<div class="text-sm font-semibold text-foreground">Ultimos 7 dias</div>
				<div class="space-y-3">
					{#each weekAlerts as alert}
						<div class="p-4 rounded-2xl border border-border bg-card shadow-sm flex items-center justify-between gap-4">
							<div class="flex items-start gap-3">
								<div class="w-9 h-9 rounded-lg border {badgeStyle(alert.type)} flex items-center justify-center">
									<svelte:component this={iconFor(alert.type)} class="w-4 h-4" />
								</div>
								<div class="space-y-1">
									<div class="text-sm font-semibold text-foreground">{alert.title}</div>
									<div class="text-xs text-muted-foreground">{alert.deal}</div>
									<div class="text-xs text-primary">{alert.action}</div>
								</div>
							</div>
							<div class="text-xs text-muted-foreground flex items-center gap-1">
								<Clock class="w-3 h-3" />
								{alert.time}
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>
