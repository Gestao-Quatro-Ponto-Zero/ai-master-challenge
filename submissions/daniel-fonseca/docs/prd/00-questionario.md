# PRD do app Vercel — questionário colaborativo (rodada 1)

> **Como responder:** cada pergunta tem uma **sugestão da IA** (`→ Sugestão`). Responda só onde discordar ou quiser detalhar, por exemplo "A3: prefiro X", ou escreva "ok" para aceitar uma seção inteira.
> Depois das respostas, a IA escreve o `docs/prd/01-prd.md` (versão para execução) e uma ADR com as decisões estruturais.
> Contexto já decidido: dashboard responde ao diagnóstico, com o enquadramento da ADR-0003; o console é o **validador** da automação (ADR-0008); a caixa de mensagens substitui o Slack (ADR-0007); o heartbeat roda pela Vercel Cron (ADR-0006); o design segue a base "Órbita" do João Vitor ([design-system.md](../design-system.md)).
> As perguntas marcadas com ★ mudam escopo ou arquitetura e são as que mais precisam da sua decisão.

---

## A. Objetivo, público e narrativa

**A1 ★ Quem é o usuário principal do app?** O avaliador do G4 (que abre o link sem contexto), o "Diretor de Operações" da história do case, ou o atendente de suporte?
→ Sugestão: **duas personas, uma narrativa.** O Diretor no dashboard (perguntas 1 e 3 do diretor) e o atendente/supervisor no console e na fila. O avaliador entra como "Diretor" e termina operando o console.

**A2 ★ Qual é a história que o app conta, e em que ordem?**
→ Sugestão, em 4 atos:
1. "Onde perdemos tempo": diagnóstico, incluindo o alerta de que o dado é sintético.
2. "O que dá para automatizar e o que não": proposta e os 3 níveis.
3. "Funciona": console com tickets reais do holdout.
4. "Quanto vale": ROI com premissas editáveis.

**A3 Página inicial:** visão executiva com os 3–4 números que respondem ao Diretor, ou ir direto ao dashboard?
→ Sugestão: **página "Resumo executivo"** com 4 cards (gargalo transversal 33% sem 1ª resposta · nenhuma variável explica o CSAT (R² ≈ 0) · 31% automatizável com 98,8% de precisão · ~R$ 21 mil/ano recuperáveis só no nível 1) e um CTA "Testar a automação" que leva ao console.

**A4 Tempo de leitura alvo:** quanto tempo o avaliador deve levar para entender a proposta?
→ Sugestão: **3 minutos** no resumo + dashboard; **2 minutos** no console. Tudo o mais é "aprofundar".

**A5 O app explica o método (ADRs, process log, como a IA foi usada)?** Isso é critério do challenge (process log).
→ Sugestão: **sim, uma aba "Como foi feito"** com linha do tempo das decisões (ADRs), as seções "onde a IA errou / o que o humano decidiu" do judgment log e links para o repositório. Sem duplicar texto: a página lê os `.md` do repo no build.

**A6 Idioma:** pt-BR em toda a interface?
→ Sugestão: **pt-BR**, mantendo os termos técnicos com tradução na primeira ocorrência (ex.: "holdout (conjunto de teste)") e os dados do DS2 em inglês, como estão.

**A7 Nome do produto/app** (aparece no título, no header e no README).
→ Sugestão: algo neutro, por exemplo **"Triagem Inteligente — Case AI Master"**. Evitar "G4" no nome do produto (ver I8).

---

## B. Arquitetura de informação e navegação

**B1 ★ Quais páginas existem no MVP?**
→ Sugestão (rotas):

| Rota | Página | Ato |
|---|---|---|
| `/` | Resumo executivo | 1–4 |
| `/diagnostico` | Diagnóstico (3 abas: Onde trava · Satisfação · Desperdício) + painel "Confiabilidade dos dados" | 1 |
| `/automacao` | Proposta: fluxo, 3 níveis, o que **não** automatizar, comparação de métodos, curva cobertura × precisão | 2 |
| `/console` | Validador: enviar ou sortear ticket → resultado ao vivo | 3 |
| `/fila` | Fila de revisão humana (HITL) | 3 |
| `/caixa` | Caixa de mensagens (alertas do nível 3 e heartbeat) | 3 |
| `/operacao` | Métricas do próprio sistema (triagens feitas no console) | 3–4 |
| `/roi` | Calculadora de ROI (pode ser aba de `/diagnostico` ou de `/automacao`) | 4 |
| `/como-foi-feito` | Método, ADRs, process log | — |

