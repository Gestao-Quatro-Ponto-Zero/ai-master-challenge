# PRD — App de triagem e diagnóstico (Vercel)

- **Versão:** v1.1 · 2026-11-10 · respostas do Daniel ao [questionário](00-questionario.md) (rodadas 1 e 2)
- **Status:** **Rascunho para validação. Construção não iniciada** (instrução do Daniel). Decisões estruturais na ADR-0014 (Proposta).
- **Regra de leitura:** onde o Daniel não comentou uma pergunta do questionário, vale a sugestão da IA.

---

## 1. Objetivo
Responder ao Diretor de Operações em um app só:
1. onde a operação perde tempo;
2. quanto isso custa e quanto a IA economizaria nos casos em que teria autonomia;
3. a automação funcionando com tickets reais.

O método (proposta de automação, decisões, uso de IA e condução do projeto) fica numa área própria, "Como foi feito".

**Destaques que o app precisa evidenciar** (P1): o domínio de IA aplicada e o **conhecimento em gestão** do Daniel. A gestão aparece em três lugares: capacidade e custo (Painel › ROI), indicadores da operação (Painel › Operação) e condução do projeto (Como foi feito).

## 2. Público e uso
- **Avaliadores do G4:** abrem o link do PR, navegam o Painel e testam o Console ao vivo, sem exemplos preparados.
- **Vídeo (5 min):** primeiro o workflow com IA, depois a navegação no app. O app não tem página "sobre mim".

## 3. Arquitetura de informação

Três áreas, cada uma com um **toggle interno** (controle segmentado) que troca a visão sem mudar de rota principal.

| Área (rota) | Toggle interno | Conteúdo |
|---|---|---|
| **Painel** (`/`) | Diagnóstico · ROI · Operação | Indicadores do DS1, economia estimada e métricas do sistema ao vivo |
| **Console** (`/console`) | Triagem · Fila · Caixa | Testar a automação, revisar rascunhos, ver alertas |
| **Como foi feito** (`/como-foi-feito`) | Proposta · Decisões · Condução | Fluxo da automação, métodos, o que não automatizar, ADRs, gestão do projeto, uso de IA |

O estado do toggle vai na URL (`/?visao=roi`, `/console?aba=fila`) para permitir links diretos (B5).

### 3.1 Navegação (recomendação)
**Desktop: top bar minimalista, 64 px, fundo `--bg` com divisor de 1 px em `--border`.**
- Esquerda: nome do app em Libre Baskerville.
- Centro: **controle segmentado das 3 áreas**, em formato pill, fundo `--surface-2`, item ativo em `--surface` com sombra suave e texto `--text-1`.
- Direita: alternância de tema (sol/lua, Lucide).
- Abaixo do título de cada página, o **toggle interno** como segundo controle segmentado, menor e alinhado à esquerda.
- O dourado **não** marca o item ativo da navegação. Ele fica reservado ao número protagonista de cada tela (regra Órbita).
- Badges discretos na navegação (B3): "Console · 3" com contagem de pendentes da fila e não lidas da caixa.

**Mobile: barra flutuante centralizada no rodapé.**
- Pill com 3 ícones + rótulo curto (Painel · Console · Método), 16 px acima da borda, com respeito à safe area.
- Fundo navy (`--navy-600`) com leve translucidez; item ativo com fundo `--surface` e texto navy.
- O toggle interno fica no topo do conteúdo, com rolagem horizontal se não couber.
- Na rolagem para baixo a barra continua visível, sem esconder.

## 4. Telas

### 4.1 Painel › Diagnóstico
Princípio: **poucos gráficos, cada um com uma conclusão escrita no topo** (headline first, em serifa).

1. **Número protagonista (dourado):** 33,3% dos tickets sem 1ª resposta. Ao lado, em neutro: 34,0% aguardando o cliente, e tempo de 1ª resposta → resolução de 6,3 h (mediana; só nos 50,7% de registros coerentes).
2. **Onde o fluxo trava: um gráfico de barras com seletor.**
   - Seletor de **métrica**: % sem 1ª resposta · % aguardando cliente · tempo até resolução · CSAT.
   - Seletor de **dimensão**: canal · prioridade · tipo · assunto · produto.
   - Cada barra traz o intervalo de confiança.
   - O resultado do teste aparece em linguagem simples, num selo acima do gráfico. Exemplo: "Os canais têm desempenho equivalente (a diferença observada está dentro do que o acaso produz)". O p-valor fica no tooltip.
   - Produto (42 grupos) mostra só os 10 maiores grupos + "outros".
