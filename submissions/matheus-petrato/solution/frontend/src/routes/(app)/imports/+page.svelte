<script lang="ts">
	import { UploadCloud, FileText, CheckCircle2, Clock, AlertTriangle, ArrowUpRight } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { api } from '$lib/services/api';

	let uploads = $state<any[]>([]);
	let uploading = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');
	let selectedType = $state('deals');

	const importTypes = [
		{ label: 'Pipeline (sales_pipeline)', value: 'deals' },
		{ label: 'Accounts', value: 'accounts' },
		{ label: 'Produtos', value: 'products' },
		{ label: 'Time (sales_teams)', value: 'team' }
	];

	const sourceLabel = (type: string) => {
		if (type === 'team') return 'Time';
		if (type === 'accounts') return 'Accounts';
		if (type === 'products') return 'Produtos';
		if (type === 'deals') return 'Pipeline';
		return '-';
	};

	const statusBadge = (status: string) => {
		if (status === 'processed') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
		if (status === 'processing') return 'bg-amber-50 text-amber-700 border-amber-200';
		return 'bg-rose-50 text-rose-700 border-rose-200';
	};

	const statusLabel = (status: string) =>
		status === 'processed' ? 'Processado' : status === 'processing' ? 'Processando' : 'Falha';

	const statusIcon = (status: string) =>
		status === 'processed' ? CheckCircle2 : status === 'processing' ? Clock : AlertTriangle;

	const normalizeStatus = (status: string) => {
		if (status === 'success' || status === 'done') return 'processed';
		if (status === 'failed') return 'error';
		if (['pending', 'validating', 'preview', 'importing'].includes(status)) return 'processing';
		return status;
	};

	const inferTypeFromName = (name: string) => {
		const fileName = name.toLowerCase();
		if (fileName.includes('sales_pipeline') || fileName.includes('pipeline')) return 'deals';
		if (fileName.includes('accounts')) return 'accounts';
		if (fileName.includes('products')) return 'products';
		if (fileName.includes('sales_teams') || fileName.includes('teams') || fileName.includes('team')) return 'team';
		return selectedType;
	};

	const formatSize = (value: any) => {
		if (typeof value !== 'number') return value ?? '-';
		if (value > 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
		if (value > 1024) return `${Math.round(value / 1024)} KB`;
		return `${value} B`;
	};

	const loadImports = async () => {
		try {
			const data = await api.imports.list();
			uploads = (data || []).map((item: any) => ({
				id: item.id ?? item.ID,
				name: item.file ?? item.File ?? '-',
				size: formatSize(item.size ?? item.Size),
				status: normalizeStatus(item.status ?? item.Status ?? 'processing'),
				updated: item.updated_at ?? item.updatedAt ?? '-',
				sourceType: item.source_type ?? item.SourceType ?? item.sourceType ?? '',
				sourceLabel: sourceLabel(item.source_type ?? item.SourceType ?? item.sourceType ?? '')
			}));
		} catch (err) {
			console.warn('Falha ao carregar imports:', err);
		}
	};

	const teamReady = $derived(uploads.some((item) => item.sourceType === 'team' && item.status === 'processed'));
	const productsReady = $derived(uploads.some((item) => item.sourceType === 'products' && item.status === 'processed'));
	const accountsReady = $derived(uploads.some((item) => item.sourceType === 'accounts' && item.status === 'processed'));
	const pipelineReady = $derived(uploads.some((item) => item.sourceType === 'deals' && item.status === 'processed'));

	const isBlocked = $derived.by(() => {
		if (selectedType === 'products' || selectedType === 'accounts') {
			return !teamReady;
		}
		if (selectedType === 'deals') {
			return !(teamReady && productsReady && accountsReady);
		}
		return false;
	});

	const blockReason = $derived.by(() => {
		if (selectedType === 'products' || selectedType === 'accounts') {
			return 'Importe primeiro o time (sales_teams.csv) para cadastrar vendedores.';
		}
		if (selectedType === 'deals') {
			if (!teamReady) return 'Importe primeiro o time (sales_teams.csv).';
			if (!productsReady || !accountsReady) return 'Importe produtos e contas antes do pipeline.';
		}
		return '';
	});

	const handleFileInput = async (event: Event) => {
		const input = event.target as HTMLInputElement;
		if (!input.files || input.files.length === 0) return;
		const file = input.files[0];
		selectedType = inferTypeFromName(file.name);
		if (isBlocked) {
			errorMessage = blockReason || 'Importacao bloqueada pela ordem de dependencias.';
			input.value = '';
			return;
		}
		uploading = true;
		errorMessage = '';
		successMessage = '';
		try {
			await api.imports.upload(file, selectedType);
			successMessage = 'Upload iniciado com sucesso.';
			await loadImports();
		} catch (err: any) {
			errorMessage = err.message || 'Falha ao enviar arquivo.';
		} finally {
			uploading = false;
			input.value = '';
		}
	};

	const handleReprocess = async (id: string) => {
		try {
			await api.imports.reprocess(id);
			await loadImports();
		} catch (err) {
			console.warn('Falha ao reprocessar:', err);
		}
	};

	const handleRemove = async (id: string) => {
		try {
			await api.imports.remove(id);
			await loadImports();
		} catch (err) {
			console.warn('Falha ao remover:', err);
		}
	};

	onMount(loadImports);
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

	<div class="flex-1 overflow-y-auto px-4 md:px-6 pb-16 pt-6">
		<div class="max-w-5xl mx-auto space-y-8">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Gestao de bases</h1>
				<p class="text-muted-foreground">
					O manager pode subir CSVs para alimentar o pipeline. Em breve integraremos CRM direto.
				</p>
			</div>

			<div class="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-4">
				<div>
					<div class="text-foreground font-semibold">Caminho feliz para popular os dashboards</div>
					<p class="text-sm text-muted-foreground">
						Alguns dados dependem do anterior. Siga a ordem abaixo para liberar KPIs, Pipeline e o Compass Chat.
					</p>
				</div>
				<div class="grid gap-3">
					<div class="flex items-center justify-between rounded-xl border border-border/60 bg-background px-4 py-3 text-sm">
						<div>
							<div class="font-medium text-foreground">1. Time (sales_teams.csv)</div>
							<div class="text-xs text-muted-foreground">Cadastra vendedores e regioes.</div>
						</div>
						<span class="text-xs px-2.5 py-1 rounded-full border {teamReady ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}">
							{teamReady ? 'Pronto' : 'Pendente'}
						</span>
					</div>
					<div class="flex items-center justify-between rounded-xl border border-border/60 bg-background px-4 py-3 text-sm">
						<div>
							<div class="font-medium text-foreground">2. Produtos & Accounts (products.csv + accounts.csv)</div>
							<div class="text-xs text-muted-foreground">Ativa graficos por produto e setor.</div>
						</div>
						<span class="text-xs px-2.5 py-1 rounded-full border {(productsReady && accountsReady) ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}">
							{(productsReady && accountsReady) ? 'Pronto' : 'Pendente'}
						</span>
					</div>
					<div class="flex items-center justify-between rounded-xl border border-border/60 bg-background px-4 py-3 text-sm">
						<div>
							<div class="font-medium text-foreground">3. Pipeline (sales_pipeline.csv)</div>
							<div class="text-xs text-muted-foreground">Libera KPIs, ranking e respostas do Compass.</div>
						</div>
						<span class="text-xs px-2.5 py-1 rounded-full border {pipelineReady ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}">
							{pipelineReady ? 'Pronto' : 'Pendente'}
						</span>
					</div>
				</div>
				<div class="text-xs text-muted-foreground">
					Endpoints que ganham vida: <span class="text-foreground">GET /api/deals</span>, <span class="text-foreground">GET /api/stats/team</span>, <span class="text-foreground">GET /api/briefing</span>, <span class="text-foreground">POST /api/chat</span>.
				</div>
			</div>

			<div class="p-6 rounded-2xl border border-dashed border-border bg-card shadow-sm">
				<div class="flex flex-col items-center text-center gap-3">
					<div class="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
						<UploadCloud class="w-6 h-6" />
					</div>
					<div class="text-sm text-foreground font-semibold">Arraste e solte seus CSVs aqui</div>
					<div class="text-xs text-muted-foreground">Formatos aceitos: sales_pipeline, accounts, products, sales_teams.</div>
					<div class="w-full max-w-sm text-left">
						<label for="import-type-select" class="text-xs text-muted-foreground">Tipo da base</label>
						<select
							id="import-type-select"
							class="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground"
							bind:value={selectedType}
						>
							{#each importTypes as type}
								<option value={type.value}>{type.label}</option>
							{/each}
						</select>
					</div>
					<label class="px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm {isBlocked ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}">
						{uploading ? 'Enviando...' : 'Selecionar arquivo'}
						<input type="file" accept=".csv" class="hidden" onchange={handleFileInput} disabled={uploading || isBlocked} />
					</label>
					{#if isBlocked}
						<div class="text-xs text-amber-700">{blockReason}</div>
					{/if}
					{#if errorMessage}
						<div class="text-xs text-red-600">{errorMessage}</div>
					{/if}
					{#if successMessage}
						<div class="text-xs text-emerald-600">{successMessage}</div>
					{/if}
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
								{@const StatusIcon = statusIcon(item.status)}
								<tr class="border-b border-border/60">
									<td class="py-3 text-foreground flex items-center gap-2">
										<FileText class="w-4 h-4 text-primary" />
										{item.name}
										<span class="text-xs text-muted-foreground">({item.size})</span>
									</td>
									<td class="py-3">
										<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-[11px] font-medium {statusBadge(item.status)}">
											<StatusIcon class="inline w-3 h-3 mr-1" />
											{statusLabel(item.status)}
										</span>
									</td>
									<td class="py-3 text-muted-foreground">{item.updated}</td>
									<td class="py-3 text-xs text-primary space-x-3">
										<button>Mapear</button>
										<button onclick={() => handleReprocess(item.id)}>Reprocessar</button>
										<button class="text-red-600" onclick={() => handleRemove(item.id)}>Remover</button>
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
