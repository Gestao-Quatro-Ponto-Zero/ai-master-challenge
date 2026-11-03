# Process log: como usei a IA

**Papéis.** Eu decidi o que fazer, em que ordem e o que entra na entrega, e aprovei cada documento. A IA (Claude Code, com o Claude Opus 5.5) leu os dados, mediu, escreveu os scripts, rodou os testes e redigiu, registrando cada passo no [audit trail](002-audit-trail.md). As mensagens trocadas estão no [chat export](chat-exports/001-chat-export.md).

## 1. Ferramentas e por quê

| Ferramenta | Por quê | Onde entrou |
|---|---|---|
| Claude Code (Claude Opus 5.5) | Agente no terminal que lê e escreve arquivos e roda scripts: permite medir em vez de supor | Todo o trabalho |
| Segunda sessão do Claude Code (Claude Opus 5.5) | Uma leitura de fora do andamento | Estratégia e revisão (seção 8) |
| OpenRouter | Uma chave para vários fornecedores, com limite de gasto | Zero-shot e IA generativa |
| Embeddings da OpenAI (text-embedding-3-large) | Dica do desafio (embeddings + zero-shot) e semelhança por sentido | Zero-shot, grupos de problema, quase duplicatas, teste de sentido da resolução |
| Jev 1.14 (TypeSafe) | Modelo de decisão entre opções, que sugeri avaliar | Zero-shot por decisão |
| Claude Opus 5.5, pelo OpenRouter | Primeiro teste da IA generativa | Trocado por ser superdimensionado (item 180) |
| GLM 5.3 Flash | Custo: US$ 0,0285 por milhão de tokens de entrada e US$ 0,0923 de saída | IA generativa do protótipo |
| scikit-learn, SciPy e pandas | Classificador e testes estatísticos locais, sem custo | Diagnóstico, classificador e protótipo |
| Streamlit | Página local simples | Protótipo |
| Playwright 1.62.0 e ffmpeg | Prints e vídeo automatizados | Embalagem da submissão |

**Custo de API:** US$ 1,89 no OpenRouter, conferido na chave em 2026-11-03. É a soma de todas as coletas, testes e rascunhos do projeto.

## 2. Como decompus o problema antes de promptar

- **Espinha:** as 4 entregas do desafio e as 3 perguntas do Diretor (onde o fluxo trava, o que impacta o CSAT, quanto se desperdiça).
- **Uma etapa de cada vez:** a IA apresenta o plano ou as opções, com custo quando há API; eu decido; só então ela executa.
- **Premissas definidas por mim:** os dados são reais, e inconsistências viram hipóteses (item 74); as colunas de tempo do Dataset 1 servem só como marcadores de status (item 95).
- **Regras de trabalho escritas antes de começar** (seção 3), para que cada número viesse de um script e cada passo ficasse registrado.

## 3. Regras que dei à IA

Seção "Regras" do `CLAUDE.md` do projeto, copiada sem alteração. A parte sobre a vaga fica de fora.

- Faça apenas o que eu pedir.
- Nomes de arquivos e pastas em minúsculas com hífen: nome-arquivo.
- Sempre numeramos os arquivos para ordenar.
- 000-readme.md é o índice de todos os arquivos. Mantenha-o atualizado.
- 001-audit-trail.md é o registro de cada passo nosso. Use as colunas: # | Data e hora | Quem | Passo | Por quê | Resultado ou correção.
- Em "Quem", diga se foi eu, a IA, ou se eu pedi e a IA executou.
- No audit trail, registre também cada erro e correção, e as escolhas que forem suas.
- Não faça contas de cabeça. Uma LLM é uma ferramenta estatística, não determinística, e cálculos são determinísticos. Quando precisar calcular ou extrair dados, use um script ou crie uma ferramenta, ainda que temporária.

**Limites**, definidos em 2026-11-01 e válidos até eu dizer o contrário:

| Limite | Situação |
|---|---|
| Não comece o desafio. | Retirado no item 191, quando passamos a preparar a submissão |
| Não faça fork. | Retirado no item 191 |
| Leia o repositório do desafio sem clonar e sem alterar nada nele. | Em vigor; liberado só para clonar o meu fork na etapa do PR (item 196) |

A regra de não fazer contas de cabeça entrou no `CLAUDE.md` depois que a IA calculou porcentagens sem script (itens 49 a 51).

## 4. Workflow

As decisões marcadas com † foram enviadas em mensagens redigidas na segunda sessão do Claude (seção 8). A decisão foi minha em todos os casos.

| Fase | Itens | Quando | O que a IA fez | O que eu decidi |
|---|---|---|---|---|
| Preparação | 1 a 19 | 2026-11-01 | Leu a vaga e o repositório do desafio, só leitura | As regras e os limites |
| Escolha e falso começo | 20 a 37 | 2026-11-01 | Baixou os dados e começou a análise sem pedido; o trabalho foi desfeito | Escolhi o desafio 002; apontei o erro; descartei a avaliação inicial (itens 27 e 33) |
| Dataset 1: o que os dados significam | 38 a 101 | 2026-11-02, manhã | Ferramenta de cálculo, checagem dos segundos, reconstrução do relógio de geração, amostra de tickets e padrões de texto | Proposta, não perguntas (60); fechamento e atendimento como sequência de tentativas, que viraram o docs/003 (62 a 66); dados reais (74); colunas de tempo como marcadores (95) |
| Dataset 2: método | 102 a 133 | 2026-11-02, tarde | Classificador supervisionado (70,8% sozinho com 95% de acerto); zero-shot com embeddings e Jev (43%); por que o zero-shot erra; teste de ligação entre os datasets (V ≤ 0,041) | Avaliar o Dataset 2 como um todo (102); formato da fase 2 (108 †); Jev (110); embeddings da OpenAI (114 e 118); entender a ligação entre os datasets antes de classificar (124, com o alerta da segunda sessão); teste da ligação (131 †) |
| Diagnóstico e proposta | 134 a 171 | 2026-11-02, noite | As três perguntas; docs/004 e docs/005; grupos de problema pelo texto; sinais no texto do Dataset 1; quase duplicatas | Uma única premissa na pergunta 3 (140 †); ressalva dos 70,8% (142 †); limite da foto (144 †); IA generativa com revisão humana e confirmação automática fora da primeira resposta (147 †); grupos pelo texto (150 †); famílias aproximadas e faixa das mensagens padronizadas (152 †); cruzar descrição e resolução (155); não usar o e-mail (169) |
| Protótipo | 172 a 189 | 2026-11-02, noite | Modelo com separação 80/20 e avaliação única no teste; página; testes; exemplos reais da IA generativa; versão 2 dos prompts | Trocar o Claude Opus 5.5 por um modelo econômico (180); exemplos reais e ajustes (182 †); iterar os prompts (184 †); aprovar os 6 textos com 2 correções (186 †) e a regra das aspas (188 †) |
| Submissão | 190 em diante | 2026-11-02 e 03 | Página sem os datasets, prints e GIF automatizados, chat export limpo, README e montagem da pasta | Estrutura e decisões da submissão (193 † e 196) |

## 5. Onde a IA errou e como corrigi

Os 27 itens do audit trail que registram erro da IA, até o item 210:

| Item | Erro da IA | Correção |
|---|---|---|
| 27 | Tratou "vamos fazer o desafio 2" como ordem de começar e fez os itens 21 a 26 sem pedido | Apontei; o trabalho foi desfeito |
| 33 | Apresentou conclusões e recomendação antes de qualquer pedido, com um volume de tickets errado | Conferi os 8.469 tickets; a avaliação inicial foi descartada |
| 41 | Inseriu os itens 38 a 40 acima do 37 no audit trail | Ordem restaurada |
| 49 | Calculou porcentagens e uma margem de acaso de cabeça | Proibi; regra no `CLAUDE.md` e ferramenta de cálculo (itens 50 a 53) |
| 52 | Comando que o zsh não rodou | Função de shell |
| 76 | Disse que uma diferença espalhada por igual entre −24 h e +24 h indicaria ruído | Corrigido: horários sem relação dão pico perto de zero |
| 81 | Contagens impressas com ".0" | Função de impressão corrigida |
| 85 | O zsh tratou o "?" de uma URL como coringa | URL entre aspas |
| 115 | Só considerou modelos Claude para o zero-shot | Perguntei por quê; a pesquisa foi ampliada |
| 119 | Entendeu "o modelo exato da OpenAI" como a Decisions API, sem confirmar | Esclareci que eram os embeddings |
| 134 | Abriu o `.env` a meu pedido sem registrar o passo na hora | Registro tardio, pelo transcript |
| 136 | Estimou os horários a partir do item 108, até 1h28 adiantados e fora de ordem | Corrigidos pelo transcript; `date` antes de cada registro |
| 145 | Afirmou que a prioridade não muda o andamento, sem considerar que os dados são uma foto | A frase virou indício |
| 149 | Item 147 com horário estimado; 140, 142 e 144 com a hora do registro em vez da mensagem | Corrigidos pelo transcript |
| 153 | Seção nova do anexo numerada fora de ordem | Renumerada |
| 159 | Scripts fora de ordem no índice | Reordenação por script |
| 166 | Escreveu "diferenças até 0,35 ponto" fazendo a conta de cabeça | Trocado por um exemplo com valores medidos |
| 170 | Faixas de exemplo com os limites trocados | Corrigido antes de rodar |
| 171 | "91%" no lugar de 90,9% e "{product}" no lugar do marcador original | Corrigidos |
| 173 | Supôs um mínimo de 8 palavras e escreveu no código que era medido | Medido: 5 palavras; comentário reescrito |
| 175 | Índice fora de ordem de novo | Script de reordenação ampliado |
| 177 | Página visível na rede local, com a chave do OpenRouter carregada | Só em 127.0.0.1 |
| 185 | Prompts antigos gravados com o número 010, antes dos exemplos novos | Renomeado para 009 |
| 187 | Registrou uma correção como apontada e aprovada por mim | Passou a extensão da IA a confirmar; confirmei no item 188 |
| 195 | Horários estimados nos itens 194 e 195 | Corrigidos pelo `date` |
| 199 | O mesmo erro no item 198, por rodar o `date` e gravar no mesmo comando | `date` num comando separado |
| 206 | Escreveu, numa resposta que entra no chat export, o nome de uma empresa que a auditoria tinha procurado | Apontei; o script 011 troca o termo, recebido por variável de ambiente, e recusa gravar o export se ele sobrar |

## 6. O que eu acrescentei que a IA sozinha não faria

Decisões e ideias até a declaração do item 190, com a origem de cada uma. "Segunda sessão" quer dizer mensagem redigida lá e enviada por mim, com ou sem ajustes.