3. **O que impacta a satisfação: forest plot.** CSAT médio com IC 95% por grupo da dimensão escolhida (sem seletor de métrica). Uma linha vertical marca a média geral (2,99).
   - Card ao lado: "70 variáveis explicam 2,1% da variação do CSAT".
   - **Callout de sobrevivência:** "O CSAT existe só para os 32,7% de tickets fechados. Os 67,3% sem resolução, os mais prováveis de gerar insatisfação, não são medidos."

**Fora desta tela** (decisão do Daniel): filtros globais, exploração da tabela crua, histograma de CSAT, recomendações de instrumentação e painel de confiabilidade dos dados.

### 4.2 Painel › ROI
1. **Premissas editáveis** (4 controles, cada um com a pill de origem e link para a fonte):
   - volume anual (30.000, brief);
   - minutos por ticket (8,6, MetricNet/HDI);
   - custo/hora (R$ 21,30, CAGED);
   - % de casos com autonomia da IA. Padrão: **medido no DS2**, com opção de ajuste manual.
2. **Frase de resultado (dourado no valor):** "Nos casos em que a IA teria autonomia, a economia seria de aproximadamente **R$ X por ano**." Logo abaixo: Y horas/ano · Z agentes em tempo integral liberados · custo por ticket de R$ 3,05 → R$ W.
3. **Composição do cálculo:** uma linha de "fórmula legível" com os valores atuais, por exemplo "30.000 tickets × 44% elegíveis × 52% com autonomia × 8,6 min × R$ 21,30/h".
4. Sem a nomenclatura "nível 1/2/3"; ver seção 5.
5. A economia oficial considera **só os casos com autonomia** (C13 sem cenário de ganho na revisão humana).

### 4.3 Painel › Operação
Indicadores do sistema real, lidos de `triage_runs`, `hitl_queue`, `notifications` e `validated_resolutions`:
- **Protagonista (dourado):** % de triagens resolvidas com autonomia da IA.
- Triagens totais e distribuição pelos 3 caminhos (ver seção 5).
- Acurácia nas triagens de tickets do holdout (previsto × rótulo real), com aviso de amostra pequena quando n < 30.
- Revisão humana: aprovadas sem edição · editadas · rejeitadas · tempo médio na fila.
- Latência p50/p95 e custo OpenAI acumulado.
- Base de conhecimento: soluções do playbook × soluções aprendidas com a revisão.
- Atualiza a cada carregamento, com botão "atualizar".

### 4.4 Console › Triagem
1. **Entrada:**
   - **Sortear do holdout** (padrão), com filtro opcional por categoria real;
   - **Escrever um ticket**, em inglês, até 4.000 caracteres, com aviso do porquê (a base é em inglês).
   - Sem exemplos prontos.
2. **Resultado** (de cima para baixo):
   1. selo do caminho, com o motivo em uma frase;
   2. categoria prevista com barra de confiança e distribuição dos votos;
   3. os 5 casos mais parecidos, com similaridade;
   4. a ação tomada: resposta enviada, rascunho na fila (com link) ou alerta na caixa (com link);
   5. rodapé técnico colapsável: tempo de cada etapa, ID da triagem, tokens e custo da chamada.
3. **Etapas da triagem (stepper):** embedding → busca de casos parecidos → regra de decisão → redação. Mostra os tempos medidos depois da resposta, sem simular progresso.
4. **Rótulo real** para tickets do holdout ("Categoria real: Storage ✓") e acurácia acumulada da sessão.
5. **Histórico da sessão:** as 10 últimas triagens do visitante.
6. **Modo offline** quando o n8n não responder: para tickets do holdout, a classificação vem direto da função `classify_ticket` no Supabase (sem redação), com aviso. O texto livre fica desabilitado.
7. Nenhum link para o n8n (a URL da VPS não aparece).

