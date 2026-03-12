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
  <h1 class="text-[32px] mb-2 font-semibold tracking-tight text-foreground">Sign up</h1>
  <p class="text-muted-foreground mb-8">Comece a conversar com seus dados agora mesmo.</p>

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
      <input id="org_name" type="text" bind:value={org_name} required placeholder="Ex: Datapus Inc" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
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
      {loading ? 'Criando conta...' : 'Começar grátis'}
    </button>
  </form>

  <button class="w-full mt-3 py-2.5 rounded-lg border border-border bg-background hover:bg-secondary/40 text-[15px] font-medium transition-all shadow-sm flex items-center justify-center gap-2 active:scale-[0.98] text-foreground">
    <!-- Google Icon -->
    <svg class="h-4 w-4" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
    Criar conta com o Google
  </button>

  <p class="text-center text-sm text-muted-foreground mt-8">
    Já tem uma conta? <a href="/login" class="text-primary font-semibold hover:underline transition-colors">Faça login</a>
  </p>
</div>
