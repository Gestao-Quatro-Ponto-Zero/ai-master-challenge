<script lang="ts">
    import { api } from '$lib/services/api';
    import { Database, AlertCircle, BrainCircuit, Sparkles } from 'lucide-svelte';

    let { onComplete, onCancel } = $props<{ onComplete: () => void, onCancel: () => void }>();

    // Form states
    let name = $state('');
    let type = $state('supabase');
    let connectionUri = $state('');
    let errorMessage = $state('');

    // Onboarding Steps State
    let onboardingStep = $state(1); // 1 = Engate, 2 = Escaneamento, 3 = Curadoria
    let currentSourceId = $state('');
    
    // Scanner Result
    let scanDraft = $state<any>({ tables: {}, columns: {} });
    let scanRaw = $state<any[]>([]);

    async function handleConnect(e: Event) {
        e.preventDefault();
        onboardingStep = 2; // Switch imediato pro loader mágico
        errorMessage = '';

        try {
            // STEP 1: Conecta / Salva no Banco
            const newSource = await api.datasources.create({
                name,
                type,
                config: JSON.stringify({ connection_uri: connectionUri }),
                semantic_schema: "{}"
            });
            // O serviço api.datasources.create ja normaliza o ID/id em lowercase .id
            currentSourceId = newSource.id;

            // STEP 2: Faz o Scan da Tabela em background
            // Em dev sem banco configurado vai falhar, então usamos um mock de fallback se a requisição falhar:
            try {
                const scanData = await api.datasources.scan(currentSourceId);
                scanDraft = scanData.draft || { tables: {}, columns: {} };
                scanRaw = scanData.raw || [];
            } catch(e) {
                // Mock fallback para UX
                await new Promise(r => setTimeout(r, 2000));
                scanDraft = {
                    tables: {
                        "users": "Tabela com todos os usuários cadastrados no SaaS.",
                        "transactions": "Transações de pagamentos e assinaturas.",
                        "logs": "" // teste empty
                    }
                };
            }
            
            // Avança pro STEP 3 da Curadoria
            onboardingStep = 3;

        } catch (err: any) {
            errorMessage = err.message || 'Erro ao conectar ao banco';
            onboardingStep = 1; // Devolve p form se der pau
        }
    }

    async function handleFinishSetup() {
        try {
            // STEP 3: Salva o rascunho final (schema semântico) no banco
            // Enviamos o semantic_schema como string JSON conforme o padrão
            await api.datasources.update(currentSourceId, {
                semantic_schema: JSON.stringify(scanDraft)
            });
            onComplete();
        } catch (err: any) {
            errorMessage = "Erro ao salvar schema: " + err.message;
        }
    }

    // Função para atualizar o rascunho conforme o usuário digita
    function updateDraft(tableName: string, newValue: string) {
        if (scanDraft.tables) {
            scanDraft.tables[tableName] = newValue;
        }
    }
</script>