### 4.5 Console › Fila
Lista à esquerda (abas Pendentes · Decididos, da mais antiga para a mais nova, com "há X min") e detalhe à direita, com:
- ticket original, categoria prevista e confiança, casos parecidos;
- rascunho editável e as checagens sugeridas pelo LLM em formato checklist;
- ações Aprovar · Editar e aprovar · Rejeitar;
- correção de categoria (dropdown das 8 categorias).

Depois de aprovar: **"Esta solução agora atende tickets parecidos"**, com um botão que leva ao Console › Triagem já com um vizinho sorteado.
Sem login e sem campo de nome (R1). A decisão fica registrada como "visitante".

### 4.6 Console › Caixa
- Card neutro por alerta, com a **pré-visualização do texto exato** que iria para o Slack (toggle) e a nota "no ambiente real, enviado pelo nó Slack do n8n".
- Ações: marcar como lida e assumir.
- Filtro Tickets · Sistema (alertas de heartbeat).

### 4.7 Como foi feito
| Toggle | Conteúdo |
|---|---|
| **Proposta** | Diagrama interativo do fluxo (hover em cada etapa com a regra); os 3 caminhos e seus critérios; **o que não automatizar**, com 3–5 tickets reais de HR Support / Administrative rights e os tipos do DS1 que vão para humano; comparação de métodos (TF-IDF 86,9% · RAG 82,8% · LLM zero-shot 43,2% · RAG + LLM 80,8%) e o motivo da escolha do RAG; matriz de confusão compacta |
| **Decisões** | Linha do tempo das ADRs (título, quem decidiu, status) com link para o texto no repositório; destaques do judgment log (onde a IA errou, o que o humano decidiu) |
| **Condução** | **Objetiva e concisa** (R5): uma tela, blocos curtos, cada um com o fato e a evidência. Ver 4.7.1 |

Os textos vêm dos `.md` do repositório, lidos no build, para não duplicar conteúdo.

#### 4.7.1 Condução — conteúdo (R5, Daniel)
Uma tela, sem rolagem longa. Cada bloco tem um título, até 3 linhas e o link da evidência.
1. **Ideação e estrutura do projeto no Claude Code:**
   - a pasta de memória persistente (`AGENTS.md` como fonte única, `CLAUDE.md` só importando, `context/STATE.md` para handoff), legível também pelo Codex;
   - o protocolo de sessão (ler o STATE, registrar ADR e process log, commitar);
   - os MCPs isolados do projeto (`supabase-g4`, `vercel-g4`, `n8n-g4`), separados das contas pessoais;
   - o `git-add.sh` que respeita o `.gitignore`;
   - as sessões paralelas por frente.
2. **Plano e timebox:** dois turnos noturnos, entregas por turno.
3. **Decisões registradas:** número de ADRs, quem decidiu cada uma, quantas a IA propôs e o Daniel mudou.
4. **Riscos tratados:** dado sintético, credenciais de outros projetos auto-atribuídas no n8n, custo da OpenAI, app público sem login (limites + monitoramento).
5. **Custo do projeto:** embeddings, avaliações e testes (valores medidos).
6. **Capacidade da operação:** horas e agentes equivalentes liberados, puxados do ROI.

## 5. Nomenclatura dos caminhos (substitui "nível 1/2/3" na interface)
| Interno (banco, ADRs) | Na interface | Cor |
|---|---|---|
| nível 1 | **Resposta automática** | `--green` |
| nível 2 | **Revisão humana** | `--gold` (só no selo; ver regra do dourado) |
| nível 3 | **Somente humano** | navy / `--text-1` |

O vermelho fica reservado a falha ou alerta de sistema. Confirmar na pendência R3.

## 6. Design (base Órbita do João Vitor)
- **Tokens:** os de [design-system.md](../design-system.md), como CSS variables, com tema claro (paper) por padrão e alternativa escura.
- **Tipografia:** Libre Baskerville nas conclusões e títulos de seção; Manrope na interface e nos números; IBM Plex Mono em IDs, tempos e trechos de tickets.
- **Um dourado por tela:**

  | Tela | Protagonista em dourado |
  |---|---|
  | Diagnóstico | 33,3% |
  | ROI | R$/ano |
  | Operação | % com autonomia |
  | Triagem | selo do caminho |
  | Fila | botão Aprovar |
  | Caixa | nenhum |
  | Como foi feito | nenhum |

  O selo "Revisão humana" usa contorno dourado, sem preenchimento, para não competir.
