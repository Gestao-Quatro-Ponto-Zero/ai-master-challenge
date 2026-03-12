<script lang="ts">
	import { Send, UploadCloud, Mic, Globe } from 'lucide-svelte';
	
	let { onsubmit } = $props<{ onsubmit: (text: string) => void }>();
	let value = $state('');

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			if (value.trim()) {
				onsubmit(value);
				value = '';
			}
		}
	}

	function handleSubmit() {
		if (value.trim()) {
			onsubmit(value);
			value = '';
		}
	}
</script>

<div class="w-full max-w-3xl mx-auto flex flex-col gap-2 p-1">
	<div class="relative flex items-end w-full rounded-2xl border border-border bg-muted/30 shadow-sm focus-within:ring-1 focus-within:ring-primary/50 transition-all p-2">
		<button class="p-3 text-muted-foreground hover:text-foreground transition-colors rounded-xl shrink-0 group">
			<UploadCloud class="w-5 h-5 group-hover:scale-110 transition-transform" />
		</button>
		
		<textarea
			class="flex-1 max-h-[200px] min-h-[44px] bg-transparent border-0 focus:ring-0 resize-none px-2 py-3 text-[13px] sm:text-sm focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 placeholder:text-muted-foreground/70"
			placeholder="Pergunte sobre seus deals..."
			rows="1"
			bind:value
			onkeydown={handleKeydown}
		></textarea>

		<div class="flex items-center gap-2 p-2 shrink-0">
			<button class="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-xl">
				<Mic class="w-5 h-5" />
			</button>
			<button 
				class="p-2 rounded-xl text-primary bg-primary/10 hover:bg-primary hover:text-primary-foreground transition-all shadow-sm focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
				disabled={!value.trim()}
				onclick={handleSubmit}
			>
				<Send class="w-5 h-5" />
			</button>
		</div>
	</div>

	<!-- Ferramentas/Sources Selection (Manus inspired) -->
	<div class="flex items-center gap-2 px-1 py-1 overflow-x-auto no-scrollbar">
		<span class="text-xs text-muted-foreground flex items-center gap-1 shrink-0 px-2">
			<Globe class="w-3 h-3" /> Filtros do pipeline:
		</span>
		
		<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary text-xs text-secondary-foreground hover:bg-secondary/80 transition-colors border border-border/50 shrink-0 shadow-sm">
			<span class="w-2 h-2 rounded-full bg-primary/80"></span>
			Todos os deals
		</button>
		<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-transparent hover:bg-secondary/50 text-xs text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-border/50 shrink-0">
			<span class="w-2 h-2 rounded-full bg-amber-400"></span>
			Em risco
		</button>
		<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-transparent hover:bg-secondary/50 text-xs text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-border/50 shrink-0">
			<span class="w-2 h-2 rounded-full bg-emerald-500"></span>
			Quentes
		</button>
	</div>
</div>

<style>
	/* Hide scrollbar for Chrome, Safari and Opera */
	.no-scrollbar::-webkit-scrollbar {
		display: none;
	}
	/* Hide scrollbar for IE, Edge and Firefox */
	.no-scrollbar {
		-ms-overflow-style: none;  /* IE and Edge */
		scrollbar-width: none;  /* Firefox */
	}
</style>