<div class="p-6 rounded-2xl border border-border bg-card shadow-sm animate-in fade-in slide-in-from-top-4 duration-500 overflow-hidden relative">
    
    <!-- STEP 1: O Engate -->
    {#if onboardingStep === 1}
        <div class="animate-in fade-in duration-300">
            <h2 class="text-xl font-medium tracking-tight mb-2">Onde estão os seus dados?</h2>
            <p class="text-sm text-muted-foreground mb-8">Conecte sua base de dados master para eu começar a estudar sua empresa.</p>
            
            {#if errorMessage}
                <div class="bg-destructive/10 border border-destructive/50 text-destructive text-sm p-4 rounded-xl mb-6 flex items-center gap-3">
                    <AlertCircle class="w-5 h-5" />
                    {errorMessage}
                </div>
            {/if}

            <form onsubmit={handleConnect} class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-2">
                        <label for="name" class="text-sm font-medium">Nome / Apelido da Conexão</label>
                        <input id="name" bind:value={name} required placeholder="Ex: Financeiro Principal" class="w-full px-4 py-2.5 rounded-xl border border-border bg-background focus:ring-2 focus:ring-primary/50 outline-none" />
                    </div>
                    <div class="space-y-2">
                        <label for="type" class="text-sm font-medium">Tipo de Banco</label>
                        <select id="type" bind:value={type} class="w-full px-4 py-2.5 rounded-xl border border-border bg-background focus:ring-2 focus:ring-primary/50 outline-none">
                            <option value="supabase">Supabase / Postgres</option>
                            <option value="postgres">PostgreSQL Nativo</option>
                        </select>
                    </div>
                </div>

                <div class="space-y-2">
                    <label for="uri" class="text-sm font-medium">Connection URI (DSN)</label>
                    <input id="uri" bind:value={connectionUri} required placeholder="postgresql://user:pass@host:port/db" class="w-full px-4 py-2.5 rounded-xl border border-border bg-background focus:ring-2 focus:ring-primary/50 outline-none font-mono text-sm" />
                    <p class="text-[12px] text-muted-foreground mt-1">Essa será a sua via de mão única para conversarmos de forma segura.</p>
                </div>

                <div class="flex items-center justify-end gap-3 pt-4 border-t border-border/50">
                    {#if onCancel}
                        <button type="button" onclick={onCancel} class="px-6 py-2.5 bg-transparent text-foreground rounded-xl font-medium hover:bg-secondary/50 transition-all">
                            Cancelar
                        </button>
                    {/if}
                    <button type="submit" class="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl font-medium shadow-sm hover:opacity-90 transition-all">
                        Conectar Base
                    </button>
                </div>
            </form>
        </div>
    
    <!-- STEP 2: O Escaneamento -->
    {:else if onboardingStep === 2}
        <div class="flex flex-col items-center justify-center p-12 text-center animate-in zoom-in-95 duration-500">
            <div class="relative w-20 h-20 mb-6 flex items-center justify-center">
                <div class="absolute inset-0 bg-primary/20 rounded-full animate-ping"></div>
                <BrainCircuit class="w-10 h-10 text-primary animate-pulse relative z-10" />
            </div>
            <h3 class="text-xl font-medium mb-3 text-foreground">Iniciando tentáculos...</h3>
            <p class="text-sm text-primary font-mono tracking-tight animate-pulse bg-primary/10 px-4 py-1.5 rounded-full inline-block">
                Lendo tabelas... Pedindo pro Mercury analisar contextos...
            </p>
        </div>

    <!-- STEP 3: A Curadoria -->
    {:else if onboardingStep === 3}
        <div class="animate-in fade-in slide-in-from-right-8 duration-500">
            <div class="flex items-center gap-3 mb-2">
                <Sparkles class="w-6 h-6 text-primary" />
                <h2 class="text-xl font-medium tracking-tight">Ajude a treinar o Polvo</h2>
            </div>
            <p class="text-sm text-muted-foreground mb-8">Nossa inteligência gerou um rascunho de contexto para o seu banco. Sinta-se à vontade para ajustar.</p>

            {#if errorMessage}
                <div class="text-destructive text-xs mb-4">{errorMessage}</div>
            {/if}

            <div class="space-y-4 max-h-[50vh] overflow-y-auto pr-2 custom-scrollbar">
                {#each Object.entries(scanDraft.tables || {}) as [tableName, desc]}
                    <div class="p-4 border border-border rounded-xl bg-background/50 hover:border-primary/30 transition-colors">
                        <h4 class="font-mono text-sm font-bold text-primary mb-3 flex items-center gap-3">
                            <Database class="w-4 h-4" /> {tableName}
                        </h4>
                        <input 
                            type="text" 
                            value={desc} 
                            oninput={(e) => updateDraft(tableName, e.currentTarget.value)}
                            placeholder="Explique brevemente o que essa tabela armazena..." 
                            class="w-full bg-secondary/30 border border-border/50 text-sm p-3 rounded-lg focus:ring-1 focus:ring-primary/50 outline-none transition-all text-foreground" 
                        />
                    </div>
                {/each}
                
                {#if Object.keys(scanDraft.tables || {}).length === 0}
                    <div class="p-8 border-2 border-dashed border-border/50 rounded-xl bg-background/30 flex flex-col items-center justify-center text-center">
                        <p class="text-sm font-medium text-foreground mb-1">Nenhum rascunho detalhado pronto.</p>
                        <p class="text-xs text-muted-foreground">Sem problemas, eu irei aprender a estrutura das tabelas conforme você conversa comigo no chat.</p>
                    </div>
                {/if}
            </div>

            <div class="mt-8 pt-6 border-t border-border/50 flex justify-end">
                <button onclick={handleFinishSetup} class="px-8 py-2.5 bg-primary text-primary-foreground font-medium rounded-xl hover:bg-primary/90 transition-all shadow-sm shadow-primary/20">
                    Concluir Onboarding
                </button>
            </div>
        </div>
    {/if}
</div>