**B2 Navegação:** sidebar fixa à esquerda ou top bar?
→ Sugestão: **sidebar** agrupada em "Diagnóstico" (Resumo, Diagnóstico, ROI) e "Operação" (Console, Fila, Caixa, Métricas), mais "Como foi feito" no rodapé. No mobile ela vira drawer.

**B3 Badges de contagem na navegação** (ex.: "Fila 3", "Caixa 2 não lidas")?
→ Sugestão: **sim**. Reforça que o sistema está vivo.

**B4 ROI: página própria ou aba?**
→ Sugestão: **aba "Desperdício" dentro do diagnóstico**, com um bloco final "e com a automação…" que puxa a taxa medida no DS2. Isso deixa o cruzamento DS1 × DS2 (ADR-0009) explícito numa tela só.

**B5 Deep links compartilháveis** (ex.: `/console?ticket=282`, `/diagnostico?tab=satisfacao`)?
→ Sugestão: **sim**, para o vídeo e o README apontarem para estados exatos.

---

## C. Dashboard de diagnóstico (questão 1)

### C.1 Onde o fluxo trava
**C1 ★ Visual principal:** tabela de cortes com p-valor, *small multiples* (um mini-gráfico por dimensão) ou heatmap canal × prioridade?
→ Sugestão: **small multiples** (canal, prioridade, tipo, assunto, produto), cada um com barras de "% sem 1ª resposta" e intervalo de confiança, e o veredito em linguagem simples: "diferença não significativa (p = 0,77)". O heatmap canal × prioridade × tipo entra como **"armadilha"**: mostra o ranking 2,29 × 3,57 e depois revela p = 0,50.

**C2 Métrica padrão dos cortes:** % sem 1ª resposta, % aguardando cliente, tempo 1ª resposta → resolução ou CSAT? Seletor?
→ Sugestão: **seletor de métrica** (4 opções); padrão "% sem 1ª resposta", que é o gargalo real.

**C3 Como mostrar significância para quem não é estatístico?**
→ Sugestão: **selo textual** ("diferença real" / "provável acaso") + tooltip com p-valor e IC. Nada de asterisco.

**C4 Gargalo transversal como "hero":** o número dourado da página é "33,3% sem 1ª resposta"?
→ Sugestão: **sim** (um único dourado por tela). Logo abaixo: "34,0% aguardando o cliente" e "o gargalo não é de um canal: é de capacidade".

**C5 Filtros globais** (canal, prioridade, tipo, produto, período)?
→ Sugestão: **sem filtros globais no MVP.** O dado é sintético, e filtrar sugere conclusões. Os cortes já são a análise. Filtro só dentro do "explorar dados".

**C6 "Explorar dados" (tabela crua do DS1 com busca e paginação)** entra no MVP?
→ Sugestão: **não no MVP**; link para o CSV e para o script reproduzível.

### C.2 O que impacta a satisfação
**C7 Visual:** CSAT médio com IC 95% por variável (forest plot) + R² do modelo com 70 variáveis?
→ Sugestão: **forest plot** horizontal (todas as barras cruzando 2,99) + card "70 variáveis explicam 2,1% (R² ajustado −0,005)" + callout do **viés de sobrevivência** (só 32,7% têm CSAT).

**C8 Mostrar a distribuição uniforme do CSAT** (553/549/580/543/544 por nota)?
→ Sugestão: **sim**, um histograma pequeno, que é a prova visual mais rápida de dado sintético.

**C9 Recomendação de instrumentação** (pesquisa para tickets abandonados, data de abertura) aparece como "próximos passos"?
→ Sugestão: **sim**, num bloco "O que eu mediria numa operação real" em 3 bullets.

### C.3 Quanto estamos desperdiçando
**C10 ★ Premissas editáveis:** quais o usuário pode mexer? Volume anual, tempo de manuseio (global ou por tipo), custo/hora, % de follow-up?
→ Sugestão: **4 controles** (volume, minutos/ticket, R$/hora, % de automação por nível vindo do DS2 com opção "usar o medido"). Tempo por tipo fica como avançado (colapsado).

