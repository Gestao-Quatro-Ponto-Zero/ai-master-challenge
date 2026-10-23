# ADR 0011: Receita esperada (chance pela idade × preço de tabela)

**Status:** aceita

## Contexto

O vendedor quer saber onde focar e quanto isso deve render. O grupo já sai da idade ([ADR 0004](0004-blocos-por-idade-valor-so-ordena.md)) e cada negócio mostra a chance histórica da faixa dele. Faltava juntar a chance com o valor do negócio num número que ele entenda, sem prometer o que o dado não sustenta.

## Decisão

- **Por negócio:** receita esperada = taxa de ganho da faixa de idade no replay (corte em 30/09/2017, ganhos até 31/12/2017), **sem arredondar**, × o preço de tabela do produto (`Avaliacao.esperado`, no contexto `score`). Nos ganhos, a mediana do `close_value` é 1,0 × o preço de tabela nos 7 produtos.
- **Textos (na política, editáveis):** com chance acima de zero, "Deve render cerca de US$ {esperado} em 3 meses (estimativa pela idade)."; com chance zero (acima de 90 dias), "Pela idade, quase nada deve render."; sem data de início, "Sem data de início: não dá pra estimar.". O preço de tabela aparece só no detalhe do negócio, como "Preço de tabela: US$ {valor}".
- **Ordem:** dentro do grupo, a receita esperada ordena (maior primeiro; empate, o preço maior, depois a idade menor e o id). Ela nunca muda o grupo.
- **Topo da lista:** a soma da receita esperada dos negócios abertos do vendedor ("Dos seus negócios abertos hoje, devem sair cerca de US$ {total} nos próximos 3 meses."), com o aviso "Estimativa pelo histórico: chance pela idade × preço de tabela. Não conta negócios novos que vão entrar. Não é promessa." e quantos negócios sem data ficam fora da conta.
- **Comissão:** o dataset não tem comissão. O campo "Sua comissão (%)" começa vazio e fica no navegador; preenchido, mostra a estimativa da comissão sobre o total. Nenhum percentual é sugerido.

## Consequências

- Na base inteira, o total é US$ 46.487; 1.479 negócios têm receita esperada zero e os 500 sem data ficam fora (`packages/dominio/src/aplicacao/integracao.test.ts`).
- Backtest dentro da amostra: nos 2.409 negócios abertos em 30/09/2017, a mesma conta previu US$ 1.284.794, e os ganhos até 31/12/2017 fecharam US$ 1.251.928 (mesmo teste). As taxas vêm desse replay, então o teste mostra coerência, não previsão fora da amostra.
- O total não é a receita do período: não conta os negócios que vão entrar. A tela e o README dizem isso.

## Alternativas consideradas

- **Ordenar pelo preço de tabela:** põe um negócio parado há 300 dias, de produto caro, na frente de um que ainda fecha.
- **Usar a chance arredondada ("3 em 10"):** distorce o valor (6,7% viraria 10%).
- **Prever a receita do trimestre:** pediria modelar os negócios que ainda vão entrar, sem dado para isso.
