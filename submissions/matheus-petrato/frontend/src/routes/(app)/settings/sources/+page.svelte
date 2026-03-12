<script lang="ts">
    import { api } from '$lib/services/api';
    import { Database, Plus, CheckCircle2, Trash2 } from 'lucide-svelte';
    import { onMount } from 'svelte';
    import Onboarding from '$lib/components/blocks/Onboarding.svelte';

    let sources = $state<any[]>([]);
    let loading = $state(true);
    let showForm = $state(false);

    async function fetchSources() {
        loading = true;
        try {
            sources = await api.datasources.list();
        } catch (err) {
            console.error(err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchSources);

    async function handleFinishSetup() {
        showForm = false;
        await fetchSources();
    }
</script>

<div class="flex-1 p-8 max-w-5xl mx-auto w-full">
    <div class="flex items-center justify-between mb-10">
        <div>
            <h1 class="text-3xl font-bold tracking-tight text-foreground">Fontes de Dados</h1>
            <p class="text-muted-foreground mt-2">Conecte seus bancos para começar a conversar com os dados.</p>
        </div>
        <button 
            onclick={() => showForm = !showForm}
            class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium shadow-sm hover:bg-primary/90 transition-all"
        >
            <Plus class="w-4 h-4" />
            Nova Conexão
        </button>
    </div>

    {#if showForm}
        <div class="mb-10 max-w-3xl">
            <Onboarding onComplete={handleFinishSetup} onCancel={() => showForm = false} />
        </div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#if loading}
            {#each Array(4) as _}
                <div class="p-6 rounded-2xl border border-border bg-card/50 animate-pulse h-32"></div>
            {/each}
        {:else if sources.length === 0}
            <div class="col-span-full py-20 flex flex-col items-center justify-center border-2 border-dashed border-border rounded-3xl">
                <Database class="w-12 h-12 text-muted-foreground/30 mb-4" />
                <p class="text-muted-foreground text-center">Nenhuma fonte configurada.<br/>Adicione sua primeira conexão para habilitar o chat.</p>
            </div>
        {:else}
            {#each sources as source}
                <div class="p-6 rounded-2xl border border-border bg-card hover:border-primary/50 transition-all group">
                    <div class="flex items-start justify-between mb-4">
                        <div class="p-3 rounded-xl bg-primary/10 text-primary">
                            <Database class="w-6 h-6" />
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-1 rounded-md bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                                <CheckCircle2 class="w-3 h-3" /> Conectado
                            </span>
                            <button class="p-2 text-muted-foreground hover:text-destructive transition-colors">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <div>
                        <h3 class="font-bold text-lg">{source.name}</h3>
                        <p class="text-sm text-muted-foreground capitalize">{source.type}</p>
                    </div>
                </div>
            {/each}
        {/if}
    </div>
</div>
