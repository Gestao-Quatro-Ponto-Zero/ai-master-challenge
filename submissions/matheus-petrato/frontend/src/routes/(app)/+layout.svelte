<script lang="ts">
	import Sidebar from '$lib/components/blocks/Sidebar.svelte';
	let { children } = $props();
</script>

<div class="flex h-screen bg-background overflow-hidden selection:bg-primary/30">
	<Sidebar />
	<main class="flex-1 flex flex-col relative overflow-hidden bg-background">
		{@render children()}
	</main>
</div>
