<script lang="ts">
	import { Mail, Star } from 'lucide-svelte';
	let { children } = $props();
</script>

<div class="min-h-screen w-full grid grid-cols-1 lg:grid-cols-2 bg-background">
	<!-- Esquerda: Forms & Conteúdo -->
	<div class="flex flex-col relative bg-background">
		<!-- Header / Logo -->
		<header class="absolute top-8 left-8 flex items-center gap-2 z-10">
			<div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-sm shadow-primary/30">
				<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4a4 4 0 0 1 4 4c0 1.5-.7 2.8-1.7 3.6l1.3 2.1a1 1 0 0 1-.4 1.3l-2.1 1.3a1 1 0 0 1-1.4-.4L11 14.8V19a1 1 0 0 1-2 0v-4.2l-.7 1.1a1 1 0 0 1-1.4.4l-2.1-1.3a1 1 0 0 1-.4-1.3l1.3-2.1C4.7 10.8 4 9.5 4 8a4 4 0 0 1 4-4"/></svg>
			</div>
			<span class="font-bold tracking-wide text-lg text-foreground">Datapus</span>
		</header>

		<!-- Content -->
		<main class="flex-1 flex flex-col justify-center px-8 sm:px-12 lg:px-24">
			<div class="w-full max-w-[400px] mx-auto">
				{@render children()}
			</div>
		</main>

		<!-- Footer -->
		<footer class="absolute bottom-8 left-8 right-8 flex justify-between items-center text-xs text-muted-foreground/80 pointer-events-none">
			<span>© Datapus 2026</span>
			<a href="mailto:help@datapus.com" class="flex items-center gap-1.5 hover:text-foreground pointer-events-auto transition-colors">
				<Mail class="w-4 h-4" /> help@datapus.com
			</a>
		</footer>
	</div>

	<!-- Direita: Testimonial Minimalista -->
	<div class="hidden lg:flex flex-col relative overflow-hidden p-12 justify-center items-center bg-[#F9FAFB]">
		
		<div class="max-w-xl w-full flex flex-col items-center text-center relative z-10">
			<!-- Stars -->
			<div class="flex text-amber-400 mb-8 gap-1">
				<Star class="w-6 h-6 fill-current" />
				<Star class="w-6 h-6 fill-current" />
				<Star class="w-6 h-6 fill-current" />
				<Star class="w-6 h-6 fill-current" />
				<Star class="w-6 h-6 fill-current" />
			</div>

			<!-- Quote -->
			<h2 class="text-[34px] font-medium leading-[1.3] text-[#111827] mb-12">
				Datapus tem nos poupado milhares de horas de trabalho de dados. Nós conseguimos subir projetos e extrair análises muito mais rápido.
			</h2>
			
			<!-- Avatar & Info -->
			<div class="flex flex-col items-center justify-center">
				<div class="w-16 h-16 rounded-full overflow-hidden mb-4 border-2 border-white shadow-sm ring-1 ring-border/10 relative">
					<img src="/avatar.png" alt="Lori Bryson" class="w-full h-full object-cover" />
					<div class="absolute bottom-0 right-0 w-5 h-5 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center text-white">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/></svg>
					</div>
				</div>
				<div class="font-semibold text-base text-[#111827]">Lori Bryson</div>
				<div class="text-sm text-muted-foreground mt-0.5">Product Designer, Sisyphus</div>
			</div>

			<!-- Carousel Dots -->
			<div class="flex items-center gap-2 mt-16">
				<svg class="w-4 h-4 text-muted-foreground/30 hover:text-muted-foreground cursor-pointer mr-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
				<div class="w-2.5 h-2.5 rounded-full bg-primary cursor-pointer"></div>
				<div class="w-2.5 h-2.5 rounded-full bg-muted-foreground/20 hover:bg-muted-foreground/40 cursor-pointer"></div>
				<div class="w-2.5 h-2.5 rounded-full bg-muted-foreground/20 hover:bg-muted-foreground/40 cursor-pointer"></div>
				<div class="w-2.5 h-2.5 rounded-full bg-muted-foreground/20 hover:bg-muted-foreground/40 cursor-pointer"></div>
				<svg class="w-4 h-4 text-muted-foreground/30 hover:text-muted-foreground cursor-pointer ml-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
			</div>
		</div>

	</div>
</div>
