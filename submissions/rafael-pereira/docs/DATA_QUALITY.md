# Qualidade dos dados

Data de referência ("hoje"): 31/12/2017. As tabelas entre marcadores `AUTO` são geradas por `python -m scorer.docs` a partir de `solution/data/processed/facts.json` (que `python -m scorer.clean` calcula dos CSVs brutos). Os números do texto são conferidos contra o mesmo arquivo por `tests/test_docs_numbers.py`.

## 1. Resumo: problema, evidência, tratamento e impacto

| Problema | Evidência | Tratamento | Impacto |
|---|---|---|---|
| "GTXPro" no pipeline, "GTX Pro" no catálogo | 1.480 dos 8.800 deals com o nome errado | `PRODUCT_NAME_MAP` troca o nome; `assert` de que todo produto existe no catálogo e de que o join mantém todas as linhas | Sem a correção, o join perde um produto inteiro (1.480 deals) |
| Setor "technolgy" | 12 contas, 1.165 deals | `SECTOR_MAP` troca por "technology" | Cosmético: o erro apareceria na interface |
| Deals sem conta | 1.425 (1.088 Engaging e 337 Prospecting), nenhum fechado; 68% dos 2.089 abertos | Mostrar "Conta não informada", sem penalidade, com alerta de higiene de CRM. `has_account` e qualquer nível "desconhecido" de setor ou porte ficam proibidos como variável | Risco de vazamento do desfecho (seção 5) |
| Prospecting sem `engage_date` | 500 deals, US$ 1,07 mi de tabela | Lista Qualifique, sem score, ordenada por preço de tabela | Sem idade, não há chance estimável; ficam fora do backtest |
| Vendedores sem deals | 35 no cadastro, 30 com deals, 5 sem nenhum; 27 com deal aberto, 3 só com fechados | Aparecem no filtro sob o manager com "(sem deals no CRM)", na "Carteira do time" com zeros e alerta; sem brief (seção 3) | Sem tratamento, o filtro mostraria pessoas vazias sem explicação |
| Win rate de 82,1% no 1º trimestre de 2017 | 647 fechamentos, todos em março; 61,1% nos trimestres seguintes; março (82,1%) fica a 1,9 pp da média de jun, set e dez (80,2%) | Artefato de recorte confirmado (seção 2): win rate por trimestre só com ressalva e fotos de treino a partir de 31/03/2017 | Comparar trimestres induz ao erro; treinar com o 1º trimestre inflaria a chance |
| `close_value` contra preço de tabela | Nos 4.238 ganhos, razão média de 0,996 (mín. 0,657, máx. 1,342); média por produto de 0,985 a 1,004; os 2.473 perdidos têm `close_value` 0 | O valor do deal aberto é `sales_price`; `close_value` só serve como desfecho no backtest (seção 4) | Pequeno: o preço de tabela representa bem o valor fechado |
| Teto de 138 dias e regra Q/Q+1 | Nenhum fechado acima de 138 dias, em nenhum trimestre de engajamento; 3.522 fecham no trimestre do engajamento, 3.188 no seguinte e 1 foge da regra | Artefatos do gerador sintético: documentados e não explorados. Os limiares saem de uma curva estimada, não de "se idade > 138" | Em CRM real o decaimento seria mais suave |
| Fechamentos rápidos no 1º mês do trimestre | Os 1.779 fechamentos de abr, jul e out têm ciclo de até 14 dias (mediana 7) e win rate de 49,0%; no 3º mês do trimestre, 80,7% | Documentados e não explorados: o score não usa mês nem posição no trimestre | O win rate de um período depende de quantos meses de fim de trimestre ele contém |
| Zumbis | 1.291 dos 1.589 Engaging (81,2%) abertos há mais que o maior ciclo fechado (138 dias), com US$ 3.198.664 dos US$ 3.892.229 de tabela do Engaging (82,2%) | Lista Limpe: confirmar com o cliente e encerrar ou atualizar, não descartar (o CRM pode estar desatualizado) | Pipeline inflado em cerca de US$ 3,2 mi |
| Truncamento à esquerda | O 1º fechamento é de 01/03/2017, mas há engajamentos desde 20/10/2016; os ciclos mínimos das coortes de out/2016 a fev/2017 são 123, 96, 63, 36 e 5 dias | O treino começa na foto de 31/03/2017 (seção 2) | As coortes antigas só mostram os deals de ciclo longo; sua win rate vai de 100% (out/2016, 7 deals) a 66% (fev/2017) |

