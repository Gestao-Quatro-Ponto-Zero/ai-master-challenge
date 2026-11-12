# Revisão técnica do plano v1 (11/11/2026)

> Revisão do [02-plano-implementacao.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/02-plano-implementacao.md) na versão de 10/11, por arquitetura de dados, engenharia de software e modelo de negócio. Cada achado foi conferido por script próprio: [analise/eda-04-auditoria-plano-v1.py](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/eda-04-auditoria-plano-v1.py), [analise/eda-05-relogio-do-trimestre.py](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/eda-05-relogio-do-trimestre.py) e [analise/eda-06-prototipo-motor-v2.py](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/eda-06-prototipo-motor-v2.py), com as saídas `.saida.txt` ao lado. Nada aqui vem de leitura; tudo vem de execução.
>
> O plano v1 era bom no que é raro (process log, backtest, honestidade sobre o que não se sabe) e frágio justamente no que ele mais prometia: a estatística. O v2 nasceu desta revisão.

---

## 0. Veredito em cinco linhas

O plano v1 tinha **seis números pinados em teste que não fecham com o dataset**, uma **tabela de probabilidade com o mesmo viés de sobrevivência que o process log se gabava de ter corrigido**, e o **achado central do desafio faltando** — o prazo do trimestre, que o PR público #242 já tem. Sua métrica de sucesso (3× o aleatório) mede mistura de preço, não previsão: a taxa de acerto do top 5 por preço é 36,8% contra 35,7% do sorteio. O piloto proposto precisaria de 109 vendedores por braço para detectar o efeito que ele promete medir com 5. E o `git add` da Tarefa 0 não adiciona arquivo nenhum, porque `submissions/` está no `.gitignore` do repositório oficial.

Em troca, a revisão encontrou um sinal real que ninguém no campo usou: **quando um deal decide depende da idade e da altura do trimestre, juntas**. Ordenar por valor esperado nessa leitura captura **1,30× o que a melhor regra pública captura** (IC 95% de 1,13 a 1,52) e **3,28× o sorteio**, com taxa de acerto de 22,7% contra 15,4%. Isso deixa de ser "ferramenta bonita sobre achado conhecido" e passa a ser scoring com evidência, que é o critério literal do desafio.

---

## 1. Erros que fazem o plano falhar na execução

Estes não são discutíveis. São testes do próprio plano que quebram no primeiro `pytest`.

