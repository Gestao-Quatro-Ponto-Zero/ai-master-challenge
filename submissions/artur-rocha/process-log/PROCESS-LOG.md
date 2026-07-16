# Process Log: como eu usei IA neste desafio

Challenge 001 (Diagnóstico de Churn) · Artur Rocha

Este documento é uma narrativa escrita do processo real, na ordem em que aconteceu, com as evidências apontadas em cada etapa. Não é uma reconstrução bonita: inclui os erros da IA, os meus erros, e as correções. O trabalho todo foi feito em pares: eu dirigindo e julgando, o Claude Code (Anthropic) executando e orquestrando subagentes.

## Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (Opus 4.8 e depois Fable 5) | Orquestrador central: análise de dados em Python, subagentes, relatório, revisão |
| Subagentes do Claude Code (4) | 2 exploradores (leram o repositório do desafio em paralelo), 1 cético adversarial (tentou refutar meu achado central), 1 pesquisador de mercado (causas de churn com fontes) |
| Python (pandas, scikit-learn, scipy, matplotlib) | Joins das 5 tabelas, testes estatísticos, modelos, gráficos. Tudo em scripts reproduzíveis em `solution/scripts/` |
| Skill de visualização de dados | Paleta validada (contraste e daltonismo) para os gráficos do relatório |

Custo de API: zero. Tudo rodou em assinatura e bibliotecas locais.

## Como eu decompus o problema antes de promptar

Antes de tocar em dados, eu li o repositório inteiro do desafio (dois subagentes em paralelo: um mapeou regras, formato de submissão e critérios; outro dissecou os 4 desafios). A decisão de escolher este desafio foi deliberada: o brief entrega um paradoxo declarado pelo CEO ("satisfação ok, uso cresceu, churn subiu") que um LLM cru não resolve, então era onde julgamento abriria mais distância do baseline.

A decomposição que eu defini para a análise:

1. Testar as 3 afirmações do CEO contra os números (não aceitar o enunciado como verdade)
2. Procurar a causa raiz cruzando as 5 tabelas, com teste de significância (não com correlação solta)
3. Medir se churn é sequer previsível (modelo com validação cruzada, sob 2 rótulos)
4. Pesar o churn por receita, não por contagem
5. Tentar destruir as próprias conclusões antes de escrever o relatório

## Workflow passo a passo (com as iterações)

1. **Leitura do repositório** (2 subagentes em paralelo). Saída: regras, critérios, e o ranking dos 4 desafios.
2. **Perfil das 5 tabelas** (`01_explore_and_claims.py`). Primeiro achado: as afirmações do CEO caíram. "Uso cresceu" é falso (estagnado), "satisfação ok" é um sinal cego (3,98 vs 3,96 entre quem saiu e quem ficou).
3. **Causa raiz com rigor** (`02_rootcause_clean.py`). As correlações que pareciam fortes (DevTools 31%, canal "event" 34%) não passaram no qui-quadrado. Nenhum sinal numérico distingue churned de retained.
4. **Stress-test preditivo** (`03_predictive_stresstest.py`). LogReg e RandomForest, validação cruzada 5-fold, sob os 2 rótulos de churn: AUC entre 0,47 e 0,54. Churn é imprevisível nesses dados. Esse virou o achado central.
5. **Verificação adversarial** (subagente cético, prompt: "tente refutar"). Ele foi além de mim: uso por feature, tenure, trajetória ancorada na data real do churn, Bonferroni, teste de permutação, análise de poder. Veredicto: não refutou, e fortaleceu (qualquer sinal útil teria sido detectado; a ausência é genuína).
6. **Receita e watchlist** (`04_revenue_and_watchlist.py`). Como churn é imprevisível, recusei entregar "score de risco" e ranqueei por receita em risco.
7. **Correção de rota humana nº 1 (a mais importante).** Eu, Artur, apontei que a análise inteira olhava só número e ignorava o fator humano das mecânicas de redução de churn. Também levantei a hipótese do build vs buy com IA (empresas cancelando SaaS para construir interno com vibe coding) e exigi que ela fosse condicionada ao ICP. Em resposta: lemos a voz do cliente nos dados (`07_human_voice.py`, que revelou que os reason codes não batem com o texto livre do cliente e que 20% cancelou logo após upgrade), rodamos pesquisa de mercado com fontes (subagente pesquisador, redirecionado no meio do voo para incluir build vs buy) e cruzamos ICP com churn (`08_icp_buildvsbuy.py`: DevTools churna 31% e tem as menores contas).
8. **Relatório executivo** (`05_charts.py`, `06_build_report.py`). Sete seções, primeira pessoa, gráficos com paleta validada.
9. **Revisão adversarial final.** Ataquei o próprio trabalho como um avaliador atacaria. Pegou 3 problemas reais (abaixo) que foram corrigidos antes da entrega.
10. **Grader de olhos frescos.** Um quinto subagente, que nunca tinha visto o trabalho, avaliou a submissão como um avaliador da G4, rodando os scripts para conferir os números. Deu nota A- e apontou os gaps que separavam do A+: a verificação adversarial não tinha script no repositório (só a palavra do subagente), dois números estavam hardcoded no gerador do relatório, os scripts usavam caminhos absolutos da minha máquina, e faltava traduzir o impacto para dólares. Todos corrigidos: nasceram os scripts 09 (reproduz Bonferroni, permutação e análise de poder dentro do repo) e 10 (robustez do método de MRR + cenários de retorno em dólares), o `requirements.txt`, e os caminhos relativos.

