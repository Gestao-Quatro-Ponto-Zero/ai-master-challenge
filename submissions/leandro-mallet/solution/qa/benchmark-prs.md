# Benchmark — submissões concorrentes do challenge 003

Complemento ao [baseline.md](baseline.md). O baseline estima o que uma IA entrega sozinha; este arquivo olha o que **outros candidatos** já entregaram para o mesmo desafio. Serve para calibrar a barra e achar onde a nossa entrega ainda pode se diferenciar.

**Escopo.** O repositório oficial tinha 239 PRs em 09/11/2026, 116 deles do 003. Desses 116, 26 têm link publicado, 107 têm process log e 58 têm testes, e nenhum foi mesclado. Os 10 mais completos por sinais objetivos (README, process log, prints, código, testes, link) foram lidos: README, lógica do score e process log. Os 8 links publicados foram abertos. Ficaram de fora 2 PRs que misturam desafios.

**Método.** Tudo só de leitura: nenhum código deles rodou, sem login, sem comentário, sem fork. Os autores estão anonimizados (Submissão A a J); a correspondência com o número do PR está na nota do fim. Os achados descrevem a abordagem de cada um com as nossas palavras.

"Completo" aqui é sinal de esforço e acabamento, não nota de qualidade. O G4 não publicou avaliação de nenhum PR.

---

## 1. Panorama das 10

| | Stack | Publicado | Score | Validação |
|---|---|---|---|---|
| A | Python gera JSON + React | Sim, abre | Chance de ganhar nos próximos 30 dias pela idade do deal; fila = valor × chance | Backtest em 4 cortes de 2017 contra "por valor", "mais novo primeiro" e acaso; teste de permutação por variável |
| B | Python stdlib + HTML/JS | Sim, abre | Sem nota: 3 colunas (negociar / qualificar / confirmar ou encerrar), ordem por preço dentro da coluna | Testou e reprovou regressão logística; backtest em 5 datas com IC por bootstrap; decompõe o ganho |
| C | Streamlit + SQLite | Sim, mas **dormindo** na visita (precisa acordar) | 45% win rate do vendedor suavizado + 35% preço + 20% urgência por idade | Só checagens de soma |
| D | Next.js | Sim, abre (o README diz que não estava) | Índice de saúde por evidência registrada pelo vendedor + score histórico dominado pelo estágio | Sem backtest |
| E | FastAPI + React em Docker | Não (só local) | p̂ por encolhimento × valor × urgência, convertido em percentil; eixos extras de confiança e estado | O mais rigoroso: holdout temporal, permutação com correção múltipla, poder estatístico |
| F | React no navegador | Sim, abre | Preço × chance de ganhar em 90 dias pela faixa de idade, em escala log | Backtest em 4 datas contra "por valor" e acaso, com IC |
| G | Next.js | Sim, abre | Afinidade vendedor × produto 50% + momento 31% + carga 19%, só para os deals "vivos" | Backtest com um corte; a ordem no meio da fila não se sustenta |
| H | Next.js + Supabase + LLM | Sim, abre (entrada por seletor) | Pontos fixos: estágio/idade 30 + produto 25 + porte da conta 25 + vendedor 20 | Nenhuma contra desfecho (só testes unitários) |
| I | FastAPI + HTML/Three.js (+ Streamlit) | Não (só local) | Chance por produto/vendedor encolhida × curva de idade × multiplicador de trimestre; valor por dia restante | Backtest no 4º tri contra "por preço"; descartou modelo por vazamento |
| J | Streamlit | Sim, abre | 55 idade + 20 encaixe vendedor × produto + 25 valor log; categorias mandam, score desempata | Regressão logística temporal + backtest em 37 cortes; empata com "mais novo primeiro" e diz isso |

---

## 2. Quem tratou o que os nossos dados mostram

✅ tratou · ◐ parcial ou com erro · ✗ não tratou