**C11 Origem de cada número:** rótulo "medido / benchmark com fonte / premissa / não mensurável" em cada card?
→ Sugestão: **sim, obrigatório** (ADR-0003). Pill pequena e neutra, com link para a fonte.

**C12 Saída do ROI:** horas/ano, R$/ano, atendentes equivalentes (FTE), custo por ticket antes × depois?
→ Sugestão: **as 4**, sendo **R$/ano recuperável** o dourado. Mostrar também a faixa conservadora ("só nível 1") × otimista ("nível 1 + 50% de ganho de tempo no nível 2"). Ver C13.

**C13 ★ Contar ganho de produtividade no nível 2** (rascunho pronto reduz o tempo de manuseio)?
→ Sugestão: **sim, como cenário separado e rotulado "premissa"** (ex.: o rascunho economiza 40% do tempo). O número oficial continua sendo só o nível 1.

**C14 Painel "Confiabilidade dos dados":** página própria, banner fixo ou card na entrada do diagnóstico?
→ Sugestão: **card de abertura do diagnóstico** ("Antes de ler: este dataset é sintético", com 5 evidências e link "ver provas") + selo discreto nos gráficos do DS1.

---

## D. Proposta de automação (questão 2)

**D1 Diagrama do fluxo:** estático (SVG) ou interativo (clicar na etapa mostra o nó n8n e o dado real)?
→ Sugestão: **SVG interativo leve**: ticket → embedding → RAG (classify_ticket) → política → 3 saídas, com hover explicando a regra e o link "ver no console".

**D2 Curva cobertura × precisão com slider de limiar** (o usuário move o 0,9 e vê cobertura e precisão mudarem, com os dados de `rag_only_policy.json`)?
→ Sugestão: **sim**. É o argumento central de que "limiar não é chute". O slider não muda a política em produção; é só simulação.

**D3 Comparação de métodos** (TF-IDF 86,9% · RAG 82,8% · LLM zero-shot 43,2% · RAG + LLM 80,8%) com a justificativa da escolha do RAG?
→ Sugestão: **sim, tabela + 1 parágrafo** "por que não o mais preciso" (decisão do Daniel, ADR-0010). Mostra julgamento, não só resultado.

**D4 ★ "O que NÃO automatizar" com exemplos reais:** mostrar 3–5 tickets do DS2 de HR Support / Administrative rights e os tipos do DS1 (reembolso, cancelamento, Critical) que vão para humano?
→ Sugestão: **sim, cards de exemplo** com o texto real e o motivo. É critério explícito do challenge.

**D5 Mostrar a matriz de confusão** (onde o RAG erra)?
→ Sugestão: **sim, compacta**, com destaque para Miscellaneous e Hardware, que mais se confundem. Mostra honestidade sobre os limites.

**D6 Ponte DS1 × DS2 (ADR-0009)** como diagrama "o DS2 prova quanto a IA acerta; o DS1 dimensiona quanto vale"?
→ Sugestão: **sim**, um bloco visual simples de duas colunas.

---

## E. Console — validador (questão 3)

**E1 ★ Modos de entrada:**
→ Sugestão:
- **"Sortear do holdout"** (padrão), com filtro opcional por categoria real e por "nível esperado";
- **"Escrever um ticket"** em inglês, até 4.000 caracteres, com aviso de idioma (ADR-0012);
- **3–5 exemplos prontos** ("um de cada nível"), para o vídeo.

**E2 Mostrar o rótulo real** de um ticket do holdout depois do resultado ("Real: Storage ✓")?
→ Sugestão: **sim**. Prova que não é cherry-picked. O console também acumula a "acurácia desta sessão".

**E3 ★ Layout do resultado:**
→ Sugestão, de cima para baixo:
1. Selo do nível (pill grande: Automático / Revisão humana / Só humano) + motivo;
2. Categoria + confiança (barra) + votos por categoria;
3. "Casos parecidos" (5, com similaridade);
4. Ação: resposta enviada (nível 1), rascunho na fila com link (nível 2) ou alerta gerado com link para a caixa (nível 3);
5. Rodapé técnico colapsável: latência, ID da triagem, tokens/custo.

**E4 Visualizar o pipeline em tempo real** (passos acendendo: embedding → RAG → política → LLM)?
→ Sugestão: **sim, um stepper** com o tempo de cada etapa. Como o n8n responde de uma vez, o stepper mostra o resultado com os tempos medidos, sem fingir streaming. Alternativa: só um spinner.

