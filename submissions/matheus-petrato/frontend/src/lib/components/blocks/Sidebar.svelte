<script lang="ts">
	import { Database, LayoutDashboard, Settings, MessageSquare, Plus } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { api, type DataSource } from '$lib/services/api';

	let sources = $state<DataSource[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			sources = await api.datasources.list();
		} catch (err) {
			console.error("Erro ao carregar fontes:", err);
		} finally {
			loading = false;
		}
	});
</script>

<aside class="w-64 border-r border-border/50 bg-background/50 h-screen flex flex-col backdrop-blur-md">
	<div class="h-16 flex items-center px-6 border-b border-border/50 gap-3">
		<div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-sm shadow-primary/30">
			<!-- Temporary SVG resembling an Octopus/Database until logo.png is loaded -->
			<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4a4 4 0 0 1 4 4c0 1.5-.7 2.8-1.7 3.6l1.3 2.1a1 1 0 0 1-.4 1.3l-2.1 1.3a1 1 0 0 1-1.4-.4L11 14.8V19a1 1 0 0 1-2 0v-4.2l-.7 1.1a1 1 0 0 1-1.4.4l-2.1-1.3a1 1 0 0 1-.4-1.3l1.3-2.1C4.7 10.8 4 9.5 4 8a4 4 0 0 1 4-4"/></svg>
		</div>
		<span class="font-bold tracking-wide text-lg text-foreground">Datapus</span>
	</div>

	<div class="flex-1 overflow-y-auto p-4 space-y-6">
		<!-- Menu Principal -->
		<div class="space-y-1">
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary font-medium transition-colors">
				<MessageSquare class="w-4 h-4" />
				Novo Chat
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors">
				<LayoutDashboard class="w-4 h-4" />
				Dashboard
			</button>
		</div>

		<!-- Data Sources -->
		<div>
			<div class="flex items-center justify-between px-3 mb-2">
				<span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Fontes de Dados</span>
				<a href="/settings/sources" class="text-muted-foreground hover:text-primary transition-colors">
					<Plus class="w-4 h-4" />
				</a>
			</div>
			<div class="space-y-1">
				{#if loading}
					<div class="px-3 py-2 space-y-3">
						<div class="h-4 bg-secondary animate-pulse rounded w-3/4"></div>
						<div class="h-4 bg-secondary animate-pulse rounded w-1/2"></div>
					</div>
				{:else if sources.length === 0}
					<p class="px-3 py-2 text-xs text-muted-foreground italic">Nenhuma fonte conectada</p>
				{:else}
					{#each sources as source}
						<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all group {source.is_active ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'}">
							<Database class="w-4 h-4 {source.is_active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}" />
							<span class="truncate">{source.name}</span>
							{#if source.is_active}
								<div class="w-1.5 h-1.5 rounded-full bg-primary ml-auto shadow-[0_0_8px_oklch(0.929_0.013_255.508)] opacity-80"></div>
							{/if}
						</button>
					{/each}
				{/if}
			</div>
		</div>
	</div>

	<div class="p-4 border-t border-border/50">
		<a href="/settings/sources" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors">
			<Settings class="w-4 h-4" />
			Configurações
		</a>
	</div>
</aside>
