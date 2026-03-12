<script lang="ts">
  import { api, setStoredToken, setStoredUser } from '$lib/services/api';

  let email = $state('');
  let password = $state('');
  let loading = $state(false);
  let errorMessage = $state('');

  async function handleLogin(e: Event) {
    e.preventDefault();
    loading = true;
    errorMessage = '';

    try {
      const data = await api.auth.login({ email, password });
      setStoredToken(data.token);
      setStoredUser(data.user);
      
      // Redirect to main app chat
      window.location.href = '/';
      
    } catch (err: any) {
      errorMessage = err.message || 'Erro ao conectar no servidor.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
  <h1 class="text-[32px] mb-2 font-semibold tracking-tight text-foreground">Log in</h1>
  <p class="text-muted-foreground mb-8">Acesse com as credenciais enviadas por email.</p>

  {#if errorMessage}
    <div class="bg-red-500/10 border border-red-500/50 text-red-600 text-sm p-3 rounded-lg mb-4">
      {errorMessage}
    </div>
  {/if}

  <form class="flex flex-col gap-4" onsubmit={handleLogin}>
    <!-- Email -->
    <div class="space-y-1.5 flex flex-col">
      <label for="email" class="text-[14px] font-medium text-foreground">Email</label>
      <input id="email" type="email" bind:value={email} required placeholder="nome@empresa.com" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
    </div>

    <!-- Password -->
    <div class="space-y-1.5 flex flex-col">
      <label for="password" class="text-[14px] font-medium text-foreground">Senha</label>
      <input id="password" type="password" bind:value={password} required placeholder="••••••••" class="w-full px-3 py-2.5 rounded-lg border border-border bg-background shadow-sm hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm placeholder:text-muted-foreground/60" />
    </div>

    <!-- Options -->
    <div class="flex items-center justify-between mt-1 mb-2">
      <div class="flex items-center gap-2">
        <input type="checkbox" id="remember" class="rounded-[4px] border border-border text-primary focus:ring-1 focus:ring-primary/50 w-4 h-4 cursor-pointer accent-primary" />
        <label for="remember" class="text-sm text-foreground font-medium cursor-pointer">Lembrar por 30 dias</label>
      </div>
      <button type="button" class="text-sm font-semibold text-primary hover:text-primary/80 transition-colors">
        Esqueceu a senha?
      </button>
    </div>

    <button type="submit" disabled={loading} class="w-full py-2.5 rounded-lg bg-primary hover:bg-opacity-90 active:scale-[0.98] text-primary-foreground text-[15px] font-medium transition-all shadow-sm shadow-primary/30 mt-2 disabled:opacity-70 disabled:cursor-not-allowed">
      {loading ? 'Entrando...' : 'Entrar'}
    </button>
  </form>

  <p class="text-center text-sm text-muted-foreground mt-8">
    Precisa de acesso? <a href="mailto:help@g4compass.com" class="text-primary font-semibold hover:underline transition-colors">Fale com seu gestor</a>
  </p>
</div>
