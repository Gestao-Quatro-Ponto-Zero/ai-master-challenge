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

<aside class="w-64 border-r border-sidebar-border bg-sidebar text-sidebar-foreground h-screen flex flex-col">
	<div class="h-16 flex items-center px-6 border-b border-sidebar-border">
		<img src="/logo-full.svg" alt="G4 Compass" class="h-7 w-auto" />
	</div>

	<div class="flex-1 overflow-y-auto p-4 space-y-6">
		<!-- Menu Principal -->
		<div class="space-y-1">
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-sidebar-accent text-sidebar-foreground font-medium transition-colors border border-sidebar-border">
				<MessageSquare class="w-4 h-4 text-primary" />
				Compass
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground transition-colors">
				<LayoutDashboard class="w-4 h-4" />
				Pipeline
			</button>
		</div>

		<!-- Data Sources -->
		<div>
			<div class="flex items-center justify-between px-3 mb-2">
				<span class="text-xs font-semibold text-sidebar-foreground/60 uppercase tracking-wider">Fontes de Dados</span>
				<a href="/settings/sources" class="text-sidebar-foreground/60 hover:text-primary transition-colors">
					<Plus class="w-4 h-4" />
				</a>
			</div>
			<div class="space-y-1">
				{#if loading}
					<div class="px-3 py-2 space-y-3">
						<div class="h-4 bg-sidebar-accent animate-pulse rounded w-3/4"></div>
						<div class="h-4 bg-sidebar-accent animate-pulse rounded w-1/2"></div>
					</div>
				{:else if sources.length === 0}
					<p class="px-3 py-2 text-xs text-sidebar-foreground/60 italic">Nenhuma fonte conectada</p>
				{:else}
					{#each sources as source}
						<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all group {source.is_active ? 'bg-sidebar-accent text-sidebar-foreground' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground'}">
							<Database class="w-4 h-4 {source.is_active ? 'text-primary' : 'text-sidebar-foreground/60 group-hover:text-sidebar-foreground'}" />
							<span class="truncate">{source.name}</span>
							{#if source.is_active}
								<div class="w-1.5 h-1.5 rounded-full bg-primary ml-auto shadow-[0_0_8px_rgba(196,149,42,0.6)] opacity-80"></div>
							{/if}
						</button>
					{/each}
				{/if}
			</div>
		</div>
	</div>

	<div class="p-4 border-t border-sidebar-border">
		<a href="/settings/sources" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground transition-colors">
			<Settings class="w-4 h-4" />
			Configurações
		</a>
	</div>
</aside>
