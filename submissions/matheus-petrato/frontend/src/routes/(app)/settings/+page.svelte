<script lang="ts">
	import { Shield, Users } from 'lucide-svelte';
	import { role } from '$lib/stores/role';
</script>

<div class="flex-1 flex flex-col h-full bg-background text-foreground">
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>Configuracoes</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	<div class="flex-1 overflow-y-auto px-6 pb-10 pt-8">
		<div class="max-w-4xl mx-auto space-y-8">
			<div class="flex flex-col gap-2">
				<h1 class="text-3xl font-bold tracking-tight text-foreground">Perfil e permissao</h1>
				<p class="text-muted-foreground">Defina se este usuario atua como vendedor ou manager.</p>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<button
					class="p-5 rounded-2xl border transition-all text-left { $role === 'seller' ? 'border-primary bg-primary/10' : 'border-border bg-card hover:border-primary/50' }"
					onclick={() => role.set('seller')}
				>
					<div class="flex items-center gap-3 mb-3">
						<div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
							<Users class="w-5 h-5" />
						</div>
						<div>
							<div class="text-lg font-semibold text-foreground">Vendedor</div>
							<div class="text-xs text-muted-foreground">Visao individual e foco em deals</div>
						</div>
					</div>
					<ul class="text-sm text-muted-foreground space-y-2">
						<li>Briefing pessoal e alertas de oportunidades</li>
						<li>Pipeline priorizado com sugestoes de acao</li>
						<li>Explainability do score por deal</li>
					</ul>
				</button>

				<button
					class="p-5 rounded-2xl border transition-all text-left { $role === 'manager' ? 'border-primary bg-primary/10' : 'border-border bg-card hover:border-primary/50' }"
					onclick={() => role.set('manager')}
				>
					<div class="flex items-center gap-3 mb-3">
						<div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
							<Shield class="w-5 h-5" />
						</div>
						<div>
							<div class="text-lg font-semibold text-foreground">Manager</div>
							<div class="text-xs text-muted-foreground">Visao macro do time e performance</div>
						</div>
					</div>
					<ul class="text-sm text-muted-foreground space-y-2">
						<li>Relatorios por regiao, stage e vendedor</li>
						<li>Filtros globais e consolidacao do pipeline</li>
						<li>Acesso a deals criticos do time</li>
					</ul>
				</button>
			</div>

			<div class="p-4 rounded-2xl border border-border bg-card text-sm text-muted-foreground">
				As permissoes sao aplicadas localmente para prototipo. Integraremos isso ao JWT quando o backend estiver pronto.
			</div>
		</div>
	</div>
</div>