| Achado (ver `analysis/findings.md`) | A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|---|
| **Chance plana** (nenhum atributo separa Won de Lost) | ✅ | ✅ | ◐ usa vendedor com 45% | ◐ sem medir | ✅ | ✅ | ◐ usa vendedor × produto com 50% | ✗ | ◐ | ✅ |
| **81% do Engaging além de 138 dias** | ✅ | ✅ | ✅ | ◐ outro corte | ✅ | ✅ | ✅ | ◐ corte em 90 d | ◐ corte em 110 d | ✅ |
| **68% dos abertos sem conta** | ✅ tarefa | ✅ tarefa | ◐ tira do resumo | ✅ fila à parte | ✅ baixa a confiança | ◐ só mostra | ✅ balde próprio | ✗ penaliza | ✅ neutro | ✅ fora do score |
| **Data de referência fixa** (2017-12-31) | ✅ | ✅ | ✅ (corrigiu o uso da data de hoje) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GTXPro × GTX Pro** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ | ✅ |
| "Deal velho ganha mais" vem do **corte de 2016 e do calendário** | ◐ corrigiu o viés de sobrevivência, mas ainda lê como sinal | ✗ | ✗ penaliza linear após 88 d | ✗ | ✗ leu como sinal | ✅ excluiu a coorte de 2016 e mostrou que o efeito das 2 semanas some dentro do trimestre | ✗ leu como sinal | ✗ | ✗ curva arbitrária | ◐ corrigiu artefato de censura depois de revisão externa |
| **Fim de trimestre** (80% × ~50%) e o que fazer com ele | ✅ fora do score: diz quando o ganho é registrado | — | — | — | — | ✅ fora do score: vale para todos | — | — | ◐ multiplicador ×1,3 sem base | — |
| **Dados parecem sintéticos** (fim de semana = 2/7, vendedores iguais ao acaso) | não encontrado em nenhum dos 10 | | | | | | | | | |

"—" = não encontrado nos arquivos lidos.

Leitura: **os cinco achados que o baseline.md tratava como diferencial já são o padrão entre os melhores.** Seis das dez citam os mesmos números (63,2%, 138 dias, 1.291 / 81%, 1.425 / 68%, 1.480 deals de GTXPro). Para quem olhou os dados, eles são o ponto de partida, não o diferencial.

Os três itens do fim da tabela separam os melhores. Calendário e coorte de 2016 já foram achados por F (e o fim de trimestre também por A). Só o diagnóstico de dados sintéticos não aparece em nenhum dos dez.

---

## 3. Padrões comuns (o "segundo baseline")

- **Stack.** Metade em React/Next na Vercel ou GitHub Pages; o resto em Streamlit ou FastAPI. Dois não publicaram, e um link publicado estava dormindo na hora da visita.
- **Score.** Nenhum usa ML em produção; três testaram e descartaram com evidência. O formato dominante é **valor do produto (muitas vezes em escala log) × uma curva de idade**, com os deals acima de 138 dias tirados da fila principal. Três deles (A, F, J) chegam a uma fórmula quase igual à nossa proposta atual.
- **Ações.** Todos separam o pipeline em 3 ou 4 grupos com verbo: algo como focar, requalificar ou cadastrar, e encerrar. Os nomes variam, a ideia é a mesma.
- **Explicação.** Frases por componente com números dos dados, mais pontos por componente num detalhe. Dois somam um assistente de LLM ao lado.
- **Manager.** Tabela por vendedor com deals parados e valor; os melhores mostram "pipeline do CRM × pipeline vivo".
- **Validação.** Backtest temporal contra "ordenar por valor" virou o padrão dos melhores. Dois (A e J) também compararam com "mais novo primeiro" e **a fila deles não venceu essa regra simples**; os dois admitem isso.
- **Process log.** Export do chat, registro de decisões e tabela de erros da IA corrigidos aparecem em quase todos. Um deles (J) também escreveu um baseline de "IA sozinha", como o nosso.
- **Persistência.** Três gravam a decisão do vendedor: banco local, navegador ou decisão em lote com desfazer.

---

## 4. Onde a nossa entrega se diferencia e onde corre risco

Comparação com o estado em 09/11/2026: `analysis/findings.md`, `scoring/desenho.md` (proposta, aguardando decisões D1–D4) e `app/` (rodando com o exemplo).