Total: 10 scripts, 5 subagentes, 4 versões do relatório, e mais de 12 iterações significativas entre mim e a IA.

## Onde a IA errou e como foi corrigido

1. **Tabela mestre inflada.** O primeiro join produziu 748 linhas para 500 contas (o merge com churn_events duplicava contas com múltiplos eventos). O próprio Claude pegou o erro ao validar contagens e refez com `assert len(m)==500`.
2. **Visão de túnel numérica (o erro mais importante, quem pegou fui eu).** A IA provou "os dados não explicam o churn" e ia parar aí. Faltava a leitura de que churn é fenômeno humano e que a redução dele é uma disciplina humana (champion, onboarding até o valor, conversa de saída, build vs buy). Sem essa correção, o relatório seria estatisticamente correto e estrategicamente vazio.
3. **Linguagem com cara de IA.** O primeiro relatório usava travessões e voz impessoal nas Limitações. Eu exigi primeira pessoa e zero travessão. O texto inteiro foi reescrito e o script passou a ter um `assert` que falha se houver travessão.
4. **Método de MRR não declarado.** A revisão final descobriu que todas as 500 contas têm múltiplas assinaturas "ativas" simultâneas (a tabela nunca fecha registros), então o MRR dependia de uma escolha de método que o relatório apresentava como fato. Corrigido: método declarado, robustez testada nos dois métodos (a fatia de receita churnada fica em 20 a 21% em ambos) e o problema virou evidência extra do achado "rastreamento quebrado".
5. **Churn sem base temporal.** "22%" era acumulado de 2 anos sendo lido como taxa anual. Corrigido para "22% em 2 anos, cerca de 12% ao ano".
6. **Detalhes visuais.** Rótulo colidindo com barra no gráfico de AUC e título cortado no gráfico de ICP, pegos ao inspecionar os PNGs renderizados, corrigidos.
7. **O relatório afirmava sem provar dentro do repo.** O grader de olhos frescos pegou a ironia: a submissão exigia dos dados da RavenStack uma prova que ela mesma não entregava (os números da verificação adversarial citados sem script, valores hardcoded, caminhos absolutos). A correção virou os scripts 09 e 10, e o relatório passou a citar somente números que qualquer avaliador reproduz com um comando.

## O que eu adicionei que a IA sozinha não faria

- **O fator humano como tese.** A IA achou o vazio (AUC 0,50); eu dei o significado: se o porquê não está na telemetria, ele é humano, e a solução é cobertura de sinal humano, não um modelo melhor. A pesquisa de mercado confirmou depois (champion que sai = 51% de churn, invisível no produto).
- **A hipótese build vs buy com IA**, que eu conheço por viver esse mercado: empresas (mais nos EUA) cancelando SaaS para construir interno com vibe coding. E a exigência metodológica de só considerá-la depois de analisar o ICP exposto. O dado sustentou de forma direcional (DevTools: maior churn, menor ticket) e entrou no relatório com a honestidade certa (aposta informada, não conclusão).
- **A proposta de NPS proativo + CS "anjo"**, escalonada por valor para o custo não engolir a cauda longa. A IA refinou com a evidência de que NPS sozinho prevê pouco e precisa vir emparelhado com health score relacional.
- **O padrão de qualidade de comunicação**: primeira pessoa, sem linguagem de IA, honestidade explícita nas limitações.
- **A decisão estratégica** de resolver este desafio primeiro e manter um segundo como reserva, e de que a entrega precisava superar o baseline por julgamento, não por volume.

## Evidências

- **Scripts reproduzíveis**: `solution/scripts/01` a `10` (a ordem dos arquivos é a ordem real do trabalho; caminhos relativos e `requirements.txt` na raiz; rodar na sequência reproduz os números do relatório)
- **Git history**: commits neste repositório documentam a evolução, incluindo a reconstrução pós-revisão
- **Saídas intermediárias**: `solution/outputs/` (tabela mestre, watchlists, gráficos)
- **Relatório final**: `solution/report.html`
