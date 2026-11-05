# Submissão — Erick M. Cormack — Challenge 003

## Sobre mim

- **Nome:** Erick M. Cormack
- **LinkedIn:** (https://www.linkedin.com/in/erick-cormack-msc-00112822/)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí o **Lead Scorer**, uma ferramenta web publicada que mostra ao vendedor, toda segunda-feira, onde focar. Ela roda sobre os dados reais do CRM, carregados num banco Supabase, com o score calculado em SQL auditável. Antes de construir, analisei os 8.800 deals e descobri que **produto, setor, região e vendedor não preveem se um deal fecha**: nenhum teste passou do acaso, e o backtest sem vazamento deu AUC abaixo de 0,5. O que prevê é o **tempo**: as perdas se concentram nas duas primeiras semanas, e **nenhum deal fechou depois de 138 dias**. Hoje, **81% dos deals em negociação (US$ 3,2 milhões, 64% do valor em aberto) já passaram desse limite**. Minha principal recomendação é limpar o pipeline e concentrar o time nos 298 deals ainda vivos, ordenados por valor esperado, que é exatamente o que a ferramenta faz.

- **App publicado:** https://lead-scorer-g4.lovable.app
  - **Acesso:** e-mail `recrutamentog4@g4club.com.br`, senha `G4Lead#2026` (válido até 20/11/2026)
- **Resumo executivo para C-level:** [`docs/resumo_executivo.md`](docs/resumo_executivo.md) (também dentro do app, no botão "Detalhar mais")
- **Análise completa:** [`analise/analise_exploratoria.ipynb`](analise/analise_exploratoria.ipynb) (versão HTML ao lado)
- **Passo a passo detalhado de tudo o que foi feito:** [`PASSO_A_PASSO.md`](PASSO_A_PASSO.md)

---

## Solução

### Abordagem

1. **Entender antes de construir.** Li o brief e a dor da Head de RevOps: os vendedores gastam tempo em deals que não vão fechar e deixam boas oportunidades esfriarem. Antes de escrever qualquer linha do app, fiz uma análise exploratória completa em Pandas.
2. **Desconfiar dos padrões óbvios.** Todo padrão foi testado contra o acaso (intervalo de confiança de Wilson, qui-quadrado, simulação binomial) e contra o futuro, com um backtest sem vazamento que usa só o que se sabia antes de cada deal.
3. **Desenhar a regra a partir do que os dados sustentam**, e não do que "parece fazer sentido". A chance vem só do tempo; o impacto vem do valor.
4. **Colocar a lógica no banco, em SQL auditável**, com parâmetros editáveis. O app só lê e explica.
5. **Conferir o resultado contra um gabarito independente.** Reimplementei o score em Pandas e comparei com o banco e com a URL publicada.

### Resultados / Findings

**1. Qualidade dos dados**

- `GTXPro` no pipeline × `GTX Pro` no catálogo (1.480 deals), setor `technolgy` e país `Philipines`. Corrigi os três na limpeza.
- **1.425 de 2.089 deals abertos (68%) não têm conta cadastrada.** A falha aparece em todos os managers (66% a 70%), então é processo, não pessoa.
- 5 vendedores cadastrados não têm nenhum deal.
- Regras de negócio consistentes: ganho com valor > 0, perdido com valor 0, fechamento depois do engajamento, sem IDs duplicados.
- Erros que só apareceram na análise de robustez: a conta Condax tem `year_established = 2017`, mas deals desde nov/2016; e há **27 grupos (64 deals) com mesmo vendedor, produto, conta e data de engajamento**, 13 deles com Won e Lost no mesmo grupo (provável duplicidade).
- **Indícios de dataset sintético:** engajamentos em volume igual nos 7 dias da semana, inclusive fins de semana, e desconto que é ruído normal puro (KS p = 0,57).
- Data de referência do snapshot: **31/12/2017**.

**2. O que NÃO prevê se um deal fecha**

| Teste                                                                                                                       | Resultado                                                                      |
| --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Taxa de ganho por produto, setor, região e manager                                                                          | Todas entre ~60% e 65% (média 63,2%); qui² p = 0,37 / 0,97 / 0,60 / 0,79       |
| Diferença entre vendedores (55% a 70%)                                                                                      | Compatível com acaso: simulação com 10 mil sorteios, p = 31%                   |
| Backtest sem vazamento (abr–dez/2017) com taxas históricas de vendedor, conta, produto, vendedor × produto, setor e manager | AUC entre 0,457 e 0,482, com o IC inteiro **abaixo** de 0,5 (reversão à média) |
| Machine learning com split temporal                                                                                         | Regressão logística AUC 0,529; gradient boosting 0,512                         |
| Regressão logística inferencial (produto + setor + região + receita + idade da conta + subsidiária)                         | Nenhum coeficiente significativo; teste LR p = 0,82; pseudo-R² 0,0016          |
| Correlações com o ganho                                                                                                     | Todas com \|Spearman\| < 0,02 e V de Cramér ≤ 0,07                             |

Conclusão: um score do tipo "esse vendedor ou setor costuma ganhar" pareceria inteligente no dashboard, mas estaria ordenando ruído.

**3. O que tem sinal**

- **Tempo.** A mediana do ciclo dos perdidos é 14 dias, contra 57 dos ganhos. Fechar em até 14 dias tem odds ratio de 0,57 (IC 0,51–0,63). A chance de ganho de quem já sobreviveu sobe: **63% no dia zero → 69% após 14 dias → 76% após 120 dias**.
- **Teto de 138 dias.** Nenhum deal da história fechou depois disso (p90 = 104 dias). Testei se era efeito de censura: as 9 coortes com mais de 200 dias de observação (4.365 deals) também têm ciclo máximo de 138, e 716 deals delas continuam abertos.
- **Valor.** O preço de lista é um ótimo substituto do valor fechado (mediana fechado ÷ lista = 1,00) e varia de US$ 55 a US$ 26.768, quase 500 vezes. Como a chance é parecida entre produtos, o valor é o principal diferenciador de prioridade.
- **Fim de trimestre.** 81% de ganho no 3º mês, contra ~50% nos outros. Não entra no score, porque depende da data de fechamento, que só existe depois que o deal fecha.

**4. O pipeline aberto em 31/12/2017**

| Indicador                                    | Número                                         |
| -------------------------------------------- | ---------------------------------------------- |
| Deals em negociação acima de 138 dias        | 1.291 de 1.589 (81%)                           |
| Valor de lista travado nesses deals          | US$ 3.198.664 de US$ 4.966.215 em aberto (64%) |
| Deals em negociação ainda vivos              | 298, com US$ 693.565 de valor de lista         |
| Deals vivos na reta final (104 dias ou mais) | 151 de 298                                     |
| Prospecting (ainda sem engajamento)          | 500                                            |

**Anomalia do escritório Central.** Minha primeira hipótese foi que o Central era mais disciplinado, por ter menos deals parados. Estava errada. Todos os 500 deals em Prospecting são dele, o que diluía o percentual. **99% do Engaging aberto do Central está parado**, e todo ele foi engajado num bloco de cerca de 4 semanas em jul–ago/2017, enquanto o mesmo time fechava normalmente os deals de set–out. Tem cara de importação em lote ou campanha que nunca foi trabalhada.

**Outros pontos de atenção**

- 80 deals ganhos (1,9%) foram vendidos acima de 120% do preço de lista, e 92 abaixo de 80%.
- Darcel Schlecht tem 747 deals (2,7 vezes a mediana), com taxa de ganho igual à média.
- O GTK 500 só foi vendido por 6 dos 30 vendedores, e dois deles concentram 29 dos 40 deals.
- Contas grandes geram mais deals (Spearman 0,59), mas não ganham mais (−0,01).

**5. A ferramenta: Lead Scorer**

App publicado em https://lead-scorer-g4.lovable.app, com a identidade visual do G4 (azul-marinho, dourado, Playfair Display e Archivo) e acesso por login exclusivo para a avaliação. São três telas:

- **Início:** resumo executivo em destaque, com o botão "Detalhar mais" que abre a análise completa; três cartões explicando como o score funciona; a curva de chance por idade; e gráficos de deals por fila, valor esperado por região e distribuição do score.
- **Meu pipeline:** cartões de resumo e três filas de ação, com filtros em cascata por região, manager e vendedor, guardados na URL:
  - **Focar agora**, com os deals vivos ordenados por score;
  - **Requalificar ou encerrar**, com os parados acima de 138 dias;
  - **Prospectar**, com os ainda não engajados, por valor.

  Cada deal abre um painel **"Por que este score"**, com os motivos em texto, a conta do valor esperado, a posição do deal na curva e o contexto da conta (que não entra no score). A tela tem ainda um gráfico de valor esperado por manager, paginação de 25 em 25 e exportação em PDF e XLSX do recorte filtrado.

- **Visão do gestor:** números por vendedor, com destaque quando mais de 70% da carteira aberta está parada, também com exportação em PDF e XLSX.

**Como o score funciona**

1. **Fila.** Won e Lost ficam fora. Prospecting vai para "Prospectar". Engaging com mais de 138 dias vai para "Requalificar ou encerrar". O resto vai para "Focar agora".
2. **Chance** = probabilidade de ganho de um deal que já sobreviveu aquela idade, calculada a partir dos deals fechados. Na cauda com menos de 100 deals, repito o último valor confiável.
3. **Valor esperado** = chance × preço de lista.
4. **Score de 0 a 100** = valor esperado em escala logarítmica dentro da fila. Uso log porque o valor varia ~500 vezes entre produtos; em escala linear, quase tudo ficaria perto de zero.
5. **Motivos em texto**, prazo limite (dia 138), momento do deal (fase de risco, em andamento ou reta final) e alertas de conta não cadastrada e de possível duplicata.

Vendedor, produto e setor aparecem só como contexto, com uma nota explicando por quê.

**Conferência rápida:** depois do login, com todos os filtros em "Todos", as abas mostram Focar 298, Requalificar 1.291 e Prospectar 500, e o valor esperado em foco é US$ 505.216. O primeiro do ranking é o deal 1LY8CAXD (GTK 500, 95 dias, 71% de chance, US$ 18.912). Os mesmos números saem de `python scripts/gabarito_score.py`.

### Recomendações

1. **Limpar o pipeline em até duas semanas.** Cada vendedor requalifica ou encerra os 1.291 deals parados há mais de 138 dias, começando pelo Central. Antes disso, a gestão precisa entender o que aconteceu com o lote de julho do Central.
2. **Usar a fila "Focar agora" toda segunda-feira**, atacando primeiro os 151 deals na reta final.
3. **Tornar obrigatório o cadastro da conta no CRM.** Sem ele, não dá para analisar setor ou porte em dois terços do pipeline.
4. **Registrar as atividades de venda** (reuniões, e-mails, propostas e mudanças de estágio). É o dado que mais falta para um score mais preditivo.
5. **Revisar casos pontuais:** os 27 grupos de prováveis duplicatas e as 80 vendas acima de 120% do preço de lista.
6. **Tratar qualquer previsão de receita feita sobre o pipeline atual como inflada** até a limpeza: dois terços do valor em aberto estão em deals fora de qualquer padrão histórico.

### Limitações

- **O dataset parece sintético.** Com dados reais, é provável que vendedor e conta ganhem algum poder preditivo. A regra precisa ser reavaliada, e os parâmetros já ficam numa tabela editável para isso.
- **A curva de chance usa só deals fechados.** Com dados contínuos, o correto é um modelo de sobrevivência com censura (Kaplan-Meier ou Cox), idealmente por produto.
- **O corte de 138 dias é empírico.** Ele se sustentou contra a censura, mas deve ser recalculado com o tempo.
- **Não há histórico de atividades nem de mudança de estágio**, que costumam ser os sinais mais fortes em CRMs reais.
- **O app é somente leitura** e não escreve de volta no CRM. Para uso real, faltam integração com o CRM (webhook ou sync agendado) e um login por vendedor, com cada um vendo só a própria carteira.
- **O login atual é uma credencial única para a avaliação**, e a validade de 15 dias é controlada pelo próprio app. Os dados do banco continuam com leitura pública, porque o dataset é público.
- **Não testei com usuários reais**, então a usabilidade das telas ainda não foi validada com vendedores.

---

## Process Log — Como usei IA

1. Inicialmente busquei entender o Github enviado com seus repositórios e desafios propostos
2. Assim, defini que usaria o Claude Code com uma pasta projeto contemplando todos os dados disponilibizados via Kaggle
3. Após análise inicial, solicitei que fizesse mais perguntas aos dados, buscando outliers, convergências ou regressão visto meu conhecimento em análise quanti e quali.
4. Verificações feitas me fizeram criar no Lovable usando o Claude Code conectado a ele, um Web Site publicado com os dados no Lovable Cloud (Supabase), no qual o Claude criou as querys e fui conferindo uma a uma
5. Criei a camada de segunrança com login e senha e data de expiração, e feito refino do site para envio ao recrutadores do G4

### Ferramentas usadas

| Ferramenta                                            | Para que usei                                                                                                                                                                               |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude (Opus, no claude.ai com ferramentas de código) | Leitura do desafio, análise exploratória em Pandas, testes estatísticos, desenho do score, SQL do banco, condução do agente do Lovable, verificação e documentação                          |
| Lovable (agente)                                      | Construção do front-end a partir de uma especificação detalhada e, depois, evoluções que eu mesmo pedi no editor: identidade G4, login, resumo executivo, gráficos, paginação e exportações |
| Lovable Cloud (Supabase)                              | Banco Postgres, carga dos dados via `pg_net` e score em views SQL                                                                                                                           |
| Navegador embutido do Claude                          | Teste da URL publicada (cartões, ranking, painel e visão do gestor)                                                                                                                         |

### Workflow

1. **Escolha do desafio.** Pedi ao Claude um resumo dos challenges 001 e 003, que combinam com meu perfil. Escolhi o 003 porque o entregável é software funcionando, e defini a stack Lovable + Supabase, que já uso no dia a dia.
2. **Dados.** O Kaggle estava bloqueado no ambiente, então usei um espelho público no GitHub e validei pelas contagens do README do desafio.
3. **Análise antes da ferramenta.** Os primeiros números já mostravam taxas de ganho planas. Em vez de partir para o app, pedi uma análise detalhada em notebook, com 12 etapas.
4. **Robustez estatística.** Pedi uma etapa extra com estatística descritiva, outliers, possíveis erros, censura, correlações e regressão inferencial. Ela confirmou o teto de 138 dias e revelou erros de cadastro.
5. **Resumo executivo** de uma página para C-level, num doc.
6. **Banco.** Esquema, carga e score em SQL, conferidos contra um gabarito independente em Pandas e com o MD5 dos arquivos baixados pelo próprio banco.
7. **App.** O Claude mandou uma especificação detalhada ao agente do Lovable, revisou o código gerado, achou bugs e pediu correções com casos de teste numéricos. Autorizei a publicação.
8. **Verificação final na URL pública**, contra o banco e o gabarito.
9. **Evolução do produto direto no Lovable.** Depois da primeira publicação, mandei 10 mensagens ao agente do Lovable pelo editor: identidade visual do G4, login com validade de 15 dias para os avaliadores, resumo executivo e mais gráficos na página inicial, números mais legíveis, paginação, botão "Detalhar mais" com a análise completa, gráfico de valor esperado por manager e exportação em PDF e XLSX respeitando os filtros.

O passo a passo completo, com cada etapa da análise, cada comando SQL e cada prompt, está em [`PASSO_A_PASSO.md`](PASSO_A_PASSO.md).

Custo do agente do Lovable na construção: cerca de 15 créditos em 3 mensagens (estrutura 1,3 + telas 9,7 + correções 3,8). O histórico completo, com as 13 mensagens, está em [`docs/lovable_prompts.md`](docs/lovable_prompts.md).

### Onde a IA errou e como corrigi

| Erro                                                                                                          | Como foi pego                                   | Correção                                                                                                       |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Textos de leitura do notebook escritos antes dos números: diziam que todos os ICs de AUC cruzavam 0,5         | Conferência célula a célula das saídas          | Os ICs ficam **abaixo** de 0,5 (reversão à média); texto reescrito                                             |
| Regressão logística sem convergir                                                                             | Aviso de convergência na saída                  | Padronização das variáveis numéricas                                                                           |
| "Todos os países cruzam a média"                                                                              | Tabela de ICs                                   | O Panamá não cruza; adicionei a nota sobre comparações múltiplas                                               |
| Hipótese "o Central é mais disciplinado"                                                                      | Abertura por região                             | Era o contrário: o Prospecting diluía a taxa, e 99% do Engaging do Central está parado                         |
| "4% vendidos acima de 120% do preço"                                                                          | Conferência com a saída                         | O certo é 1,9% (80 deals)                                                                                      |
| Rótulos sobrepostos em gráficos                                                                               | Inspeção visual dos PNGs                        | Reposicionamento                                                                                               |
| Carga planejada com a extensão `http`                                                                         | Erro do Lovable Cloud (extensão não suportada)  | Troca para `pg_net` (assíncrona), com MD5 conferido                                                            |
| Motivo "Faltam 0 dias"                                                                                        | Leitura dos textos gerados pelo SQL             | Mensagem específica para o último dia                                                                          |
| Agente do Lovable: a curva despencava para 0% no dia 138 (`p_ganho` nulo virava 0) e mostrava a cauda ruidosa | Screenshot do app e leitura do `CurvaChart.tsx` | Linha sólida só com amostra ≥ 100, tracejada no valor que o score usa, e marcador com a chance do próprio deal |
| Agente do Lovable: limite de 138 dias fixo no código                                                          | Revisão do código                               | Parâmetros lidos da tabela `parametros`                                                                        |
| Agente do Lovable declarou pronto sem testar filtros                                                          | Leitura do relatório do próprio agente          | Testes com números esperados calculados antes (Central 5/403/500; Darcel 0/83/111), e bateram                  |
| Valores nos motivos com separador americano (US$ 18,912)                                                      | Inspeção do painel na URL publicada             | Formatação pt-BR na view SQL                                                                                   |
| Agente do Lovable não conseguiu ler o resumo executivo pelo link (a página exige login)                       | Resposta do próprio agente                      | Colei o conteúdo em Markdown direto no chat do Lovable                                                         |

### O que eu adicionei que a IA sozinha não faria

- **Análise e verificação antes de construir.** Exigi entender os dados antes de abrir o Lovable. O desenho por filas de ação nasceu disso, e não de um template de "lead score".
- **Pedido explícito de robustez estatística** (outliers, descritiva e inferência). Foi isso que validou o teto de 138 dias contra a censura e revelou a Condax e os prováveis duplicados.
- **Recusa do score "bonito".** Vendedor, produto e setor não entram como peso, mesmo sendo o caminho óbvio, porque o backtest mostrou que não preveem. No app, eles aparecem como contexto, com a explicação.
- **Leitura de negócio dos números.** O caso do Central virou uma pergunta para a gestão ("o que aconteceu em julho?"), e a recomendação principal é de gestão (limpar o pipeline), não de tecnologia.
- **Comunicação em dois níveis:** notebook para o time técnico e resumo de uma página para o C-level.
- **Escolha de stack e custo:** Lovable + Supabase, que eu já domino, com a lógica no banco para não depender do código gerado pelo agente. A IA recomendava Python + página web; mantive minha escolha.
- **Olhar de produto depois da primeira versão.** Pedi direto no Lovable o que o vendedor e o gestor precisariam para usar de verdade: identidade visual do G4, login para os avaliadores, resumo executivo dentro do app, gráfico por manager, paginação e exportação em PDF e XLSX respeitando os filtros.

---

## Evidências

- [x] Notebook comentado e executado (`analise/`)
- [x] Scripts e SQL versionados (`scripts/`, `sql/`)
- [x] Prompts e respostas do agente do Lovable, com as 13 mensagens (`docs/lovable_prompts.md`)
- [x] Passo a passo completo do processo ([`PASSO_A_PASSO.md`](PASSO_A_PASSO.md))
- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Chat exports ([`docs/chat_export.md`](docs/chat_export.md) + link oficial da conversa: _[preencher]_)
- [ ] Git history
- [x] Outro: app publicado em https://lead-scorer-g4.lovable.app e resumo executivo em [`docs/resumo_executivo.md`](docs/resumo_executivo.md)

---

_Submissão enviada em: 05/11/2026
