<script lang="ts">
	import { page } from '$app/state';
	import { role } from '$lib/stores/role';
	import Sidebar from '$lib/components/blocks/Sidebar.svelte';
	import { LayoutDashboard, MessageSquare, Sparkles, Bell, Database, UploadCloud, Settings } from 'lucide-svelte';
	let { children } = $props();

	const currentPath = $derived(page.url.pathname);
	const isActive = (path: string) => {
		if (path === '/') return currentPath === '/';
		return currentPath === path || currentPath.startsWith(`${path}/`);
	};
</script>

<div class="flex min-h-screen bg-background overflow-hidden selection:bg-primary/30">
	<Sidebar />
	<main class="flex-1 flex flex-col relative overflow-hidden bg-background pb-20 md:pb-0">
		{@render children()}
	</main>

	<!-- Mobile bottom navigation -->
	<nav class="md:hidden fixed bottom-0 left-0 right-0 bg-[#0C1923] border-t border-[#1F2A37] text-white">
		<div class="flex items-center gap-3 px-3 py-2 overflow-x-auto no-scrollbar">
			<a href="/briefing" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/briefing') ? 'text-primary' : 'text-white/70'}">
				<LayoutDashboard class="w-4 h-4 mb-1" />
				Briefing
			</a>
			<a href="/pipeline" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/pipeline') ? 'text-primary' : 'text-white/70'}">
				<MessageSquare class="w-4 h-4 mb-1" />
				Pipeline
			</a>
			<a href="/" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/') ? 'text-primary' : 'text-white/70'}">
				<Sparkles class="w-4 h-4 mb-1" />
				Compass
			</a>
			<a href="/alerts" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/alerts') ? 'text-primary' : 'text-white/70'}">
				<Bell class="w-4 h-4 mb-1" />
				Alertas
			</a>
			{#if $role === 'manager'}
				<a href="/reports" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/reports') ? 'text-primary' : 'text-white/70'}">
					<Database class="w-4 h-4 mb-1" />
					Relatorios
				</a>
				<a href="/imports" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/imports') ? 'text-primary' : 'text-white/70'}">
					<UploadCloud class="w-4 h-4 mb-1" />
					Bases
				</a>
			{/if}
			<a href="/settings" class="flex flex-col items-center justify-center min-w-[64px] text-xs {isActive('/settings') ? 'text-primary' : 'text-white/70'}">
				<Settings class="w-4 h-4 mb-1" />
				Config
			</a>
		</div>
	</nav>
</div>

<style>
	.no-scrollbar::-webkit-scrollbar {
		display: none;
	}
	.no-scrollbar {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}
</style>