- **Paleta das 8 categorias:** tons dessaturados derivados de navy/gold mais neutros quentes, validados em AA nos dois temas, com rótulo sempre escrito.
- **Componentes:** Tailwind + shadcn/ui reestilizado; Recharts para barras e IC; forest plot customizado; ícones Lucide.
- **Animação:** só skeletons e transição do stepper.
- **Responsivo:** desktop-first; Console e Fila usáveis no celular.
- **Marca:** sem logo nem nome G4 no app. Rodapé: "Protótipo de candidato ao processo AI Master do G4. Linguagem visual inspirada no Core-Slides-G4 (MIT). Não é um produto oficial do G4."
- **Acessibilidade:** WCAG AA, foco visível, Console e Fila operáveis por teclado.

### 6.1 Regras de texto (L1, Daniel)
- Frases afirmativas e diretas, com o dado. **Sem antagonismos** do tipo "é X, não Y" e **sem analogias**.
- Conclusão primeiro, método em "ver como calculamos".
- Termos técnicos explicados por tooltip na primeira ocorrência e reunidos num glossário em "Como foi feito".

## 7. Arquitetura técnica
- **Stack:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts, em `solution/app/`. Vercel Hobby, região `gru1`.
- **Dados (J2 = B, tudo do Supabase):**
  - **Resultados da análise:** novas tabelas `analysis_diagnostic_cuts` (o CSV atual), `analysis_metrics` (os JSON de avaliação, um registro por arquivo) e `analysis_examples` (tickets de exemplo do "o que não automatizar"). Carregadas por script a partir das saídas reproduzíveis de `solution/analysis/`. O Python continua sendo a fonte do cálculo estatístico, e o Supabase a fonte de leitura do app.
  - **Agregados simples do DS1:** views SQL (`v_ds1_status`, `v_ds1_cuts`).
  - **Operação:** consultas ao vivo nas tabelas do n8n.
- **Acesso ao Supabase:** só no servidor (Server Components e Route Handlers), com a service role. O navegador não recebe chave.
- **Rotas de API:**
  - `/api/triage` e `/api/hitl`: repassam ao n8n com `X-Webhook-Secret`, timeout de 30 s e modo offline;
  - `/api/heartbeat`: Vercel Cron às 12:00 UTC, protegido por `CRON_SECRET`;
  - `/api/demo/reset`: restaurar demonstração.
  - Todas as rotas `/api/*` aplicam os limites de uso e gravam em `usage_events` (8.1).
- **Deploy:** projeto Vercel ligado ao fork no GitHub, com *root directory* `submissions/daniel-fonseca/solution/app`.
- **Variáveis:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `N8N_BASE_URL`, `N8N_WEBHOOK_SECRET`, `CRON_SECRET`, `IP_HASH_SALT`, `FREE_TEXT_ENABLED` e os limites de uso (`RATE_*`).
- **Banco (novo):** tabela `usage_events`; `notifications.kind` passa a aceitar `usage_alert`; colunas de tokens, custo e latência em `triage_runs` (migration na construção).
- **Testes:** unitários das fórmulas do ROI + 1 e2e do Console.

## 8. Segurança, abuso e custo
- **Sem login** (R1, decisão do Daniel). Painel, Console e Como foi feito são públicos.
- **Limites de uso** (aplicados no servidor, nas rotas `/api/*`, contados na tabela `usage_events`):

  | Ação | Por IP | Global |
  |---|---|---|
  | Triagem com texto livre | 10 / hora · 20 / dia | 300 / dia |
  | Triagem de ticket do holdout | 30 / hora · 60 / dia | 600 / dia |
  | Ações na fila (aprovar, editar, rejeitar) | 30 / hora | 300 / dia |
  | Restaurar demonstração | 3 / dia | 10 / dia |

  Acima do limite, a rota responde 429 com uma mensagem clara. Os números são a proposta inicial e ficam em variáveis de ambiente.
