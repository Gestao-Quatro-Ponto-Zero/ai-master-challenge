<script lang="ts">
  import { api, setStoredToken, setStoredUser } from '$lib/services/api';

  let name = $state('');
  let org_name = $state('');
  let email = $state('');
  let password = $state('');
  let loading = $state(false);
  let errorMessage = $state('');

  async function handleRegister(e: Event) {
    e.preventDefault();
    loading = true;
    errorMessage = '';

    try {
      const data = await api.auth.register({ name, org_name, email, password });
      setStoredToken(data.token);
      setStoredUser(data.user);
      
      // Redirect to main app
      window.location.href = '/';
      
    } catch (err: any) {
      errorMessage = err.message || 'Erro ao conectar no servidor.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
  <h1 class="text-[32px] mb-2 font-semibold tracking-tight text-foreground">Criar conta</h1>
  <p class="text-muted-foreground mb-8">Use o convite interno enviado por email para habilitar seu acesso.</p>

  {#if errorMessage}
    <div class="bg-red-500/10 border border-red-500/50 text-red-600 text-sm p-3 rounded-lg mb-4">
      {errorMessage}
    </div>
  {/if}

  <form class="flex flex-col gap-4" onsubmit={handleRegister}>
    <!-- Name -->
    <div class="space-y-1.5 flex flex-col">
      <label for="name" class="text-[14px] font-medium text-foreground">Nome Completo</label>
      <input id="name" type="text" bind:value={name} required placeholder="Seu nome" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
    </div>

    <!-- Organization Name -->
    <div class="space-y-1.5 flex flex-col">
      <label for="org_name" class="text-[14px] font-medium text-foreground">Nome da Empresa</label>
      <input id="org_name" type="text" bind:value={org_name} required placeholder="Ex: G4 Compass" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
    </div>

    <!-- Email -->
    <div class="space-y-1.5 flex flex-col">
      <label for="email" class="text-[14px] font-medium text-foreground">Email Corporativo</label>
      <input id="email" type="email" bind:value={email} required placeholder="nome@empresa.com" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
    </div>

    <!-- Password -->
    <div class="space-y-1.5 flex flex-col">
      <label for="password" class="text-[14px] font-medium text-foreground">Senha</label>
      <input id="password" type="password" bind:value={password} required placeholder="Crie uma senha forte" minlength="8" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
      <p class="text-[13px] text-muted-foreground/80 mt-1">Deve conter pelomenos 8 caracteres.</p>
    </div>

    <button type="submit" disabled={loading} class="w-full py-2.5 rounded-lg bg-primary hover:bg-opacity-90 active:scale-[0.98] text-primary-foreground text-[15px] font-medium transition-all shadow-sm shadow-primary/30 mt-2 disabled:opacity-70 disabled:cursor-not-allowed">
      {loading ? 'Criando conta...' : 'Criar conta'}
    </button>
  </form>

  <p class="text-center text-sm text-muted-foreground mt-8">
    Já tem acesso? <a href="/login" class="text-primary font-semibold hover:underline transition-colors">Faça login</a>
  </p>
</div>
