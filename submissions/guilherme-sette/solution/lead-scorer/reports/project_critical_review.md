# Revisao critica do projeto

Data da revisao: 2026-06-23

## Veredito

O projeto esta funcional e acima do minimo do desafio em escopo de produto, mas ainda nao esta pronto como pacote forte de submissao. O risco principal nao e falta de algoritmo: e reprodutibilidade, curadoria da entrega, clareza do README final e explicabilidade operacional dentro da interface.

## Status apos primeira correcao

Itens ja enderecados apos esta revisao:

- `README.md` passou a abrir com a solucao implementada, comandos portaveis e links para artefatos principais.
- `SOLUTION.md` e `data/README.md` deixaram de depender de caminhos absolutos do runtime local.
- `requirements.txt` foi adicionado.
- `PROCESS_LOG.md` foi criado dentro do diretorio do desafio.
- `scripts/validate_outputs.py` foi adicionado e executado com sucesso.
- O front passou a mostrar decomposicao compacta do score por valor, fit, tempo e conta.
- A coluna de especialista foi ajustada para explicitar apoio consultivo vs ownership sujeito a aprovacao.
- `.DS_Store` foi removido do workspace.

Riscos ainda relevantes:

- A transcricao local existe, mas nao e prova perfeita de completude literal sem exportacao oficial do chat.
- O score continua sendo heuristica operacional, nao forecast calibrado.
- A UI ainda nao foi revalidada visualmente por navegador apos os ajustes, por decisao operacional de evitar o processo que causou instabilidade.
- A pasta `reports/` ainda pode ser mais curada antes do PR final.

## Regras usadas como criterio

- O challenge exige software funcionando, dados reais, logica de scoring alem de ordenar por valor e explicacao para vendedor nao tecnico.
- A documentacao minima precisa cobrir setup, logica e limitacoes.
- O process log e obrigatorio na submissao.
- O guardrail local exige manter o projeto dentro do escopo Lead Scorer, com heuristicas pragmaticas e explicaveis, sem vender precisao de ML nao sustentada.
- Untitled UI e referencia visual, nao dependencia obrigatoria.

## Evidencias reproduzidas

- Pipeline de ETL, raio X, fit vendedor-segmento e score rodou sem erro localmente.
- Dados processados:
  - 8.800 oportunidades totais.
  - 6.711 oportunidades fechadas para historico.
  - 2.089 oportunidades abertas para scoring.
  - 1.425 oportunidades abertas sem conta conhecida, ou 68,2%.
- Score aberto:
  - media: 54,7.
  - mediana: 54,7.
  - desvio padrao: 8,3.
  - minimo: 30,5.
  - maximo: 76,8.
- Bandas de prioridade:
  - baixa: 862.
  - revisao: 632.
  - media: 563.
  - alta: 32.
- Sinais de roteamento:
  - manter: 857.
  - corrigir_dados: 384.
  - consultar_especialista: 309.
  - nurture: 269.
  - last_chance: 138.
  - manager_review: 110.
  - remanejar: 22.
- Aprovacoes:
  - 132 deals exigem aprovacao.
  - 110 revisoes gerente.
  - 22 remanejamentos.
- Remanejamento:
  - 22 remanejamentos recomendados.
  - 0 casos em que vendedor atual e recomendado sao iguais.
- Concentracao de especialista recomendado:
  - Hayden Neloms: 1.153 deals.
  - Maureen Marcano: 892 deals.
  - Moses Frase: 44 deals.
  - Total de vendedores recomendados como especialista: 3.
  - Vendedores atuais na carteira aberta: 27.

## Achados criticos originais

Estes achados refletem o estado auditado antes da primeira rodada de correcao listada acima.

### Alto risco original

1. O README principal do desafio ainda e o enunciado, nao o README de submissao.

Um avaliador que abrir `README.md` primeiro vera o desafio original, nao a solucao construida. A solucao esta em `SOLUTION.md`, mas isso depende de o avaliador procurar o arquivo certo. Para submissao por PR, isso e uma fragilidade direta.

2. O setup documentado nao e portavel.

`SOLUTION.md` usava caminhos absolutos do runtime local do Codex. Isso rodava nesta maquina, mas nao era uma instrucao limpa para outro avaliador. `data/README.md` tambem repetia um caminho absoluto.

3. O process log existe fora da pasta do challenge.

A transcricao estava fora do diretorio do desafio e ainda nao existia `PROCESS_LOG.md`, `process_log.md` ou equivalente dentro da pasta de submissao. Como o guia diz que sem process log a submissao e desclassificada, isso precisava ser resolvido antes de PR.

4. O score e explicavel no CSV e no documento, mas ainda nao o suficiente no produto.

A tabela mostra score, sinal, fit e motivos. Porem o usuario nao ve uma decomposicao clara do score por componentes: valor, fit, timing, stage, conta, carteira e confianca. Como o README exige que vendedor entenda por que um deal tem score alto ou baixo, a interface deveria mostrar a composicao do score, nao apenas reason codes textuais.

5. O roteamento visual pode induzir interpretacao errada sobre sobrecarga.