| Decisão ou ideia | Item | Origem |
|---|---|---|
| Apontar que a IA começou sem pedido e conferir o volume de tickets | 27 e 33 | Minha |
| Proibir contas de cabeça | 50 | Minha |
| Levar à equipe uma proposta pronta para decisão, não uma lista de perguntas | 60 | Minha |
| Registrar o fechamento e tratar o atendimento como sequência de tentativas | 62 a 66 | Minha |
| Investigar os 1.365 fechados com a resolução antes da primeira resposta | 68 a 72 | Minha |
| Tratar os dados como reais | 74 | Minha |
| Usar as colunas de tempo só como marcadores de status | 95 | Minha |
| Avaliar o Dataset 2 como um todo | 102 | Minha |
| Seguir a dica do desafio na fase 2, com opções e custo antes de executar | 108 | Segunda sessão |
| Avaliar o Jev e os embeddings da OpenAI | 110, 114 e 118 | Minha |
| Entender a ligação entre os datasets antes de classificar | 124 | Minha, com o alerta da segunda sessão |
| Testar a ligação aplicando o modelo ao Dataset 1 | 131 | Segunda sessão |
| Corrigir os horários do audit trail pelo transcript | 135 | Segunda sessão |
| Uma única premissa para o desperdício, a cada 1.000 tickets | 140 | Segunda sessão |
| Deixar claro que os 70,8% foram medidos em outro domínio | 142 | Segunda sessão |
| Incluir o limite da foto na pergunta 1 | 144 | Segunda sessão |
| IA generativa com revisão humana; confirmação automática fora da primeira resposta | 147 | Segunda sessão |
| Grupos de problema só pelo texto | 150 | Segunda sessão |
| Tratar como aproximados os percentuais das famílias e mostrar as mensagens padronizadas como faixa de 3,7% a 12,5% | 152 | Segunda sessão |
| Cruzar a descrição com a resolução no Dataset 1 | 155 | Minha |
| Conferir as entregas contra o desafio, uma a uma | 162 | Minha |
| Não usar o e-mail dos clientes, nem com hash | 169 | Minha |
| Trocar o Claude Opus 5.5 por um modelo econômico na IA generativa | 180 | Minha |
| Gravar exemplos reais da IA generativa | 182 | Segunda sessão |
| Iterar os prompts antes de aprovar | 184 | Segunda sessão |
| Aprovar os textos com duas correções e a regra das aspas | 186 e 188 | Segunda sessão |

## 7. Iterações

- **Audit trail:** até o item 210, 78 itens meus, 56 da IA e 76 pedidos meus executados pela IA; 27 itens registram erro da IA.
- **Classificador:** fase 1 com validação cruzada; fase 2 com duas abordagens zero-shot e a checagem de ordem do Jev; modelo do protótipo com separação 80/20 e uma única avaliação no teste.
- **Conteúdo mínimo do ticket:** 8 palavras supostas, 5 medidas.
- **IA generativa:** 2 modelos (Claude Opus 5.5, depois GLM 5.3 Flash), 2 versões de prompt e 6 textos aprovados, com 2 correções e a regra das aspas.
- **Proposta:** estrutura aprovada com 4 ajustes, depois acréscimos dos grupos de problema, dos sinais no texto do Dataset 1, das quase duplicatas e do limiar por categoria.
- **Página do protótipo:** primeiro visível na rede local, depois só em 127.0.0.1; por fim, sem precisar dos datasets.

## 8. Segunda sessão do Claude

Segunda sessão do Claude. Usei, em paralelo, uma segunda sessão do Claude Code (Claude Opus 5.5) para consultas sobre estratégia e para revisar o andamento desta sessão, lendo o transcript dela. Essa segunda sessão só leu; não alterou nenhum arquivo do projeto. As decisões foram minhas. Parte das mensagens que enviei a esta sessão foi redigida lá e enviada por mim, com ou sem ajustes: as de 17:05, 18:58, 19:07, 19:30, 19:39, 19:41, 19:47, 19:55, 20:05, 20:20, 22:27, 22:32, 22:37 e 22:42 de 2026-11-02 (horário local). Dela vieram principalmente: o formato da fase 2 (seguir a dica de embeddings + zero-shot, com as opções e o custo antes de executar); o alerta sobre o critério de cruzamento dos datasets, que levei na mensagem de 18:01; a redução da pergunta 3 a uma única premissa, a cada 1.000 tickets; a inclusão da IA generativa com revisão humana na proposta; e os pedidos de gravar exemplos reais da IA generativa e de iterar os prompts.

As mensagens de 00:33, de 06:36 e de 06:49 de 2026-11-03 (horário local) também foram redigidas na segunda sessão e enviadas por mim.