## 2. Investigação 2a: o win rate de 82% no 1º trimestre de 2017

**Pergunta.** O 1º trimestre de 2017 é melhor ou é um artefato de recorte?

**Critério de decisão.** É artefato de recorte se valerem as três condições:

1. O 1º trimestre só tem fechamentos no primeiro mês observado (março).
2. O win rate desse mês fica a até 5 pp da média dos meses de fim de trimestre seguintes (jun, set e dez).
3. As coortes engajadas antes do primeiro fechamento não têm ciclos curtos: o ciclo mínimo de cada coorte fica a até 7 dias do piso que o recorte impõe (a distância entre o último dia da coorte e o primeiro fechamento).

As condições 1 e 2 e a tolerância de 5 pp vieram do plano. A tolerância de 7 dias da condição 3 foi escolhida pelo executor depois de uma primeira rodada exploratória em que as folgas já apareciam entre 2 e 7 dias. Ela vale no limite, então não deve ser lida como teste independente; por isso há o reforço sem tolerância na tabela de critérios e as coortes estão listadas abaixo.

**Evidência: win rate e ciclo por mês de fechamento.**

<!-- AUTO:dq-meses -->
| Mês de fechamento | Fechados | Win rate | Ciclo mediano (dias) | % com ciclo de até 14 dias |
| :--- | ---: | ---: | ---: | ---: |
| mar/2017 | 647 | 82,1% | 75 | 18% |
| abr/2017 | 586 | 48,6% | 7 | 100% |
| mai/2017 | 805 | 54,4% | 68 | 21% |
| jun/2017 | 641 | 82,8% | 77 | 22% |
| jul/2017 | 627 | 49,1% | 7 | 100% |
| ago/2017 | 785 | 56,8% | 70 | 22% |
| set/2017 | 635 | 79,2% | 73 | 23% |
| out/2017 | 566 | 49,3% | 7 | 100% |
| nov/2017 | 768 | 52,9% | 66 | 24% |
| dez/2017 | 651 | 78,5% | 76 | 16% |
<!-- /AUTO:dq-meses -->

**Evidência: por trimestre de fechamento.** O 1º trimestre é só março. Os outros trimestres misturam três meses de comportamentos muito diferentes.

<!-- AUTO:dq-trimestres -->
| Trimestre de fechamento | Fechados | Win rate | Ciclo mediano (dias) |
| :--- | ---: | ---: | ---: |
| 2017-Q1 | 647 | 82,1% | 75 |
| 2017-Q2 | 2.032 | 61,7% | 37 |
| 2017-Q3 | 2.047 | 61,4% | 27 |
| 2017-Q4 | 1.985 | 60,3% | 41 |
| Depois de 2017-Q1 | 6.064 | 61,1% | — |
<!-- /AUTO:dq-trimestres -->

**Evidência: por coorte mensal de engajamento (só deals fechados).** O ciclo mínimo das coortes antigas encosta no piso do recorte: sem o recorte, esperaríamos ciclos curtos, como nas coortes de março em diante.

<!-- AUTO:dq-coortes -->
| Coorte (mês de engajamento) | Fechados | Win rate | Ciclo mínimo (dias) | Piso do recorte (dias) | Folga (dias) | % com ciclo de até 14 dias |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| out/2016 | 7 | 100,0% | 123 | 121 | 2 | 0% |
| nov/2016 | 102 | 81,4% | 96 | 91 | 5 | 0% |
| dez/2016 | 196 | 81,6% | 63 | 60 | 3 | 0% |
| jan/2017 | 247 | 73,3% | 36 | 29 | 7 | 0% |
| fev/2017 | 420 | 66,0% | 5 | 1 | 4 | 8% |
| mar/2017 | 655 | 67,2% | 1 | — | — | 32% |
| abr/2017 | 753 | 56,7% | 1 | — | — | 67% |
| mai/2017 | 588 | 62,2% | 1 | — | — | 28% |
| jun/2017 | 681 | 66,5% | 1 | — | — | 37% |
| jul/2017 | 796 | 55,4% | 1 | — | — | 67% |
| ago/2017 | 539 | 63,3% | 1 | — | — | 29% |
| set/2017 | 677 | 62,8% | 1 | — | — | 33% |
| out/2017 | 703 | 56,9% | 1 | — | — | 71% |
| nov/2017 | 244 | 64,3% | 1 | — | — | 64% |
| dez/2017 | 103 | 77,7% | 2 | — | — | 73% |
<!-- /AUTO:dq-coortes -->