- **Teto de gasto** no projeto da OpenAI (configurado pelo Daniel no painel da OpenAI).
- **Interruptor manual** `FREE_TEXT_ENABLED` (variável de ambiente) para pausar o texto livre. **Só é usado com instrução do Daniel** (8.1).
- **Dados pessoais:** nome e e-mail do DS1 não aparecem em nenhuma tela. O IP do visitante é guardado só como hash com sal (`ip_hash`), por 30 dias.
- **Restaurar demonstração:** recria 2–3 itens na fila e alertas na caixa, dentro dos limites acima.
- **Fila e caixa sem identificação do revisor** (sem login, sem campo de nome). O registro guarda "visitante" + `ip_hash`.

### 8.1 Monitoramento de uso e alertas (pedido do Daniel)
**Regra de conduta:** a rotina **observa e alerta**. Nenhuma ação contra abuso é tomada sem instrução clara do Daniel, seja pausar o texto livre, bloquear um IP, despublicar um workflow, mudar limites ou apagar dados. Os limites da tabela acima são a única proteção automática, porque foram aprovados antes.

**O que é registrado** (tabela `usage_events`, gravada pelas rotas da Vercel):
`ts`, `route`, `ip_hash`, `user_agent` (resumido), `outcome` (ok · 429 · 4xx · 5xx · offline), `latency_ms`, `tokens_in`/`tokens_out` e `cost_usd` (vindos de `triage_runs`), `flag` (ex.: texto com padrão de *prompt injection*).

**Sinais de alerta (proposta):**

| Sinal | Limite para alertar | Fonte |
|---|---|---|
| Um IP com muitas triagens | > 10 em 1 hora | `usage_events` |
| Respostas 429 | > 20 em 1 hora (alguém insistindo no limite) | `usage_events` |
| Volume global | > 100 triagens em 1 hora | `usage_events` |
| Custo OpenAI do dia | > US$ 0,50 (≈ 160 triagens) | `triage_runs` |
| Erros 5xx ou execuções com erro no n8n | > 5 em 1 hora | `usage_events` + execuções do n8n |
| Texto com padrão de *prompt injection* ("ignore previous instructions", pedidos de chave ou prompt) | qualquer ocorrência | `usage_events.flag` |
| Ações em massa na fila | > 30 em 1 hora por IP | `usage_events` |
| Banco perto do limite | > 400 MB de 500 | Supabase |

**Como a rotina funciona:**
1. **Camada determinística (n8n, a cada 15 min):** workflow "Monitor de uso" consulta `usage_events` e `triage_runs`. Se um sinal passar do limite, grava um alerta em `notifications` (`kind = 'usage_alert'`) e envia ao Daniel pelo canal escolhido (R8). Custo zero de LLM.
2. **Camada de leitura de logs (Claude, rotina agendada):** lê o resumo do monitor, os logs de runtime da Vercel (`vercel-g4`; o plano Hobby guarda só 1 hora), os logs do Supabase (`supabase-g4`) e as execuções do n8n (`n8n-g4`). Manda ao Daniel um resumo curto com o que observou e as opções de ação, **sem executar nenhuma**.
3. **Resposta:** o Daniel decide. A IA só executa a ação que ele instruir e registra no process log.

O script e o workflow ficam versionados (`scripts/monitor_usage.py`, `solution/n8n/04_monitor_uso.sdk.ts`) e entram na construção, depois do deploy.

## 9. KPIs
| KPI | Fórmula | Fonte | Tela |
|---|---|---|---|
| % sem 1ª resposta | Open / total | DS1 | Diagnóstico |
| % aguardando cliente | Pending / total | DS1 | Diagnóstico |
| Tempo 1ª resposta → resolução | mediana, registros coerentes | DS1 | Diagnóstico |
| CSAT médio (IC 95%) | média dos fechados | DS1 | Diagnóstico |
| Poder explicativo do CSAT | R² com 70 variáveis | DS1 | Diagnóstico |
| Economia nos casos com autonomia | volume × % elegível × % autonomia × min × R$/h | DS1 × DS2 + premissas | ROI |
| Horas/ano e agentes liberados | economia em horas ÷ 1.976 h/ano | idem | ROI |
| Custo por ticket antes × depois | custo total ÷ volume | idem | ROI |
| % com autonomia (ao vivo) | caminho automático / triagens | `triage_runs` | Operação |
| Acurácia ao vivo | previsto = real (holdout) | `triage_runs` × `ds2_tickets` | Operação |
| Revisão humana | aprovadas / editadas / rejeitadas, tempo na fila | `hitl_queue` | Operação |
| Latência e custo | p50/p95; tokens × preço | `triage_runs` | Operação |
| Base de conhecimento | playbook × aprendidas | `validated_resolutions` | Operação |