| # | Onde | O plano v1 diz | O dataset diz | Causa |
|---|---|---|---|---|
| 1.1 | Tarefa 3, `test_capacidade_tem_piso_e_teto` | `len(c) == 35` | 30 vendedores têm algum deal; 27 têm deal aberto | `sales_teams.csv` tem 35 cadastrados, mas Carl Lin, Carol Thompson, Elizabeth Anderson, Mei-Mei Johns e Natalya Ivanova não aparecem em nenhuma linha do pipeline. Donn Cantrell, Garret Kinder e Reed Clapper têm histórico e nenhum deal aberto |
| 1.2 | Tarefa 5, `test_build_grava_e_soma` | `len(j["vendedores"]) == 35` | idem | mesma causa; o motor tem de decidir explicitamente se a lista é o cadastro ou quem tem deal, e dizer qual na tela |
| 1.3 | Tarefa 2, `test_vencido_vai_para_encerrar` | 1.291 vencidos | **1.301** com `hoje = 01/01/2018` | o EDA mediu idade contra 31/12 (último dia do export) e o produto define `hoje` como o dia seguinte. Um dia de diferença move 10 deals |
| 1.4 | Tarefa 2, `test_fases_por_idade` | 0-30 = cedo, 31-90 = decisão, 91-138 = esfriando | as contagens com `hoje` certo são 17, 93 e 178, não 18, 92 e 188 | mesma causa |
| 1.5 | Tarefa 2, `test_filas_somam_abertos` | `len(s) == 2089` ✓ | 2.089 confere | único número de contagem que sobrevive |
| 1.6 | Tarefa 1, `test_gtxpro_e_gtx_pro` | 333 abertos com `GTX Pro` | 333 confere ✓, mas o teste afirma `produto_norm == "GTX Pro"` | decisão de produto escondida em teste: o catálogo diz `GTX Pro`, o CRM diz `GTXPro`. Normalizar para o nome do catálogo muda o que o vendedor lê na tela em 1.480 linhas. É escolha, não detalhe |
| 1.7 | Tarefa 1, `test_qualidade_conta_e_datas` | `maior_data == "2017-12-31"` ✓ | confere | ok |
| 1.8 | Tarefa 0, Step 5 | `git add submissions/diego-rodrigues` | não adiciona nada | `submissions/` está no `.gitignore` do repositório oficial (achado que o PR #184 publicou). Precisa de `git add -f` |
| 1.9 | Tarefa 3, `test_vendedor_sem_fechamento_recebe_minimo` | usa `hist[hist.sales_agent != "Anna Snelling"]` | Anna Snelling tem 448 deals e é o 2º maior volume | o teste remove o vendedor errado para simular o caso; qualquer um dos 5 sem deal já é o caso real, sem precisar mutilar o histórico |

**Além disso**, a capacidade do v1 não produz o que o guia promete. A fórmula (fechamentos em 90 dias ÷ 12,86 × 1,5, piso 5, teto 25) dá `cap_dia = 1` para 12 vendedores e `cap_dia = 2` para 19; a mediana da capacidade semanal é 7. O guia e o rascunho de tela falam em "5 por dia, 20 a 25 por semana". E a fila `vivo` do v1 (Engaging, até 138 dias, preço acima de 550) tem **mediana zero por vendedor**: 18 dos 35 não têm nenhum deal nela. A tela principal abriria vazia para metade do time.

---

## 2. O erro estatístico que o plano cometia enquanto dizia tê-lo evitado

O `onde-a-ia-errou.md` do v1 lista, com razão, "modelo treinado só em fechados aprende que deal velho é bom (viés de sobrevivência)". A `tabela_chance` da Tarefa 2 comete exatamente esse erro.

A definição do v1: *"entre deals do histórico com ciclo ≥ faixa_ini, fração com ciclo ≤ faixa_ini + horizonte"*. O denominador são **só deals que já fecharam**. Quem ainda está aberto na idade `faixa_ini` não entra. Como todo deal fechado fecha em algum momento, a fração tende a 1 conforme a idade sobe.

| Idade | Em risco de verdade (com os abertos e a censura) | Decide em 30 dias: real | Decide em 30 dias: fórmula do v1 |
|---|---|---|---|
| 0 | 8.283 | 38,1% | 47,1% |
| 30 | 5.089 | 10,6% | 16,2% |
| 60 | 4.495 | 35,6% | 55,0% |
| 90 | 2.794 | 42,9% | 86,4% |
| 120 | 1.388 | 15,6% | **100,0%** |
| 138 | 772 | 0,3% | **100,0%** |

A tela diria "cerca de 100 em cada 100 deals nessa idade decidem no próximo mês" para um deal de 120 dias. O real é 16 em 100. Esse número aparece no cartão "por quê" de cada deal, na Tela 3 e na métrica de calibração dos evals — é o número mais visível da submissão, e estaria errado por um viés que o process log reivindica ter corrigido. Um avaliador que recalcule encontra isso em dez minutos, e o custo não é o erro: é a credibilidade do resto.

**Correção no v2:** tábua de vida com censura explícita. Em risco na idade `a` = todo deal (fechado ou aberto) com duração observada ≥ `a`, mantido só se a janela de 28 dias inteira é observável (fechou, ou ainda estava aberto 28 dias depois). É a Tarefa 3 do v2, com este teste como regressão.

---

## 3. O achado que faltava, e que um PR público já tem

O guia v1 constrói tudo sobre um limite: nenhum deal fechou depois de 138 dias. Está certo, e é point-in-time (o ciclo máximo conhecido já era 138 em 01/04/2017, conferido na seção C do eda-05). Mas é **metade da regra**.

Os fechamentos param no **fim do trimestre seguinte ao do engajamento**: 6.710 de 6.711. A única exceção é um deal perdido. Conferida em cada data, a regra nunca teve contraexemplo conhecido (0 em 01/07, 0 em 01/10, 1 em 01/01/2018).

Consequência direta na foto de 01/01/2018:

| Regra | Vivos | Valor vivo | Vencidos | Valor vencido |
|---|---|---|---|---|
| Só 138 dias (v1) | 288 deals | US$ 1,74 mi | 1.301 | US$ 3,23 mi (65,0%) |
| 138 dias **e** prazo do trimestre (v2) | **115 deals** | **US$ 235.930** | 1.474 | US$ 3,66 mi (73,6%) |

E aqui está o problema de coerência: **os números que o guia v1 cita como seus já são os da segunda regra**. "US$ 3,66 mi vencidos, 74% do pipeline, US$ 236 mil vivos no prazo" (seções 3.5 e 8) só saem se o prazo do trimestre estiver aplicado. O guia aplicou a regra na conta e descreveu outra no texto. São 173 deals, US$ 429 mil, que o motor do v1 colocaria na fila do vendedor e que a história diz que não fecham mais.

O PR #242 (Daniel Resende) tem essa regra, em português, com drift check. Entregar sem ela não é só perder um número: é entregar atrás do que já está público, no critério em que o avaliador disse que "parecido com o baseline" reprova.

---

## 4. A métrica de sucesso media a coisa errada

O v1 e o guia vendem "3× o aleatório" e o teste `test_ferramenta_bate_aleatorio` exige `≥ 2.5 ×`. Conferido:

| | Valor ganho em 90 dias, top 5 por vendedor | Taxa de acerto |
|---|---|---|
| Top 5 por preço de tabela | US$ 2.169.514 | **36,8%** |
| Sorteio entre os abertos | US$ 795.726 | **35,7%** |

O múltiplo de valor é 2,73×. O preço médio dos escolhidos é 2,87× o preço médio dos abertos. **As duas razões são a mesma razão.** A política não acerta mais deals: ela acerta deals mais caros, porque foi ordenada por preço. Com taxa de acerto idêntica, "3× o aleatório" é uma tautologia disfarçada de resultado, e o teste que a exige passa sem que a ferramenta tenha qualquer poder preditivo.

Pior: é o número da frase do CFO ("cinco deals vivos que valem três vezes mais que a escolha ao acaso"). A frase é verdadeira e vazia ao mesmo tempo — e um avaliador que vende transformação para dono de empresa reconhece a diferença.

**Correção no v2:** três métricas, cada uma medindo uma coisa.
1. **Contra a melhor alternativa honesta** (preço de tabela entre os vivos pelas duas regras), não contra o sorteio.
2. **Taxa de acerto**, que mistura de preço não move.
3. **Fração do teto**: quanto do valor que um oráculo com o futuro na mão captaria a ferramenta capta (41,2% contra 31,6% da regra de preço).

O sorteio continua na tabela, como piso, com a nota de que o múltiplo contra ele é em grande parte mistura de preço. Declarar isso é mais forte do que esconder: é o julgamento que o desafio diz procurar.

---

## 5. O sinal que ninguém usou: o relógio do trimestre

Este é o achado novo da revisão. Conferido em [eda-05](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/eda-05-relogio-do-trimestre.py), seções A, B, D, E e F.

**O fato.** Nenhum deal com ciclo acima de 30 dias fechou no primeiro mês de um trimestre. Nenhum. O maior ciclo de um fechamento ocorrido num 1º mês é **13 dias**. Nos três trimestres medidos, dos **3.618 deals com 16 a 138 dias abertos no 1º dia de um trimestre, zero decidiram nas quatro semanas seguintes**.

Nos meses 2 e 3 a janela abre, e a taxa de ganho salta na semana 10 do trimestre: 55,8% a 60,7% nas semanas 5 a 9, e 78,9% a 80,1% nas semanas 10 a 13.

**O que isso não é.** O PR #240 viu o efeito de calendário na taxa de ganho (81% nos meses de fim de trimestre contra 52%), checou se se concentrava nos últimos dias do mês, viu que não, e **descartou como artefato**. A conclusão dele está certa para o que ele mediu — como preditor de *ganho contra perda*, o mês do fechamento é inútil para priorizar, porque só se conhece depois.

**O que isso é.** O mês do trimestre em que a *data de hoje* cai é conhecido hoje. O que ele prevê não é quem ganha: é **quando decide**. Isso é o que a lista de segunda-feira precisa saber, e é a pergunta que o desafio faz ("onde focar"). O #240 descartou a variável respondendo à pergunta errada; o v2 a usa respondendo à certa. Essa diferença é a melhor história de julgamento da submissão, e ela existe porque alguém leu o PR público e discordou com dado na mão.

**O resultado.** Backtest as-of, segundas a cada quatro semanas de julho a dezembro de 2017 (janelas de 28 dias que não se sobrepõem), top 5 por vendedor, tudo aprendido só das datas análogas dos trimestres anteriores:

| Política | Valor ganho em 28 dias | Taxa de acerto | Fração do teto |
|---|---|---|---|
| **Relógio do trimestre (v2)** | **US$ 1.097.324** | **22,7%** | **41,2%** |
| Preço entre vivos pelas duas regras (melhor regra pública) | US$ 842.462 | 15,4% | 31,6% |
| Preço entre os de até 138 dias (v1 sem o prazo) | US$ 867.889 | 16,0% | — |
| Sorteio entre os vivos | US$ 334.520 | 14,4% | — |

| Razão | Valor | IC 95% (bootstrap por vendedor, 30 vendedores, 5.000 reamostras, semente 7) |
|---|---|---|
| Relógio ÷ preço entre vivos | **1,30×** | 1,13 a 1,52 |
| Relógio ÷ preço até 138 dias | 1,26× | 1,13 a 1,44 |
| Relógio ÷ sorteio | 3,28× | 2,53 a 4,39 |

O intervalo não cruza 1 em nenhuma das três. Em todas as 22 segundas de julho a dezembro (janelas sobrepostas, só para ver estabilidade), o relógio ficou acima da regra de preço em 16.

**Por que não é vazamento.** O limiar não é escrito à mão: sai da tabela aprendida das datas análogas, que só usa fechamentos já conhecidos naquela data. A prova está na seção G do eda-06: em 28/08/2017 (semana 9) o motor coloca 1.845 deals em "fechar"; em 02/10/2017 (semana 1) coloca 1.349 em "preparar" e só 368 em "fechar". Mesma regra, duas respostas, porque o trimestre está em outra altura. Nenhuma constante mudou entre as duas execuções.

**Por que é honesto.** Não é "o modelo prevê quem ganha". É "a janela em que uma decisão acontece neste negócio tem forma de trimestre, e a lista de segunda respeita essa forma". Em produção isso vira configuração (o ciclo do cliente pode ser mensal, anual ou de safra), e o drift check avisa quando a forma muda. É o oposto de sofisticação sem prova.

---

## 6. Modelo de negócio: três problemas e o que fazer

### 6.1 O piloto proposto não pode funcionar

O guia (seção 8) propõe: uma região, metade dos vendedores usa, critério de aceite +10% de valor ganho com intervalo que exclua zero. Conferido na seção F do eda-04:

- Valor ganho por vendedor por trimestre: coeficiente de variação médio **0,59**; correlação entre trimestres consecutivos **0,90**.
- Com 5 vendedores por braço (metade de uma região): menor efeito detectável **104%**, ou 47% ajustando pelo trimestre anterior.
- Para detectar +10% com esse ajuste: **109 vendedores por braço**. A empresa tem 30 ativos.

Prometer esse critério de aceite é prometer um teste que vai dar "não significativo" mesmo se a ferramenta funcionar muito bem. Um avaliador que faz conta de poder — e o repositório mostra avaliadores pedindo "n, intervalo, teste de significância" — lê isso como desenho ingênuo.

**O que o v2 propõe.** Sorteio **por deal, dentro do vendedor**, não por vendedor. Cada vendedor recebe sua lista, e uma fração dos deals elegíveis é retida do score (entra na lista por ordem de preço, como hoje). O ICC da decisão por vendedor é 0,031, então o agrupamento quase não infla a variância, e cada vendedor é seu próprio controle. Métrica primária: taxa de decisão em 28 dias dos deals priorizados. Com base de 22%, **1.100 deals por braço** detectam +5 pontos — cerca de três semanas de pipeline do time inteiro, não três trimestres. O valor ganho continua como métrica secundária, declarado como ruidoso demais para ser primário, com a conta mostrada.

### 6.2 O ROI está apoiado numa premissa e parece medição

"3 horas por semana por vendedor em deals vencidos × R$ 80 a hora = R$ 430 mil por ano". As duas pontas são hipóteses, e a multiplicação dá um número com cara de medida. O v2 mantém a conta, mas: inverte a apresentação (primeiro o que é medido, depois o que é premissa), e substitui o número único por **faixa com o ponto de equilíbrio** — quantas horas por semana precisariam ser verdade para o projeto pagar o próprio custo de entrega. Isso é a pergunta que um dono de empresa faz, e é o que a formação de FDE chama de declarar a premissa antes de vender o resultado.

O que **é** medido e vale mais do que a estimativa de horas: US$ 3,66 mi de pipeline aberto no CRM sem nenhuma chance histórica de fechar, 73,6% do total. O forecast que a Head leva para o CFO está construído sobre isso. Esse é o número do resumo executivo.

### 6.3 Falta o maior ativo do dataset, e ele é de negócio, não de código

Os 500 deals em Prospecting valem **US$ 1.073.986 de preço de tabela** — 4,5 vezes todo o pipeline vivo (US$ 235.930). Estão todos na região Central e nenhum tem data de engajamento. O v1 os trata como "fila iniciar, até `cap_semana`, ordenado por valor".

Mas deals engajados dentro de um 1º mês de trimestre decidem no próprio mês em 48,9% dos casos, com 24,3% de ganho no mês (seção J do eda-05). Como 01/01/2018 é a primeira segunda-feira de um trimestre, e como quase nada mais está vivo, **a recomendação honesta para essa semana é: o trabalho é começar os 500, não resgatar os velhos**. Ordem de grandeza se eles se comportarem como os engajamentos anteriores: US$ 260 mil, declarado como premissa.

Isso muda a cara da submissão. Em vez de uma ferramenta que diz "ligue para estes cinco", ela diz: *"esta semana não há o que fechar; a sua semana é abrir os 500 que estão parados sem data, e aqui está a ordem"*. Nenhum dos três PRs do topo faz essa leitura, porque nenhum olhou a altura do trimestre. É leitura de processo, que é o que a vaga pede.

---

## 7. Arquitetura de dados e engenharia: o que muda

| # | Problema no v1 | Correção no v2 |
|---|---|---|
| 7.1 | `hoje` padrão = maior data + 1 dia, implícito | `hoje` é parâmetro obrigatório do motor, sem padrão escondido. `run.py` resolve o default e **imprime** qual data usou |
| 7.2 | O backtest "usa o mesmo motor", mas quem apaga o futuro é o backtest | Uma função `recortar(dados, hoje)` é a **única** porta de entrada do motor, usada igual em produção e em avaliação. O motor não recebe coluna de desfecho futuro; é impossível vazar, não só combinado |
| 7.3 | Limiares de fase em `config.json` (30, 90, 138) | Nenhum limiar de fase. Faixas de idade + tabela aprendida das datas análogas. O que fica em config é o que é escolha de operação (horizonte, foco, chance mínima), não leitura dos dados. É o "código específico vira configuração" de verdade |
| 7.4 | `pontuar` devolve 18 colunas, `distribuir` muta a coluna `fila` | Fronteiras explícitas: `aprender` (histórico → tabela) e `pontuar` (tabela + abertos → fila). Nenhuma função reescreve o que outra decidiu |
| 7.5 | `tabela_chance` com faixas fixas `[0,15)...(138,∞)` | Bordas vêm de `config`, última faixa fecha em `ciclo_max` **aprendido**, e faixa com menos de `n_min` observações é agrupada. Sem faixa de 2 deals virando probabilidade |
| 7.6 | Nenhum teste de vazamento | Teste que roda o motor em duas datas e verifica que a saída da primeira não muda quando o futuro é alterado; e um deal sintético que fecha no dia seguinte ao corte, que não pode aparecer como decidido |
| 7.7 | Determinismo testado por igualdade de JSON | Hash SHA-256 do JSON sem o campo de data de geração, gravado em arquivo e comparado. É o que um CI checaria |
| 7.8 | `anthropic` como dependência opcional sem versão de piso clara | `requirements.txt` com piso e `requirements-lock.txt`. Python 3.12+ declarado e testado também em 3.9 (o macOS do avaliador pode ter 3.9) |
| 7.9 | Dados copiados sem procedência | `data/FONTE.md` com a URL do Kaggle, a licença CC0 e `SHA256SUMS` dos quatro CSVs. É o que torna o número reproduzível por terceiro |
| 7.10 | Nada detecta que o mundo mudou | `drift.py`: recalcula ciclo máximo, validade da regra do trimestre e tabela por faixa a partir de dados novos, compara com o guardado e falha com mensagem se moveu além da tolerância |

---

## 8. O que o v1 acertou e o v2 preserva

Não é um plano ruim. É um plano que precisa de aritmética.

- **Process log desde o primeiro minuto**, baseline reproduzido em dois modelos, "onde a IA errou" com o teste que derrubou cada coisa. É o critério de 30% da nota e o v1 já tratava como primeira classe.
- **TDD com valores pinados.** O defeito foi nos valores, não no método: foi justamente o rigor de pinar número em teste que permitiu descobrir os seis erros antes de escrever código. Um plano com "assert len(x) > 0" não teria revelado nada.
- **Nada de regra de negócio no front.** Mantido e testado.
- **Todo número do README sai de script.** Mantido, agora com o script também imprimindo o intervalo de confiança.
- **LLM só onde há variação, com validador determinístico e fallback.** Mantido; o v2 só aperta o validador (ver Tarefa 9 do v2) e acrescenta o registro de custo e de recusas.
- **O kit de deploy como diferencial.** Mantido inteiro. Era e continua sendo o espaço em branco do campo.

---

## 9. Riscos do v2 e como tratá-los

| Risco | Tratamento |
|---|---|
| O relógio do trimestre é artefato de um dataset sintético | Dito em `limitacoes.md` com todas as letras, e é por isso que `drift.py` existe. O argumento da submissão não é "trimestres são universais": é "a janela de decisão deste negócio tem uma forma, o motor a aprende dos dados e avisa quando ela muda" |
| Três trimestres é pouca história | Declarado. O IC do bootstrap é por vendedor, não por data, e o número de datas análogas aparece em cada linha do backtest. Em 01/01/2018 são três |
| A fila "fechar" tem 7 deals na data de referência | É o resultado honesto, e vira o argumento do produto (seção 6.3). A tela precisa de um estado vazio bem feito, não de um número inflado |
| Parecer que copiei o #242 ao adotar o prazo do trimestre | Declarado em uma linha no README e no process log: li os PRs públicos depois de ter a minha tese, achei a regra lá, conferi com script próprio, adotei e creditei. Isso é prior art tratado como num projeto real, e é mais forte do que chegar sem ela |
| O avaliador não recalcular e achar o v2 mais complicado | `numeros.py` imprime cada número com rótulo e fonte; a Tela 3 mostra a tabela aprendida e as regras rejeitadas. A complexidade fica no motor, não na tela do vendedor |

---

## 10. Checklist da revisão (o que foi conferido e onde)

| Afirmação do v1 | Script | Resultado |
|---|---|---|
| 35 vendedores em toda tabela | eda-04 A | ✗ 30 com deal, 27 com deal aberto |
| 1.291 vencidos | eda-04 B | ✗ 1.301 com `hoje = 01/01/2018` |
| Fases 0-30 / 31-90 / 91-138 com 18 / 92 / 188 | eda-04 B | ✗ 17 / 93 / 178 |
| 2.089 abertos, 500 Prospecting, 1.425 sem conta | eda-04 A, eda-06 A | ✓ |
| 333 abertos de GTX Pro, merge ingênuo derruba US$ 1,6 mi | eda-06 A | ✓ (1.480 linhas no total com o apelido) |
| `tabela_chance` dá probabilidade válida | eda-04 C | ✗ chega a 100% aos 120 dias; real 15,6% |
| Nenhum deal ganho após 138 dias | eda-04 B, eda-05 C | ✓ e point-in-time em todas as datas |
| Capacidade de ~5/dia e 20-25/semana | eda-04 D | ✗ mediana 7/semana, `cap_dia` 1 ou 2 para 31 de 35 |
| Fila `vivo` serve de tela principal | eda-04 D | ✗ mediana 0 por vendedor, 18 de 35 com zero |
| Lift 3× o aleatório é resultado | eda-04 E | ✗ taxa de acerto 36,8% contra 35,7%; é mistura de preço |
| Piloto detecta +10% com meia região | eda-04 F | ✗ precisaria de 109 por braço |
| US$ 3,66 mi vencidos / 74% / US$ 236 mil vivos | eda-04 G | ✓ mas só com a regra do trimestre, que o v1 não tem |
| Atributos não preveem ganho | eda-05 L | ✓ e continua valendo controlando o mês do trimestre (conta p=0,98; vendedor p=0,28; vendedor×produto p=0,45) |
| Prazo do trimestre vale e é point-in-time | eda-05 C | ✓ 6.710 de 6.711; 0 contraexemplos conhecidos até 01/10/2017 |
| Relógio do trimestre bate a melhor regra pública | eda-05 F, eda-06 F | ✓ 1,30× com IC 95% de 1,13 a 1,52 |
| A especificação do v2 é implementável | eda-06 | ✓ protótipo roda, 0 violações de monotonia, valores de ouro fixados |
| `submissions/` entra no commit | `.gitignore` do upstream | ✗ precisa de `git add -f` |

---

## 11. Onde cada correção entrou no plano v2

| Achado | Tarefa do v2 |
|---|---|
| 1.1 a 1.9 (números pinados, `git add -f`) | Tarefas 0 a 5, com os valores de ouro vindos do eda-06 |
| 2 (viés na tabela de probabilidade) | Tarefa 3, `motor/aprender.py`, com o teste de regressão |
| 3 (prazo do trimestre) | Tarefa 2, `motor/janela.py` |
| 4 (métrica errada) | Tarefa 7, `avaliacao/backtest.py`, três métricas e o bootstrap |
| 5 (relógio do trimestre) | Tarefas 3 e 4, o score inteiro |
| 6.1 (poder do piloto) | Tarefa 12, `docs/experimento.md` |
| 6.2 (ROI) | Tarefa 13, `docs/resumo-executivo.md` |
| 6.3 (os 500 de Prospecting) | Tarefas 4, 9 e 13 |
| 7.1 a 7.10 (arquitetura) | Tarefas 1 a 8 e 11 |
| Registro de uso de IA auditável | Tarefa 0 e o kit `registro-ia` (`.claude/skills/registro-ia/`) |