**Evidência: trimestre de engajamento contra trimestre de fechamento.** O gerador fecha os deals no trimestre em que foram engajados ou no seguinte (regra Q/Q+1). A única exceção é um deal do 2º trimestre fechado no 4º.

<!-- AUTO:dq-cruzamento -->
| Engajado em \ fechado em | 2017-Q1 | 2017-Q2 | 2017-Q3 | 2017-Q4 |
| :--- | ---: | ---: | ---: | ---: |
| 2016-Q4 | 305 | — | — | — |
| 2017-Q1 | 342 | 980 | — | — |
| 2017-Q2 | — | 1.052 | 969 | 1 |
| 2017-Q3 | — | — | 1.078 | 934 |
| 2017-Q4 | — | — | — | 1.050 |

Fechados no mesmo trimestre do engajamento: 3.522; no trimestre seguinte: 3.188; fora da regra: 1.
<!-- /AUTO:dq-cruzamento -->

**Evidência: posição do mês dentro do trimestre.** O mesmo gerador fecha rápido no 1º mês do trimestre e com win rate alto no 3º.

<!-- AUTO:dq-posicao-trimestre -->
| Mês dentro do trimestre | Fechados | Win rate | Ciclo mediano (dias) | % com ciclo de até 14 dias |
| :--- | ---: | ---: | ---: | ---: |
| 1º mês (jan, abr, jul, out) | 1.779 | 49,0% | 7 | 100% |
| 2º mês (fev, mai, ago, nov) | 2.358 | 54,7% | 68 | 22% |
| 3º mês (mar, jun, set, dez) | 2.574 | 80,7% | 75 | 20% |
<!-- /AUTO:dq-posicao-trimestre -->

**Resultado do critério.**

<!-- AUTO:dq-criterio-2a -->
| Condição | Medido | Limite | Vale? |
| :--- | :--- | :--- | ---: |
| (i) o 2017-Q1 só tem fechamentos em mar/2017 | 0 fechamentos fora de mar/2017 | 0 | sim |
| (ii) win rate de mar/2017 perto dos meses de fim de trimestre (jun, set, dez) | 82,1% contra 80,2% (+1,9 pp) | ±5 pp | sim |
| (iii) coortes engajadas antes de 01/03/2017 sem ciclos curtos (truncamento) | maior folga entre o ciclo mínimo e o piso do recorte: 7 dias (5 coortes) | 7 dias | sim |

**Resultado: artefato de recorte confirmado (as três condições valem).**

Reforço sem tolerância: nas coortes com piso de 14 dias ou mais, 0% dos fechamentos são rápidos; nas coortes sem recorte, no mínimo 28%.
<!-- /AUTO:dq-criterio-2a -->

**Decisão (decisão autônoma do Claude).**

- **(a)** O win rate por trimestre só aparece com a ressalva de que o 1º trimestre tem um mês.
- **(b)** As fotos de treino do bloco 3 começam em 31/03/2017, a primeira de fim de mês dentro do período observado de fechamentos. Os deals fechados em março de 2017 não entram como observação de treino. Os engajados antes e ainda abertos em 31/03 entram, porque a população aberta numa data dentro do período observado é completa.
- **(c)** A foto de 28/02/2017 entra só como sensibilidade no bloco 3, porque depende da hipótese não verificável de que o recorte removeu exatamente os fechados antes de 01/03/2017.
- **(d)** Os artefatos do gerador (regra Q/Q+1, fechamentos rápidos no 1º mês do trimestre e teto de 138 dias) ficam documentados e não são explorados pelo score.

**Transparência sobre 28/02.** O planejador (Claude Opus) viu, num protótipo, que começar em 28/02 piora o modelo do corte de 30/06. A regra de começar em 31/03 foi justificada a priori (item b), mas escolhida depois de ver isso. Por isso 28/02 é reportado como sensibilidade, e não como alternativa equivalente.

## 3. Investigação 2b: vendedores sem deals

**Critério.** Zero deals em qualquer estágio significa "cadastro sem pipeline": não há o que priorizar nem como atribuir desempenho.

<!-- AUTO:dq-vendedores -->
Cadastro: 35 vendedores; com algum deal: 30; com deal aberto na data de referência: 27; sem nenhum deal: 5; só com deals fechados: 3.

**Sem nenhum deal no CRM**

| Vendedor | Manager | Região |
| :--- | :--- | :--- |
| Carl Lin | Summer Sewald | West |
| Carol Thompson | Celia Rouche | West |
| Elizabeth Anderson | Cara Losch | East |
| Mei-Mei Johns | Melvin Marxen | Central |
| Natalya Ivanova | Rocco Neubert | East |