Para o custo por triagem ficar disponível, o n8n passa a gravar os tokens usados e a latência em `triage_runs` (ajuste pequeno no fluxo 1, colunas novas).

## 10. Escopo (revisto)
- **Must:**
  - Shell (top bar, barra inferior mobile, temas);
  - Painel › Diagnóstico e ROI;
  - Console › Triagem, Fila e Caixa;
  - rotas de API + modo offline + limites de uso e `usage_events`;
  - `/api/heartbeat` + cron;
  - tabelas e views de leitura no Supabase;
  - deploy.
- **Should:**
  - monitoramento e alertas (8.1);
  - Painel › Operação;
  - Como foi feito (Proposta + Decisões);
  - efeito "aprendeu";
  - restaurar demonstração;
  - links diretos.
- **Could:** Como foi feito › Condução com conteúdo rico, matriz de confusão interativa, e2e.
- **Won't:** login, Realtime, Slack real, edição do playbook pela interface, filtros globais, tabela crua do DS1, painel de confiabilidade, curva cobertura × precisão, diagrama DS1 × DS2, exemplos prontos no Console.

## 11. Execução em sessões paralelas
1. **Base (esta sessão ou a primeira):** projeto Next.js, tokens Órbita, shell de navegação, cliente Supabase no servidor, tabelas e views de leitura, rotas de API vazias, deploy de preview.
2. **Frente A (sessão própria):** Painel (Diagnóstico, ROI, Operação) + Como foi feito.
3. **Frente B (sessão própria):** Console (Triagem, Fila, Caixa) + `/api/triage`, `/api/hitl`, modo offline, limites de uso, `usage_events` e restaurar demonstração.
4. **Depois do deploy:** workflow "Monitor de uso" no n8n + rotina agendada do Claude (8.1), conforme R8–R11.

As frentes A e B não editam os mesmos arquivos: cada uma tem sua pasta de rotas e de componentes, e os componentes compartilhados ficam na base.

## 12. Critérios de pronto
- Deploy em produção com as três áreas navegáveis no desktop e no celular.
- Um ticket de cada caminho testado ao vivo pelo Console, com Fila e Caixa refletindo.
- Lighthouse ≥ 90 em acessibilidade.
- **Validação do Daniel** da documentação e do checklist de submissão do G4 (README no template, process log, PR), item por item. Só então está pronto.

## 13. Decisões da rodada 2 e pendências da rodada 3

**Resolvidas (10/11):**
- **R1:** sem login, com limites de uso e monitoramento (seção 8).
- **R5:** Condução objetiva e concisa, incluindo a ideação e a estrutura do projeto no Claude Code (4.7.1).
- **R2, R3, R4, R6 e R7:** aceitas como sugeridas.
  - O app abre no Painel › Diagnóstico.
  - Os caminhos se chamam Resposta automática · Revisão humana · Somente humano.
  - O ranking 2,29 × 3,57 aparece como uma frase no selo de significância.
  - O toggle do Painel segue a ordem Diagnóstico · ROI · Operação.
  - O tema escuro fica como opção.

**Pendências (rodada 3, sobre o monitoramento):**

| # | Pergunta | Sugestão da IA |
|---|---|---|
| **R8 ★** | Por qual canal você quer receber os alertas? | **Notificação push no celular pela rotina do Claude** para o resumo, e alerta imediato do n8n por **e-mail** para você (credencial Gmail/SMTP dedicada G4). Alternativa: WhatsApp pelo seu WAHA, que pertence a outro contexto e exigiria uma credencial nova e separada |
| R9 | Frequência da rotina do Claude (leitura de logs) | A cada **2 horas** nos dias de avaliação, com resumo só quando houver algo fora do normal, e 1 resumo diário às 09:00 mesmo sem alertas |
| R10 | Os limites e os gatilhos de alerta das tabelas da seção 8 estão bons? | Sim, como ponto de partida, ajustados depois do primeiro dia de uso real |
| R11 | Por quanto tempo manter a rotina ativa? | Do deploy até o resultado do processo seletivo; desligada por sua instrução |
