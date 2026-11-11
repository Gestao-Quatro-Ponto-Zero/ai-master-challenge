# Design

## Abordagens consideradas

1. **Ordem por preço de tabela, com desempate por prazo.** É o que o campo faz hoje sem ferramenta: olhar os maiores negócios abertos. Testada no backtest como `preco_prazo`.
2. **Ordem por preço entre deals dentro do ciclo observado (até 138 dias).** O que a fórmula ingênua de v1 faria. Testada como `preco_138`.
3. **Ordem pelo relógio do trimestre** (fila por estado aprendido + valor esperado na janela): a escolhida.
4. **Ordenar por probabilidade de ganho (AUC de atributos).** Rejeitada antes de entrar no backtest: nenhum atributo do deal prediz ganho (`docs/logica.md`, todos p > 0,05). Não há o que ordenar por "quem ganha".

## A rejeitada, com número

**Ordenar por preço (o que o campo faz hoje) rende 0,77× o valor do relógio do trimestre, com IC 95% de 0,66 a 0,88 — o intervalo não cruza 1.** Esse número é o inverso da razão relógio/preço e prazo de `docs/logica.md` (1,30, IC [1,13; 1,52]): 1/1,30 ≈ 0,77, e os extremos do IC invertem na mesma ordem (1/1,52 ≈ 0,66; 1/1,13 ≈ 0,88). A inversão preserva o intervalo porque a razão é positiva; é a mesma comparação lida ao contrário. O relógio ganha em 5 dos 6 cortes do backtest; no corte de 23/10/2017, preço e prazo ganha (US$ 150.104 contra US$ 133.640). O intervalo de confiança é o que sustenta a afirmação, não a consistência corte a corte.

Preço também perde na taxa de acerto: 15,4% contra 22,7% do relógio (`docs/numeros-saida.txt`). Mas essa comparação é secundária — ver a nota sobre taxa de acerto em `docs/logica.md`.

## Princípios

- **O score nunca promete quem ganha.** Só diz quando, historicamente, deals dessa idade decidiram. É a distinção que a Consultora do Empresário pede em B6: "não me diga quem vai ganhar... me dê contexto suficiente para eu saber onde vale colocar minha energia hoje" (P9).
- **Todo número citado sai de `avaliacao/numeros.py`.** Nenhum número aparece na tela, no README ou nos docs sem essa fonte única.
- **Nenhum limiar de fase escrito à mão.** Ciclo máximo, regra do trimestre e tabela de destino são aprendidos do histórico conhecido na data; `config.json` só guarda escolha de operação (horizonte, foco por vendedor, chance mínima), nunca leitura dos dados.

## Não-metas

- **Não prever quem ganha.** Fundamentado no próprio dado (nenhum atributo prediz ganho) e na premissa P9 (confirmada parcialmente: a Consultora lê percentual como janela, não como chance, desde que a ferramenta não finja prever o resultado).
- **Não ser ranking de obediência.** P7 (contrariada): marcar "não está vivo" não é neutro quando mexe no número do gerente (Caio, B7). P8 (indeterminada): a tela não decide se o gestor vai cobrar indivíduo; ela mitiga mostrando agregado por padrão.

## Anti-meta

**Não virar mais uma tela para alimentar.** A Embaixadora da Cultura nomeia o critério de morte em A3: "ela morre quando vira mais uma tela para alimentar... o sinal mais claro de que morreu é este: a liderança precisa fazer campanha para todo mundo abrir." O design não pede registro que não exista em algum lugar: a nota curta de exceção (P11) é o único campo novo, e só aparece quando o vendedor discorda do estado.