**E5 Histórico de triagens na sessão** (lista lateral com as últimas 10)?
→ Sugestão: **sim** (localStorage, por visitante) + link para `/operacao`, que mostra o histórico global.

**E6 ★ Modo fallback** quando o n8n estiver fora: mostrar resultado pré-computado do holdout com o aviso "modo offline"?
→ Sugestão: **sim**. Para os tickets do holdout, a classificação vem da função SQL direto no Supabase (sem LLM), com o aviso. O texto livre fica desabilitado no modo offline.

**E7 Botão "ver no n8n"** (link para a execução)?
→ Sugestão: **não**: exporia a URL da VPS. Em vez disso, mostrar o ID da triagem e "registrado em `triage_runs`".

**E8 Mostrar o custo estimado da chamada** (tokens × preço)?
→ Sugestão: **sim, no rodapé técnico.** Reforça a conversa de ROI.

---

## F. Fila de revisão humana (HITL)

**F1 Layout:** lista à esquerda + detalhe à direita (padrão inbox) ou cards?
→ Sugestão: **lista + detalhe.** No detalhe, o ticket original, a categoria prevista e a confiança, os casos parecidos, o rascunho editável, as "checagens" (do LLM, como checklist) e os botões Aprovar / Editar e aprovar / Rejeitar.

**F2 O revisor pode corrigir a categoria?**
→ Sugestão: **sim** (dropdown das 8). Grava `final_category`, que é o rótulo humano.

**F3 Identificação do revisor** sem login: campo "seu nome" lembrado no navegador?
→ Sugestão: **sim** (localStorage). Sem autenticação no MVP (ver K1).

**F4 ★ Mostrar o efeito "aprendeu"** depois da aprovação (ex.: "esta solução agora atende tickets parecidos; teste: [botão que sorteia um vizinho]")?
→ Sugestão: **sim**. É o ponto mais forte da demo (ADR-0004).

**F5 Filtros da fila:** pendentes / decididos / todos; ordenação por antiguidade?
→ Sugestão: **abas Pendentes · Decididos**, com ordenação pela mais antiga primeiro.

**F6 SLA visual** (tempo na fila)?
→ Sugestão: **sim, texto relativo** ("há 12 min"). Sem regra de SLA no MVP.

---

## G. Caixa de mensagens (nível 3 e sistema)

**G1 Visual da mensagem:** imitar um card de Slack (avatar, canal `#suporte-alertas`, formatação mrkdwn) ou um card neutro do app?
→ Sugestão: **card neutro com "pré-visualização do Slack"** (toggle). Não copia a marca do Slack; mostra o texto exato que seria enviado e uma nota "no caso real: nó Slack no n8n".

**G2 Ações na caixa:** marcar como lida, "assumir ticket" (muda o status)?
→ Sugestão: **marcar como lida** + **"assumir"** (grava quem assumiu). Responder ao cliente fica fora do MVP.

**G3 Alertas de sistema** (heartbeat falhou) na mesma caixa, com filtro?
→ Sugestão: **mesma caixa, com filtro "Tickets · Sistema"**.

---

## H. Métricas da operação (o sistema funcionando)

**H1 ★ KPIs do painel `/operacao`** (calculados de `triage_runs`, `hitl_queue`, `notifications`):
→ Sugestão:
- triagens totais;
- % por nível;
- **acurácia nos tickets do holdout** (previsto × real);
- taxa de aprovação sem edição no HITL;
- taxa de edição;
- taxa de rejeição;
- tempo médio na fila;
- latência p50/p95;
- custo OpenAI acumulado;
- soluções validadas (playbook × aprendidas).

**H2 Comparar o "ao vivo" com o "medido offline"** (ex.: nível 1 ao vivo 100% × holdout 98,8%)?
→ Sugestão: **sim, lado a lado**, com aviso de amostra pequena quando n < 30.

**H3 Último heartbeat** visível (ADR-0006)?
→ Sugestão: **sim, no rodapé global** ("Banco ativo · último heartbeat há 3 h").

**H4 Atualização:** em tempo real (Supabase Realtime) ou a cada carregamento?
→ Sugestão: **a cada carregamento + botão atualizar.** O Realtime exige expor o anon key com RLS/policies, que hoje estão fechadas. Fica fora do MVP.

