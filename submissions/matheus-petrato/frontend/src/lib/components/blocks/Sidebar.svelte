<script lang="ts">
	import { LayoutDashboard, Settings, MessageSquare, Bell, FileText, Sparkles, Database } from 'lucide-svelte';

	const isManager = true;
	const activeRoute = 'home';
	const regions = ['Central', 'East', 'West'];
	let selectedRegion = $state('Central');
	const managers = ['Amanda Rocha', 'Bianca Lima', 'Diego Souza'];
	let selectedManager = $state('Amanda Rocha');
	const sellers = ['Camila Torres', 'Felipe Costa', 'Rafael Dias'];
	let selectedSeller = $state('Camila Torres');


</script>

<aside class="w-72 border-r border-sidebar-border bg-sidebar text-sidebar-foreground h-screen flex flex-col">
	<div class="h-16 flex items-center px-6 border-b border-sidebar-border">
		<img src="/logo-full.svg" alt="G4 Compass" class="h-7 w-auto" />
	</div>

	<div class="flex-1 overflow-y-auto p-4 space-y-6">
		<!-- Menu Principal -->
		<div class="space-y-1">
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'home' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<LayoutDashboard class="w-4 h-4 {activeRoute === 'home' ? 'text-primary' : ''}" />
				Briefing
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'pipeline' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<MessageSquare class="w-4 h-4 {activeRoute === 'pipeline' ? 'text-primary' : ''}" />
				Pipeline
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'deal' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<FileText class="w-4 h-4 {activeRoute === 'deal' ? 'text-primary' : ''}" />
				Deal Detail
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'compass' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<Sparkles class="w-4 h-4 {activeRoute === 'compass' ? 'text-primary' : ''}" />
				Compass
			</button>
			<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'alerts' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<Bell class="w-4 h-4 {activeRoute === 'alerts' ? 'text-primary' : ''}" />
				Alertas
			</button>
			{#if isManager}
				<button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {activeRoute === 'reports' ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
					<Database class="w-4 h-4 {activeRoute === 'reports' ? 'text-primary' : ''}" />
					Relatorios
				</button>
			{/if}
		</div>

		<!-- Filtros Globais -->
		<div class="space-y-3">
			<span class="text-xs font-semibold text-sidebar-foreground/60 uppercase tracking-wider px-3">Filtros</span>
			<div class="space-y-2 px-3">
				<div class="space-y-1">
					<label class="text-[11px] uppercase tracking-wider text-sidebar-foreground/60">Regiao</label>
					<select bind:value={selectedRegion} class="w-full rounded-lg bg-sidebar-accent/70 border border-sidebar-border px-3 py-2 text-sm text-sidebar-foreground focus:outline-none focus:ring-2 focus:ring-primary/40">
						{#each regions as region}
							<option value={region}>{region}</option>
						{/each}
					</select>
				</div>
				{#if isManager}
					<div class="space-y-1">
						<label class="text-[11px] uppercase tracking-wider text-sidebar-foreground/60">Manager</label>
						<select bind:value={selectedManager} class="w-full rounded-lg bg-sidebar-accent/70 border border-sidebar-border px-3 py-2 text-sm text-sidebar-foreground focus:outline-none focus:ring-2 focus:ring-primary/40">
							{#each managers as manager}
								<option value={manager}>{manager}</option>
							{/each}
						</select>
					</div>
				{/if}
				<div class="space-y-1">
					<label class="text-[11px] uppercase tracking-wider text-sidebar-foreground/60">Vendedor</label>
					<select bind:value={selectedSeller} class="w-full rounded-lg bg-sidebar-accent/70 border border-sidebar-border px-3 py-2 text-sm text-sidebar-foreground focus:outline-none focus:ring-2 focus:ring-primary/40">
						{#each sellers as seller}
							<option value={seller}>{seller}</option>
						{/each}
					</select>
				</div>
			</div>
		</div>


	</div>

	<div class="p-4 border-t border-sidebar-border">
		<a href="/settings" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground transition-colors">
			<Settings class="w-4 h-4" />
			Configurações
		</a>
	</div>
</aside>
