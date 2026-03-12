<script lang="ts">
	import { UploadCloud, FileText, CheckCircle2, Clock, AlertTriangle, ArrowUpRight } from 'lucide-svelte';

	const uploads = [
		{ name: 'sales_pipeline.csv', size: '2.1 MB', status: 'processed', updated: 'Hoje, 09:12' },
		{ name: 'accounts.csv', size: '420 KB', status: 'processing', updated: 'Hoje, 08:45' },
		{ name: 'products.csv', size: '180 KB', status: 'error', updated: 'Ontem, 18:32' }
	];

	const statusBadge = (status: string) => {
		if (status === 'processed') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
		if (status === 'processing') return 'bg-amber-50 text-amber-700 border-amber-200';
		return 'bg-red-50 text-red-700 border-red-200';
	};

	const statusLabel = (status: string) =>
		status === 'processed' ? 'Processado' : status === 'processing' ? 'Processando' : 'Falha';

	const statusIcon = (status: string) =>
		status === 'processed' ? CheckCircle2 : status === 'processing' ? Clock : AlertTriangle;
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Importacao de CSV</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-6 pb-10 pt-8">
		<div class="max-w-5xl mx-auto space-y-8">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Gestao de bases</h1>
				<p class="text-muted-foreground">
					O manager pode subir CSVs para alimentar o pipeline. Em breve integraremos CRM direto.
				</p>
			</div>

			<div class="p-6 rounded-2xl border border-dashed border-border bg-card shadow-sm">
				<div class="flex flex-col items-center text-center gap-3">
					<div class="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
						<UploadCloud class="w-6 h-6" />
					</div>
					<div class="text-sm text-foreground font-semibold">Arraste e solte seus CSVs aqui</div>
					<div class="text-xs text-muted-foreground">Formatos aceitos: sales_pipeline, accounts, products, sales_teams.</div>
					<button class="px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm">
						Selecionar arquivo
					</button>
				</div>
			</div>

			<div class="p-6 rounded-2xl border border-border bg-card shadow-sm">
				<div class="flex items-center justify-between mb-4">
					<div class="text-foreground font-semibold">Uploads recentes</div>
					<button class="text-xs text-primary flex items-center gap-1">
						Ver historico completo <ArrowUpRight class="w-3 h-3" />
					</button>
				</div>
				<div class="w-full overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="text-xs uppercase tracking-wider text-muted-foreground border-b border-border">
								<th class="text-left py-3">Arquivo</th>
								<th class="text-left py-3">Status</th>
								<th class="text-left py-3">Atualizado</th>
								<th class="text-left py-3">Acoes</th>
							</tr>
						</thead>
						<tbody>
							{#each uploads as item}
								<tr class="border-b border-border/60">
									<td class="py-3 text-foreground flex items-center gap-2">
										<FileText class="w-4 h-4 text-primary" />
										{item.name}
										<span class="text-xs text-muted-foreground">({item.size})</span>
									</td>
									<td class="py-3">
										<span class="px-2 py-1 rounded-full border text-xs {statusBadge(item.status)}">
											<svelte:component this={statusIcon(item.status)} class="inline w-3 h-3 mr-1" />
											{statusLabel(item.status)}
										</span>
									</td>
									<td class="py-3 text-muted-foreground">{item.updated}</td>
									<td class="py-3 text-xs text-primary space-x-3">
										<button>Mapear</button>
										<button>Reprocessar</button>
										<button class="text-red-600">Remover</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</div>