---

## I. Design system e visual (base "Órbita" do João Vitor)

**I1 ★ Tema:** só claro (paper `#F5F4F3`), só escuro (navy `#001525`) ou os dois com toggle?
→ Sugestão: **claro por padrão + toggle escuro.** Os tokens já existem para os dois. O dashboard executivo lê melhor no claro; o console fica bem no escuro.

**I2 O "único protagonista dourado por tela":** confirmar o dourado de cada página?
→ Sugestão:
- Resumo: o R$/ano;
- Diagnóstico: 33,3% sem 1ª resposta;
- Satisfação: R² ≈ 0;
- Automação: 98,8% de precisão no nível 1;
- Console: o selo do nível;
- Fila: o botão Aprovar;
- Operação: % automatizado.

**I3 Paleta categórica para as 8 categorias do DS2** (navy e dourado não bastam):
→ Sugestão: **derivar 8 tons dessaturados** da escala navy/gold mais 2–3 neutros quentes, validados em contraste AA nos dois temas. Os rótulos ficam sempre escritos, nunca só cor (regra do design system).

**I4 Cores dos 3 níveis:**
→ Sugestão: Automático = `--green`, Revisão = `--gold`, Só humano = navy/`--text-1` (não vermelho: "só humano" não é erro, é decisão). O vermelho fica reservado para falha ou alerta.

**I5 Tipografia:**
→ Sugestão: **Libre Baskerville** nos títulos de seção e frases editoriais ("O gargalo não é de um canal"), **Manrope** na UI e nos números hero, **IBM Plex Mono** em IDs, latências e trechos do DS2. Carregar via `next/font`.

**I6 Biblioteca de gráficos:** Recharts, visx, Tremor, ECharts ou Observable Plot?
→ Sugestão: **Recharts** (React, simples e suficiente para barras, IC e linhas) com tema próprio pelos tokens. O forest plot e a curva com slider saem com componentes customizados leves.

**I7 Componentes de UI:** shadcn/ui (Radix + Tailwind) reestilizado com os tokens Órbita ou CSS próprio?
→ Sugestão: **Tailwind + shadcn/ui** com os tokens como CSS variables. É rápido de construir e acessível.

**I8 ★ Marca G4:** usar logo/nome G4 no header?
→ Sugestão: **não usar o logo nem "G4" como marca do app.** Usar só a linguagem visual, com a ressalva no rodapé: "Protótipo de candidato ao AI Master G4; linguagem visual inspirada no Core-Slides-G4 (MIT); não é produto oficial do G4." Isso evita parecer produto oficial.

**I9 Densidade e responsividade:** desktop-first? Funcionar no celular?
→ Sugestão: **desktop-first (≥ 1280 px)**, com layout que não quebra no tablet ou no celular. O console e a fila precisam ser usáveis no celular (o avaliador pode abrir o link no telefone).

**I10 Ícones:** Lucide?
→ Sugestão: **Lucide**, traço fino, usado com parcimônia.

**I11 Microinterações e animação:** contadores animados, transição do stepper?
→ Sugestão: **mínimas** (stepper e skeletons). Nada de animação decorativa.

**I12 Referências visuais que você gosta** (Linear, Vercel, Stripe, Notion, um dashboard específico)?
→ Pergunta aberta. Sem referência, a IA segue os slides do João Vitor: muito respiro, serifa editorial nos títulos, cards brancos sobre paper.

---

## J. Arquitetura técnica

**J1 ★ Stack:**
→ Sugestão: **Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts**, em `solution/app/`, com deploy na Vercel (Hobby, região `gru1`).

**J2 ★ De onde vêm os dados do dashboard:**
- (a) JSON/CSV pré-computados pelos scripts Python e copiados para o app no build;
- (b) consultas ao vivo no Supabase (views agregadas sobre `ds1_tickets`);
- (c) misto.

→ Sugestão: **misto.** Diagnóstico e avaliação = (a): estáticos, reproduzíveis e sem latência, e já são as saídas dos scripts. Operação, fila e caixa = (b), ao vivo, só no servidor.

**J3 Acesso ao Supabase:** só em Server Components/Route Handlers com a service role (nunca no navegador)?
→ Sugestão: **sim**, todas as leituras e escritas pelo servidor. O navegador nunca vê chave nenhuma. Isso mantém o RLS fechado como está.

