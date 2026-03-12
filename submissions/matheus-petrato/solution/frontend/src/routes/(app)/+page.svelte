<script lang="ts">
	import ChatInput from '$lib/components/blocks/ChatInput.svelte';
import Markdown from '$lib/components/blocks/Markdown.svelte';
	import { role } from '$lib/stores/role';
	import { Sparkles, Activity, TrendingUp, Target, BrainCircuit, Users } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { api, getStoredToken, getStoredUser } from '$lib/services/api';

	interface Suggestion {
		icon: any; 
		label: string;
		prompt: string;
	}

	const sellerSuggestions: Suggestion[] = [
		{ icon: TrendingUp, label: 'Deals quentes', prompt: 'Quais sao meus deals mais quentes agora?' },
		{ icon: Activity, label: 'Deals em risco', prompt: 'Quais deals estao em risco e o que fazer agora?' },
		{ icon: Target, label: 'Priorizar semana', prompt: 'Me ajuda a priorizar minha semana de vendas.' },
		{ icon: Sparkles, label: 'Resumo do mes', prompt: 'Me traga um resumo do meu mes.' },
	];

	const managerSuggestions: Suggestion[] = [
		{ icon: Users, label: 'Top vendedores', prompt: 'Quem sao os top vendedores do time e por que?' },
		{ icon: Activity, label: 'Risco do time', prompt: 'Quais deals do time estao em risco e como agir?' },
		{ icon: Target, label: 'Foco da semana', prompt: 'Qual deve ser o foco do time nesta semana?' },
		{ icon: Sparkles, label: 'Resumo executivo', prompt: 'Crie um resumo executivo do pipeline para hoje.' },
	];

	const suggestions = $derived($role === 'manager' ? managerSuggestions : sellerSuggestions);
	const greeting = $derived(
		$role === 'manager' ? 'Pronto para priorizar o time hoje?' : 'Pronto para priorizar seus deals hoje?'
	);

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		isStreaming?: boolean;
	}

	let messages = $state<Message[]>([]);
	let ws = $state<WebSocket | null>(null);
	let isConnecting = $state(false);
	let loadingPage = $state(true);

	// Thinking Effect Logic
	const thinkingPhrases = [
		"Analisando seu pipeline...",
		"Calculando score dos deals...",
		"Checando oportunidades em risco...",
		"Comparando com historico do time...",
		"Montando seu briefing diario...",
		"Priorizando os proximos passos..."
	];
	let thinkingPhrase = $state(thinkingPhrases[0]);

	onMount(async () => {
		// Intervalo para rotacionar as frases
		const phraseInterval = setInterval(() => {
			thinkingPhrase = thinkingPhrases[Math.floor(Math.random() * thinkingPhrases.length)];
		}, 3000);

		const token = getStoredToken();
		
		// 1. Fetch History (no onboarding required for now)
		try {
			const history = await api.chat.history().catch(() => []);
			messages = history.map((m: any) => ({
				id: m.id,
				role: m.role,
				content: m.content,
				isStreaming: false
			}));
		} catch (err) {
			console.warn("Erro no startup da página:", err);
		} finally {
			loadingPage = false;
		}

		// 2. Open WebSocket
		try {
			// Passando o token via query param para o Upgrade do Handshake
			const wsUrl = `ws://localhost:8080/ws/chat${token ? '?token=' + token : ''}`;
			ws = new WebSocket(wsUrl);
			
			ws.onopen = () => {
				console.log('WS Connectado');
			};

			ws.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					// Payload esperado: { channel: "web", content: "...", stream_state: "chunk"|"done" }
					
					// Update last message Se for do assistente
					if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
						if (data.stream_state === 'chunk') {
							messages[messages.length - 1].content += data.content;
						} else if (data.stream_state === 'done') {
							messages[messages.length - 1].isStreaming = false;
						}
					}
				} catch (e) {
					console.error("Failed to parse WS message", e);
				}
			};

			ws.onclose = () => {
				console.log('WS Disconnectado');
			};
		} catch(err) {
			console.error("WS error:", err);
		}

		return () => {
			if (ws) ws.close();
			clearInterval(phraseInterval);
		};
	});

	async function sendMessage(text: string) {
		const msgId = crypto.randomUUID();
		messages = [...messages, { id: msgId, role: 'user', content: text }];

		// Adiciona a bolha da AI Vazia e Streaming
		const aiMsgId = crypto.randomUUID();
		messages = [...messages, { id: aiMsgId, role: 'assistant', content: '', isStreaming: true }];

		const user = getStoredUser();
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify({
				content: text,
				session_id: user?.id || 'unknown',
				type: 'text'
			}));
		} else {
			// Mock se o backend estiver fora:
			setTimeout(() => {
				simulateStreaming(aiMsgId);
			}, 500);
		}
	}

	function handleSuggestion(suggestion: Suggestion) {
		if (!suggestion?.prompt) return;
		sendMessage(suggestion.prompt);
	}

	// Helper para UX "Mock" (Usado só se não houver um Backend Mock ou Real rodando WS na 8080)
	function simulateStreaming(msgId: string) {
		const sampleText = "Analisei seu pipeline: 3 deals entraram em zona ideal e 5 estao em risco. Quer que eu priorize o que atacar hoje e gere um resumo rapido para a semana?";
		let i = 0;
		const interval = setInterval(() => {
			const idx = messages.findIndex(m => m.id === msgId);
			if (idx === -1) return clearInterval(interval);

			if (i < sampleText.length) {
				const charCode = sampleText.charCodeAt(i);
				// Apenas append char (chunking básico)
				messages[idx].content += sampleText[i];
				i++;
			} else {
				messages[idx].isStreaming = false;
				clearInterval(interval);
			}
		}, 30);
	}