**Só com deals fechados (nenhum aberto)**

| Vendedor | Manager | Região |
| :--- | :--- | :--- |
| Donn Cantrell | Rocco Neubert | East |
| Garret Kinder | Cara Losch | East |
| Reed Clapper | Rocco Neubert | East |

Times sem nenhum vendedor fora do pipeline: Dustin Brinkmann.
<!-- /AUTO:dq-vendedores -->

**Decisão (decisão autônoma do Claude).**

- Os 5 sem deals aparecem no filtro de vendedor, agrupados sob o manager, com o sufixo "(sem deals no CRM)" e um estado vazio que explica o motivo.
- Aparecem na "Carteira do time" com zeros e um alerta.
- Não recebem brief; o índice dos briefs os lista.
- Os 3 só com deals fechados mostram "sem deals abertos".

## 4. Investigação 2c: `close_value` e preço de tabela

**Critério.** O preço de tabela serve como valor do deal aberto se a média de `close_value` / `sales_price` de cada produto ficar entre 0,95 e 1,05 e a média trimestral variar até 3 pp.

<!-- AUTO:dq-razao-preco -->
| Recorte | Ganhos | Média | Mediana | p5 | p95 | Mín | Máx |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Todos os ganhos | 4.238 | 0,996 | 0,998 | 0,833 | 1,164 | 0,657 | 1,342 |
| Produto: GTK 500 | 15 | 0,998 | 0,967 | 0,913 | 1,114 | 0,887 | 1,132 |
| Produto: GTX Basic | 915 | 0,992 | 0,995 | 0,829 | 1,151 | 0,664 | 1,302 |
| Produto: GTX Plus Basic | 653 | 0,985 | 0,988 | 0,819 | 1,140 | 0,686 | 1,254 |
| Produto: GTX Plus Pro | 479 | 1,001 | 1,004 | 0,844 | 1,169 | 0,676 | 1,342 |
| Produto: GTX Pro | 729 | 0,999 | 1,001 | 0,835 | 1,170 | 0,657 | 1,279 |
| Produto: MG Advanced | 654 | 0,999 | 0,997 | 0,839 | 1,167 | 0,730 | 1,313 |
| Produto: MG Special | 793 | 1,004 | 1,000 | 0,855 | 1,164 | 0,691 | 1,309 |
| Fechamento em 2017-Q1 | 531 | 0,993 | 0,995 | 0,836 | 1,161 | 0,664 | 1,265 |
| Fechamento em 2017-Q2 | 1.254 | 0,998 | 0,998 | 0,836 | 1,162 | 0,657 | 1,342 |
| Fechamento em 2017-Q3 | 1.257 | 0,995 | 1,000 | 0,827 | 1,164 | 0,684 | 1,309 |
| Fechamento em 2017-Q4 | 1.196 | 0,998 | 0,998 | 0,831 | 1,168 | 0,676 | 1,332 |

- Média por produto: de 0,985 a 1,004 (faixa aceita: 0,95 a 1,05): sim.
- Variação da média entre trimestres: 0,5 pp (limite: 3 pp): sim.
- Perdidos com `close_value` = 0: 2.473 de 2.473; ganhos com `close_value` = 0: 0.
<!-- /AUTO:dq-razao-preco -->

**Decisão (decisão autônoma do Claude).** O critério vale. O valor do deal aberto é `sales_price`, e `close_value` só serve como desfecho no backtest. Os 4.238 ganhos têm `close_value` positivo e os 2.473 perdidos têm 0, então `close_value` também não pode ser usado para identificar o estágio de um deal aberto.

## 5. Vazamento pela conta ausente

Todos os 1.425 deals sem conta estão abertos no fim dos dados, então "sem conta" equivale a "nunca fechou". Qualquer variável que carregue essa ausência (`has_account`, a categoria "desconhecido" de setor ou de porte) funcionaria como um detector de deal parado e inflaria qualquer métrica sem prever nada. Decisão: essas variáveis são proibidas como entrada do score. Atributos de conta só podem ser avaliados no subconjunto com conta; o bloco 3 testa a guarda e mostra o que aconteceria sem ela.

## 6. Como reproduzir

```
cd solution
python -m scorer.clean      # grava data/processed/deals.csv e facts.json
python -m scorer.docs       # reescreve os blocos AUTO dos documentos
python -m pytest            # inclui a conferência dos números do texto
```
