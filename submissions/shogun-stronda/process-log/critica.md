# Revisão crítica independente

Um sub-agente do Claude Code revisou a solução **sem acesso ao raciocínio do builder**. Recebeu só o brief, o código, os dados e a instrução de ser duro e reprovar. Ele não editou arquivos. Escreveu os próprios scripts para reproduzir os números a partir dos CSVs crus.

## O que reproduziu

Todos os números de destaque: teto de 138 dias, 1.291 zumbis (81% do Engaging), 51% das perdas até o dia 14, 2.089 abertos, 1.425 sem conta, os 12 testes, zero erros no console.

## Nota da v2: 6/10

O crítico avaliou a v2 (Valor 50 + Chance temporal 35 + Urgência 15). Os findings e o que fiz com cada um:

| # | Finding | Decisão |
|---|---|---|
| 1 | **A "Chance" temporal reprova no meu próprio gate.** Backtest por snapshot (deals abertos no corte, idade no corte): AUC 0,505 a 0,555 | **Aceito, foi o mais importante.** Implementei o backtest por snapshot em 3 cortes com IC por bootstrap (`snapshot()`, `backtest()`). Tirei a probabilidade do score. v3 = Valor + Momento, apresentado como política, não previsão |
| 2 | Score é quase um sort por preço (Spearman 0,77); `P_LO/P_HI` esticava uma variação de 1,2x em 28 pontos | **Aceito.** Sem o esticamento. Assumido e explicado em `logica.md` ("Consequência assumida") |
| 3 | "Fechar esta semana" nunca disparava para 3 dos 7 produtos (exigia ticket ≥ US$ 1,2k) | **Aceito.** Ação agora depende só do momento. Teste `test_action_independent_of_price` |
| 4 | Penhasco no dia 138 e urgência invertida: deals perto do teto tinham menos urgência que deals novos | **Aceito.** Novo estado "reta final" (90 a 138 dias) com 35 pts, ação "Empurrar fechamento" e "faltam X dias" |
| 5 | Forecast "realista" inflado: Prospecting recebia 63% de chance, mas Prospecting → Won nunca é observado | **Aceito.** Prospecting e zumbis têm chance e valor esperado `None`. Valor esperado só de Engaging vivo: US$ 486 mil, não US$ 1,16 mi |
| 6 | Zumbi afirmado forte demais ("forecast inflado 4x", "encerrar o resto"); 758 zumbis engajados no 3º tri podem ser artefato do gerador | **Aceito.** Ação virou "Verificar no CRM"; texto diz "inconsistente com o histórico". Mantive o máximo (138) em vez de p99: é estável desde maio/2017 e qualquer deal acima dele está, por definição, fora de tudo já observado |
| 7 | Higiene: `critica.md` citado e inexistente; `submissions/` ignorado pelo `.gitignore` do repo (PR sairia vazio); `__pycache__` e `.playwright-cli` iriam junto | **Aceito.** Este arquivo; `git add -f` só da pasta; `.gitignore` local na submissão |
| 8 | Gate frágil: um corte só, sem IC, 0,53 escolhido depois de ver os dados | **Aceito.** 3 cortes, IC 95% por bootstrap, gate 0,55 em todos os cortes |
| 9 | Off-by-one: deal aberto há `a` dias terá ciclo ≥ `a+1` | **Aceito.** `survival[age + 1]` + teste |
| 10 | CSV ilegível no Excel pt-BR; exportar na aba Time baixava deals, não o time; `revokeObjectURL` imediato; injeção de fórmula | **Aceito.** `;` + BOM, export do time, revoke com atraso, prefixo `'` em `=+-@` |
| 11 | Filtros de ação, busca e aba persistiam: segunda de manhã abria filtrado | **Aceito.** Só região, manager e vendedor persistem. KPIs com `aria-pressed` |
| 12 | Aba Time ignorava o filtro de ação, mas o mostrava | **Aceito.** Ação e busca desabilitadas na aba Time |
| 13 | Gaveta: sem `aria-modal`, foco não volta | **Aceito.** `aria-modal`, foco volta à linha |
| 14 | Central vira lista de Prospecting ordenada por preço | **Parcial.** É o que os dados permitem: Central tem 500 Prospecting e 5 Engaging vivos. Ação clara ("Avançar para Engaging") e virou recomendação nº 2 no README |

Nenhum finding foi descartado sem resposta. Os testes subiram de 12 para 17 (snapshot sem vazamento, off-by-one, ação independente de preço, chance desconhecida sem valor esperado, IC).