**J4 Chamada ao n8n:** Route Handler `/api/triage` e `/api/hitl` na Vercel, que adicionam o `X-Webhook-Secret` e repassam?
→ Sugestão: **sim** (o segredo fica só no servidor), com timeout de 30 s e fallback (E6).

**J5 `/api/heartbeat` + Vercel Cron:** horário 12:00 UTC (09:00 SP), protegido por `CRON_SECRET`, gravando em `heartbeat` (`source = 'vercel-cron'`)?
→ Sugestão: **sim**. O n8n roda às 06:00 SP como redundância.

**J6 Deploy:** projeto Vercel ligado ao GitHub (fork, *root directory* `submissions/daniel-fonseca/solution/app`) com deploy a cada push, ou deploy por CLI/MCP?
→ Sugestão: **Git integration com o fork.** Cada push na branch gera um preview e o merge vai para produção. O avaliador vê o histórico de deploys.

**J7 Variáveis de ambiente na Vercel:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `N8N_BASE_URL`, `N8N_WEBHOOK_SECRET`, `CRON_SECRET`. Mais alguma?
→ Sugestão: essas 5. Opcional: `FREE_TEXT_DAILY_LIMIT`.

**J8 Testes:** quanto investir?
→ Sugestão: **mínimo útil**: testes das funções de cálculo do ROI (unitários) + 1 teste e2e do console (Playwright) contra o ambiente de preview. Nada além disso no timebox.

---

## K. Segurança, abuso e custo

**K1 ★ O app é público** (qualquer pessoa com o link) ou protegido?
→ Sugestão: **público.** O avaliador não deve precisar de login. A Vercel Hobby só oferece "Vercel Authentication", que exigiria conta Vercel.

**K2 ★ Proteção contra abuso do texto livre** (cada chamada custa OpenAI):
→ Sugestão:
- limite por IP (ex.: 20 triagens/dia) e global (ex.: 300/dia), contados numa tabela no Supabase;
- limite de gasto no projeto da OpenAI;
- botão "pausar texto livre" via variável de ambiente.

**K3 Ações destrutivas na fila e na caixa** (aprovar/rejeitar) abertas a qualquer visitante?
→ Sugestão: **sim no MVP** (é demo), com um botão "Restaurar dados de demonstração" que recria a fila. Ver O2.

**K4 Dados pessoais:** o DS1 tem nome e e-mail (sintéticos). Mostrar no app?
→ Sugestão: **não mostrar nome nem e-mail** nem na tabela; só os campos operacionais. É boa prática, mesmo com dado falso.

---

## L. Conteúdo, linguagem e acessibilidade

**L1 Tom dos textos:** executivo e direto ("o gargalo é capacidade, não canal") com detalhe técnico colapsado?
→ Sugestão: **sim.** Frases-conclusão em serifa no topo de cada seção ("headline first"); o método fica em "ver como calculamos".

**L2 Glossário/tooltips** (p-valor, IC, holdout, embedding, RAG, HITL)?
→ Sugestão: **tooltips curtos** + página de glossário dentro de "Como foi feito".

**L3 Acessibilidade:** meta WCAG AA (contraste, foco visível, navegação por teclado no console e na fila)?
→ Sugestão: **AA**. A regra "nunca só cor" já vem do design system.

**L4 ★ Tour guiado para o vídeo** (modo "apresentação" que segue os 4 atos com botões "próximo")?
→ Sugestão: **opcional (should have).** Ajuda no vídeo e no avaliador apressado. Se faltar tempo, o vídeo segue um roteiro manual.

---

## M. KPIs: definição formal (para validar)

| KPI | Fórmula | Fonte | Onde aparece |
|---|---|---|---|
| % sem 1ª resposta | status = Open / total | DS1 | Diagnóstico (hero) |
| % aguardando cliente | status = Pending / total | DS1 | Diagnóstico |
| Tempo 1ª resposta → resolução | mediana e p90, só nos registros coerentes (50,7%) | DS1 | Diagnóstico |
| CSAT médio (IC 95%) | média das notas dos fechados | DS1 | Satisfação |
| Poder explicativo do CSAT | R² e R² ajustado (70 variáveis) | DS1 | Satisfação |
| Horas/ano em manuseio | volume × min/ticket ÷ 60 | brief + benchmark | Desperdício |
| R$/ano em manuseio | horas × R$/h | benchmark | Desperdício |
| % automatizável (nível 1) | share do nível 1 no holdout | DS2 | Automação, ROI |
| Precisão do nível 1 | acertos / nível 1 | DS2 | Automação (hero) |
| Economia nível 1 | horas × % elegível DS1 × % nível 1 | DS1 × DS2 | ROI (hero do resumo) |
| Acurácia ao vivo | previsto = real nas triagens do holdout | `triage_runs` | Operação |
| Aprovação sem edição | approved / decididos | `hitl_queue` | Operação |