### Já se diferencia (manter e deixar visível)

1. **Diagnóstico de dados sintéticos.** Nenhum dos dez diz isso. É o tipo de julgamento que o G4 pede ("saber quando desconfiar") e muda o que o score pode prometer. Há uma evidência nova e forte para somar ao `findings.md`: **os 1.779 deals que fecharam no 1º mês de um trimestre levaram no máximo 13 dias** (mediana 7); quem fecha no 2º ou 3º mês leva até 125 e 138. Isso é regra de gerador, não comportamento de vendedor.
2. **Curva de idade e calendário, mais completos que o melhor concorrente nesse ponto (F).** F mostrou que o efeito das "2 primeiras semanas" some quando se controla pelo mês de **fechamento**. Conferi: é verdade (no 3º mês, rápidos 86% × lentos 81%). Só que o mês de fechamento não existe para um deal aberto. Controlando pelo mês de **início** (que existe), o efeito continua: 50% × 69%, 57% × 64% e 63% × 69% nos três meses do trimestre. A leitura certa é "sobreviver às 2 primeiras semanas ainda informa, e o mecanismo é o calendário do gerador". Nenhum dos dez chegou a essa distinção.
3. **Corte de "desistir" em 276 dias** (o dobro do recorde), separado de "requalificar". Os outros usam um corte só.
4. **App estático sem build**: abre em qualquer servidor, sem dormir e sem login, se for publicado num host estático.

### Risco de ficar igual

1. **Fórmula do score.** Valor em log (45) + curva de idade (35) é, na essência, o score de A, F e J. Para não ser "mais um", o diferencial tem que estar na validação e no que a tela faz com o score, não na fórmula.
2. **Validação sem "mais novo primeiro".** O plano em `scoring/desenho.md` compara com "por valor" e com o acaso. Dois concorrentes mostraram que "mais novo primeiro" empata ou vence. **Incluir essa comparação e publicar o resultado como sair.** Se a nossa fila não vencer, dizer isso, como os melhores fizeram.
3. **Componente `conta` como pontos (0 ou 20).** Tira 20 pontos de 68% do pipeline. O único concorrente que penalizou a falta de conta (H) é o mais fraco do grupo; os melhores tratam como tarefa de cadastro sem mexer na ordem. O argumento "nenhum deal fechado está sem conta" também pode ser artefato do gerador sintético (os dados não dizem por que só os abertos estão sem conta). **Ponto para o Leandro decidir (D2).**
4. **Peso do valor.** Com chance plana e conta binária, o score pode virar "ordenar por produto caro" dentro de cada grupo. Um concorrente mediu correlação de 0,90 entre o score dele e o preço e corrigiu. Medir e publicar a correlação score × preço.
5. **Ações focar/requalificar/desistir.** Todo mundo tem. O que diferencia é o que acontece depois do clique: nenhum dos dez mede quanto do pipeline foi limpo ou mostra ao manager quem já decidiu os parados. Hoje o nosso app não grava decisão nenhuma (só lembra o último vendedor).
6. **Prospecting (500 deals).** Ninguém resolveu bem; o nosso desenho usa a faixa de 0–14 dias por falta de data. Melhor dizer na tela que não há sinal para esses deals do que dar uma nota inventada.
7. **Process log e baseline.** Export do chat, decisões e erros da IA são o mínimo; um concorrente também fez baseline de IA. O nosso fica acima se o `decisoes.md` mostrar as escolhas do Leandro contra a proposta da IA (já mostra: decisão 10).
8. **Publicação.** Dois dos dez não publicaram e um estava dormindo. Publicar num host estático e testar o link de uma janela anônima antes do PR.

---

## 5. Nota — correspondência com os PRs

PRs do repositório oficial `Gestao-Quatro-Ponto-Zero/ai-master-challenge`: A = 239, B = 197, C = 75, D = 238, E = 110, F = 175, G = 124, H = 25, I = 200, J = 129. Leitura feita em 09/11/2026; os PRs podem ter mudado depois.
