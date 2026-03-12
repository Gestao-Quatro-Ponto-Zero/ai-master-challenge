<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	// Redireciona para pipeline com modal de deal (o detalhe agora é modal na pipeline)
	$effect(() => {
		const id = page.url.searchParams.get('id');
		const target = id ? `/pipeline?deal=${encodeURIComponent(id)}` : '/pipeline';
		goto(target, { replaceState: true });
	});
</script>

<div class="flex-1 flex flex-col items-center justify-center min-h-[50vh] text-muted-foreground">
	<p>Redirecionando para o pipeline...</p>
</div>
