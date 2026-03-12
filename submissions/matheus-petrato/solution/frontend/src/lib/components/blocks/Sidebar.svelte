<script lang="ts">
	import { page } from '$app/state';
	import { role } from '$lib/stores/role';
	import { LayoutDashboard, MessageSquare, Bell, FileText, Sparkles, Database, UploadCloud } from 'lucide-svelte';

	const currentPath = $derived(page.url.pathname);
	const isActive = (path: string) => {
		if (path === '/') return currentPath === '/';
		return currentPath === path || currentPath.startsWith(`${path}/`);
	};
</script>

<aside class="w-72 border-r border-sidebar-border bg-sidebar text-sidebar-foreground h-screen flex-col hidden md:flex">
	<div class="h-16 flex items-center px-6 border-b border-sidebar-border">
		<img src="/logo-full.svg" alt="G4 Compass" class="h-7 w-auto" />
	</div>

	<div class="flex-1 overflow-y-auto p-4 space-y-6">
		<!-- Menu Principal -->
		<div class="space-y-1">
			<a href="/briefing" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/briefing') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<LayoutDashboard class="w-4 h-4 {isActive('/briefing') ? 'text-primary' : ''}" />
				Briefing
			</a>
			<a href="/pipeline" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/pipeline') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<MessageSquare class="w-4 h-4 {isActive('/pipeline') ? 'text-primary' : ''}" />
				Pipeline
			</a>
			<a href="/" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<Sparkles class="w-4 h-4 {isActive('/') ? 'text-primary' : ''}" />
				Compass
			</a>
			<a href="/alerts" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/alerts') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
				<Bell class="w-4 h-4 {isActive('/alerts') ? 'text-primary' : ''}" />
				Alertas
			</a>
			{#if $role === 'manager'}
				<a href="/reports" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/reports') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
					<Database class="w-4 h-4 {isActive('/reports') ? 'text-primary' : ''}" />
					Relatorios
				</a>
				<a href="/imports" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors border {isActive('/imports') ? 'bg-sidebar-accent text-sidebar-foreground border-sidebar-border' : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground border-transparent'}">
					<UploadCloud class="w-4 h-4 {isActive('/imports') ? 'text-primary' : ''}" />
					Bases (CSV)
				</a>
			{/if}
		</div>

	</div>

	<div class="p-4 border-t border-sidebar-border">
		<div class="text-xs text-sidebar-foreground/60 px-3">G4 Compass</div>
	</div>
</aside>