O sistema limita remanejamentos a 22, mas a coluna de especialista mostra recomendacoes concentradas em 3 vendedores. Se a tela nao diferenciar claramente "especialista consultivo" de "novo dono sugerido", o gerente pode ler isso como uma proposta operacional impossivel.

6. Nao ha script formal de validacao.

Os scripts rodam, mas nao existe `scripts/validate_outputs.py` ou comando unico que prove invariantes importantes: row counts, colunas obrigatorias, ausencia de leakage, JSON parseavel, quantidade de aprovacoes, remanejamento com vendedor diferente, etc. Para uma submissao com muitos artefatos gerados, isso enfraquece a confianca.

### Medio risco original

1. A complexidade esta alta para um desafio de 4-6 horas.

Os principais scripts e arquivos de front somam milhares de linhas. Isso pode ser bom se a narrativa explicar o valor, mas tambem pode parecer overengineering. Sem um README muito claro, a complexidade joga contra.

2. Muitos thresholds estao hard-coded.

`HIGH_VALUE_CUTOFF`, gaps de fit, confianca minima, cortes de idade e pesos sao bons para heuristica operacional, mas precisam ser apresentados como politica inicial calibravel. Nao devem parecer parametros estatisticamente otimizados.

3. A normalizacao do valor e relativa ao lote aberto.

O `value_score` usa min-max com log sobre os valores do proprio dataset aberto. Isso e simples, mas em producao o score mudaria quando entrassem novas oportunidades extremas. Para V1 serve; para escala precisaria congelar cortes ou usar quantis historicos.

4. Fit vendedor-produto/empresa/ticket e associativo, nao causal.

O modelo usa historico fechado e uplift suavizado, o que e pragmatico. O risco e confundir "ja recebeu esse tipo de deal" com "e causalmente melhor para esse tipo de deal".

5. Red-flag de vendedor pode virar punicao automatizada.

As regras de baixa performance sao uteis para governanca, mas precisam ficar como sinal de gerente, nao como mecanismo automatico de retirada de oportunidade. O produto atual faz isso de forma razoavelmente conservadora, mas a documentacao deve reforcar.

6. Dados incompletos dominam a decisao.

68,2% das oportunidades abertas sem conta conhecida significa que boa parte do produto vira saneamento de CRM. Isso e uma verdade operacional relevante, mas precisa ser vendida como achado do sistema, nao como falha escondida.

7. A persistencia de aprovacao e apenas `localStorage`.

Serve para demo, mas nao e fluxo real de gerente. A limitacao esta documentada, porem no produto a acao parece mais definitiva do que realmente e.

8. UI tem risco de overflow horizontal.

A tabela usa `min-width: 1180px`. Em validacao anterior antes de interromper o uso do browser, o body ficou maior que o viewport em desktop padrao. Isso nao quebra a demo, mas e friccao real para notebook.

9. O pacote esta ruidoso.

Ha `.DS_Store` dentro da pasta do desafio e varios screenshots intermediarios. Antes de PR, a entrega deveria ser curada para conter apenas evidencias finais e arquivos necessarios.

10. A linguagem mistura portugues e ingles.

Termos como deal, manager, score, red-flag, fit e ownership sao aceitaveis em RevOps, mas a mistura precisa ser intencional. Hoje ela parece parcialmente acidental.

## Pontos fortes

1. Usa dados reais e preserva raw vs processed.
2. Separa oportunidades fechadas para historico e abertas para scoring.
3. Evita leakage obvio no conjunto de treino/scoring.
4. Vai alem de ordenar por valor: combina valor, fit, timing, stage, conta, carteira e confianca.
5. Inclui fit vendedor-segmento e governanca de remanejamento.
6. Tem dois portais coerentes com o uso real: vendedor e gerente.
7. Inclui fila de aprovacao para remanejar e manager review.
8. Documenta limitacoes importantes, inclusive ausencia de forecast calibrado.
9. Visualmente segue a direcao de dashboard operacional tipo Untitled UI.

## Recomendacoes antes de submissao

1. Transformar `README.md` em README de submissao ou colocar no topo dele um link claro para `SOLUTION.md`.
2. Remover caminhos absolutos do setup e trocar por `python3`.
3. Adicionar um `requirements.txt` minimo com `pandas` e `numpy`, ou documentar dependencia de ambiente Python com esses pacotes.
4. Criar `PROCESS_LOG.md` dentro do diretorio do desafio, apontando para a transcricao completa e resumindo iteracoes, erros, correcoes e decisoes humanas.
5. Adicionar `scripts/validate_outputs.py` com checks reproduziveis.
6. Expor decomposicao do score no front, mesmo que compacta.
7. Renomear ou explicar melhor a coluna de especialista: "Especialista consultivo" quando nao houver remanejamento aprovado.
8. Curar `reports/`: manter screenshots finais e remover duplicatas/intermediarios.
9. Remover `.DS_Store` e adicionar `.gitignore` local se necessario.
10. Reforcar no texto que o score e prioridade operacional, nao probabilidade de fechamento.

## Veredito final

O projeto esta no caminho certo para passar no criterio funcional. Para ficar forte, precisa menos de modelo novo e mais de embalagem, validacao e clareza. A versao atual demonstra pensamento RevOps real, mas ainda exige que o avaliador confie demais em quem construiu. A proxima iteracao deve reduzir essa dependencia.