</script>

<div class="flex-1 flex flex-col h-full bg-background relative overflow-hidden text-foreground min-h-0">
	<!-- Top Bar -->
	<header class="h-14 flex items-center justify-between px-6 w-full shrink-0 border-b border-[#1F2A37] bg-[#0C1923] text-white z-10 absolute top-0">
		<div class="font-medium text-sm flex items-center gap-2 text-white/70">
			<span>G4 Compass</span>
		</div>
		<button class="w-8 h-8 rounded-full bg-[#152634] border border-[#1F2A37] flex justify-center items-center text-xs font-bold font-mono tracking-wider overflow-hidden text-white/80">
			MP
		</button>
	</header>

	{#if loadingPage}
		<div class="flex-1 flex items-center justify-center bg-background">
			<div class="relative w-12 h-12 flex items-center justify-center">
				<div class="absolute inset-0 bg-primary/20 rounded-full animate-ping"></div>
				<BrainCircuit class="w-6 h-6 text-primary animate-pulse relative z-10" />
			</div>
		</div>
	{:else if messages.length === 0}
		<!-- Empty State Area (Centered Chat) -->
		<div class="flex-1 flex flex-col items-center justify-center p-4 pt-20 overflow-y-auto">
			<!-- Greeting -->
			<div class="flex flex-col items-center gap-4 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
				<Sparkles class="w-8 h-8 text-foreground" />
					<h1 class="text-3xl text-foreground font-medium tracking-tight">
						{greeting}
					</h1>
			</div>

			<!-- Chat Input Block -->
			<div class="w-full max-w-3xl mb-8 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
				<ChatInput onsubmit={sendMessage} />
			</div>

			<!-- Action Suggestions -->
			<div class="flex flex-wrap items-center justify-center gap-3 max-w-2xl animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-500">
				{#each suggestions as suggest}
					<button
						class="flex items-center gap-2 px-4 py-2 rounded-xl border border-border/30 bg-secondary/20 text-sm text-foreground hover:bg-secondary/60 transition-all shadow-sm"
						onclick={() => handleSuggestion(suggest)}
					>
						<suggest.icon class="w-4 h-4 text-muted-foreground" />
						{suggest.label}
					</button>
				{/each}
			</div>
		</div>
	{:else}
		<!-- Chat History Area -->
		<div class="flex-1 overflow-y-auto w-full pt-16 pb-48 md:pb-32 px-4 flex flex-col scroll-smooth min-h-0">
			<div class="max-w-3xl w-full mx-auto flex flex-col gap-6">
				{#each messages as msg}
					<div class="flex w-full {msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300">
						
						{#if msg.role === 'assistant'}
							<!-- Assistant Marker -->
							<div class="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center shrink-0 mr-4 shadow-sm border border-primary/20">
								<img src="/logo-icon.svg" alt="G4 Compass" class="w-5 h-5" />
							</div>
						{/if}

						<div class="max-w-[85%] rounded-2xl px-5 py-4 text-[15px] leading-relaxed 
							{msg.role === 'user' ? 'bg-[#0C1923] text-white border border-[#1F2A37]' : 'bg-transparent text-foreground'}">
							
							{#if msg.role === 'assistant' && !msg.content && msg.isStreaming}
								<div class="flex flex-col gap-2">
									<div class="flex items-center gap-2 text-primary font-medium animate-pulse text-sm">
										<BrainCircuit class="w-4 h-4" />
										<span>{thinkingPhrase}</span>
									</div>
									<div class="flex gap-1">
										<div class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay: 0ms"></div>
										<div class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay: 150ms"></div>
										<div class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay: 300ms"></div>
									</div>
								</div>
							{:else}
								<!-- Rich Markdown Content -->
								<Markdown content={msg.content} />

								{#if msg.isStreaming}
									<span class="inline-block w-1.5 h-4 bg-primary align-middle ml-1 animate-pulse"></span>
								{/if}
							{/if}
						</div>

					</div>
				{/each}
			</div>
		</div>

		<!-- Pinned Bottom Input -->
		<div class="w-full absolute bottom-16 md:bottom-0 left-0 bg-gradient-to-t from-background via-background/95 to-transparent pb-24 md:pb-6 pt-10 px-4">
			<div class="max-w-3xl mx-auto">
				<ChatInput onsubmit={sendMessage} />
			</div>
		</div>
	{/if}
</div>