**M1** Falta algum KPI que o Diretor pediria?
→ Sugestão: **custo por ticket antes × depois** (R$ 3,05 → ?) e **FTE liberados** (6,2 atendentes → ?).

**M2 ★ Elegibilidade do DS1 para automação:** a ponte usa 44,4% elegíveis (excluindo reembolso, cancelamento e Critical, ADR-0010). Confirma que esses tipos ficam fora do automático na história do DS1?
→ Sugestão: **confirmar** (já está na ADR-0005/0010).

---

## N. Escopo, prioridade e definição de pronto (timebox: hoje à noite)

**N1 ★ MoSCoW proposto:**
- **Must:** Resumo · Diagnóstico (3 abas + confiabilidade) · Automação (fluxo, níveis, curva, o que não automatizar) · Console (sortear + texto livre + resultado) · Fila (aprovar/editar/rejeitar) · Caixa · `/api/heartbeat` + cron · deploy.
- **Should:** Operação · fallback offline · rate limit · toggle escuro · deep links · efeito "aprendeu".
- **Could:** Tour guiado · "Como foi feito" lendo os `.md` · matriz de confusão interativa · testes e2e.
- **Won't (agora):** login, Realtime, Slack real, edição do playbook pela UI, tabela crua do DS1.

→ Concorda com os cortes? O que sobe ou desce?

**N2 Definição de pronto:** deploy em produção + 1 ticket de cada nível pelo console ao vivo + fila e caixa refletindo + Lighthouse ≥ 90 em acessibilidade + README com link?
→ Sugestão: **sim.**

**N3 Ordem de construção:**
→ Sugestão:
1. Esqueleto + tema;
2. Console + rotas de API (prova que funciona);
3. Fila + caixa;
4. Diagnóstico;
5. Automação;
6. Resumo;
7. Operação;
8. Polimento.

O console vem primeiro porque é o "me mostre que funciona" do Diretor.

**N4 Quem constrói:** a IA nesta sessão, ou dividir em sessões paralelas (ex.: uma para diagnóstico/automação, estáticos, e outra para console/fila/caixa, ao vivo)?
→ Sugestão: **duas frentes paralelas** depois do esqueleto e do tema prontos, em worktrees separados, porque não tocam os mesmos arquivos.

---

## O. Dados de demonstração e higiene

**O1 Triagens de teste já gravadas** (#1–#6, incluindo a #1 do bug): manter como histórico ou limpar antes do deploy?
→ Sugestão: **limpar antes da gravação do vídeo**, com um script versionado `scripts/reset_demo.py`, mantendo o playbook e a solução aprendida #15 (ou não?).

**O2 Botão "Restaurar demonstração"** no app (recria 2–3 itens na fila e alertas na caixa)?
→ Sugestão: **sim**, só no servidor e protegido por limite de uso. Garante que o avaliador sempre encontre a fila com algo.

**O3 Pré-popular a fila** com alguns rascunhos reais (rodar 5–10 tickets do holdout de nível 2 antes do deploy)?
→ Sugestão: **sim**, custa centavos e deixa a demo rica.

---

## P. Perguntas abertas para você

**P1** Há algo do G4 (vaga, cultura, produtos) que você quer que a interface evoque, além do design system?
**P2** Quer que o app tenha uma página "Sobre mim / por que eu" ou isso fica só no README e no vídeo?
**P3** O vídeo vai ser gravado navegando no app? Se sim, o roteiro guia a ordem das páginas (N3/L4).
**P4** Algum número ou gráfico que você **não** quer mostrar (por exemplo, o TF-IDF acima do RAG)?
→ Sugestão: **mostrar**. Transparência sobre a escolha é ponto a favor.
**P5** Existe prazo de corte de escopo hoje (ex.: "às 23h para de construir e vai para vídeo e PR")?
