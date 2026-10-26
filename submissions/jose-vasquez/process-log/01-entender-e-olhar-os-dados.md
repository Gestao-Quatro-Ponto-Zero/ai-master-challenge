# Etapas 1 e 2 — Entender o problema e olhar os dados

Ferramenta: Claude Code (Claude Opus 5.5), com Python + pandas.

## Etapa 1 — O problema antes dos dados

Antes de abrir qualquer arquivo, pedi à IA para explicar o desafio em linguagem simples: a situação, a reclamação da chefe de vendas e o que o G4 exige. Só segui depois de concordar com o resumo:

- **Reclamação 1:** os vendedores perdem tempo com vendas que não vão fechar.
- **Reclamação 2:** deixam esfriar as vendas boas.
- **Pedido:** algo simples, que funcione, para o vendedor abrir na segunda-feira e saber onde focar.

Decisões minhas nesta etapa:

- **A ferramenta tem dois usuários.** O vendedor ("as 5 da semana") e a chefe de vendas, que foi quem fez o pedido ("o pipeline de verdade").
- **A arquitetura fica documentada desde o início** ([`docs/arquitetura.md`](../docs/arquitetura.md)), antes de qualquer código.
- **Conferi que os dados são os oficiais:** 85 clientes, 7 produtos, 35 vendedores e 8.800 vendas, como o desafio descreve.

## Etapa 2 — O que os dados mostram

Script: [`solution/analise/01_dados.py`](../solution/analise/01_dados.py). Cada afirmação abaixo sai dele.

### Qualidade dos dados

| Problema | Tamanho | O que fazer |
|---|---|---|
| Produto escrito "GTXPro" nas vendas e "GTX Pro" no catálogo | 1.480 vendas | Padronizar o nome |
| Setor escrito "technolgy" | 1 setor | Corrigir para exibição |
| Vendas em prospecção sem data de início | 500 (todas) | Não dá para medir o tempo delas |
| Vendedores sem nenhuma venda | 5 de 35 | Não aparecem na ferramenta |
| **Vendas abertas sem cliente** | **1.425 de 2.089** | Ver "armadilha" abaixo |

### Hipóteses testadas

| Hipótese | Teste | Resultado |
|---|---|---|
| Produto, setor, região, gerente ou porte do cliente mudam a chance | Taxa de ganho por grupo | Todos entre 60% e 66%. **Quase não mudam** |
| Alguns vendedores fecham muito mais que outros (55% a 70%) | Sorteio: embaralhar os resultados 1.000 vezes e ver se a mesma variação aparece por acaso | Por acaso aparece 0,035; real, 0,037. **33% de chance de ser só acaso**: não é confiável |
| A taxa do vendedor ou do produto se repete no tempo | Taxa da 1ª metade do período comparada com a 2ª | Correlação 0,23 (vendedor), 0,18 (produto), −0,13 (setor). **Quase não se repete** |
| Venda que passa de 90 dias fecha mais (71%) | Olhando só as encerradas | **Suspeito.** Só conta quem já fechou; as vendas que ficaram abertas para sempre não entram. Precisa de teste sem olhar o futuro (etapa 3) |

### O que os dados mostram de verdade

1. **Vendas perdidas morrem cedo.** Metade das perdas acontece em até 14 dias. As ganhas levam, no meio, 57 dias.
2. **Nenhuma venda da história levou mais de 138 dias.** Hoje, **1.291 das 1.589 negociações abertas (81%)** já passaram disso: US$ 3,2 mi de preço de tabela parado.
3. **O preço manda.** Vai de US$ 55 a US$ 26.768 (487 vezes), e o valor fechado é o preço de tabela (média 1,00). A chance varia pouco entre grupos.
4. **Armadilha do cliente vazio.** 1.425 vendas abertas não têm cliente, mas **nenhuma das 6.711 encerradas está sem cliente**. Ou o sistema só preenche o cliente no fechamento, ou são registros incompletos. Por isso, "ter cliente" não pode virar sinal da nota: seria usar informação do futuro.
5. **Região Central:** tem as 500 prospecções do dataset. As outras regiões não têm nenhuma.
6. **Fim de trimestre:** vendas encerradas em março, junho, setembro e dezembro foram ganhas 81% das vezes, contra 52% nos outros meses. Fica registrado; não serve para a nota, porque o mês de fechamento só se sabe depois.

### Onde a IA precisou de correção

- A conta "passou de 90 dias, fecha 71%" parece mostrar que venda antiga fecha mais. A própria saída do script marca o risco: **só conta quem já fechou**. Esse número não entra na nota até ser testado da forma certa (etapa 3).

### Conclusão para a nota

- **Entra:** o tempo de negociação (com teste sem olhar o futuro) e o preço.
- **Não entra:** vendedor, produto, setor, região, gerente e porte (não se repetem no tempo).
- **Não entra:** "ter cliente cadastrado" (armadilha).
