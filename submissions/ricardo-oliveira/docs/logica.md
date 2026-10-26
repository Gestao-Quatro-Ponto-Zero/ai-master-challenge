# Lógica: que critérios entram na prioridade e por quê

A versão completa, com cada decisão e o porquê, é o SOP (abaixo). Aqui, o resumo que o código executa.

## O que os dados mostraram

- 8.800 oportunidades, 85 contas, 35 vendedores em 6 times e 3 escritórios. Período: out/2016 a dez/2017. "Hoje" nos dados é 31/12/2017.
- Toda conta já compra. 88% dos ganhos são recompra de um produto que a conta já tinha. De 8 a 29 vendedores ganharam deal na mesma conta: não existe dono de conta.
- 68% dos deals abertos (1.425 de 2.089) não têm conta, em todo time, região e produto. Processo do CRM.
- Nenhum atributo da conta mostrou diferença confiável na chance de fechar: 61% a 65% em todo corte (porte, setor, idade, sede, região, vendedor, manager).
- Deal perdido morre cedo (metade em 14 dias). Deal aberto há mais de 30 dias ganha 68%; há mais de 90, 71%. Nenhum deal fechou depois de 138 dias, nem ganho nem perdido (limite do arquivo).
- Cada conta recompra o mesmo produto a cada 34 dias, em média, com muita variação.

## As regras, na ordem em que o código decide

1. **Deal sem conta** vai pra fila "identificar a conta" (prazo de 10 dias úteis, escala pro manager). Fica com quem está nele.
2. **Deal de GTK 500** vai pra um dos três especialistas, que age junto com o dono da conta.
3. **Deal vivo** (até 138 dias desde o engajamento) fica com o vendedor atual até ganhar ou perder.
4. **Todo o resto** vai pro dono da conta (modo Carteiras) ou fica com o vendedor atual (modo Como está hoje). A prioridade é a mesma nos dois modos.
5. **Troca feita pelo manager** dentro do time e da faixa de 10% substitui o dono sugerido.

## A prioridade do dia (por vendedor)

| Passo | Quem entra | Por quê |
|---|---|---|
| 1 | Deal vivo em produto fora da janela de recompra ou entrando nela em até 30 dias | Motivo pra ligar e oportunidade no CRM ao mesmo tempo |
| 2 | Os outros deals vivos | Ainda dentro do ciclo; nada fecha depois de 138 dias |
| 3 | Deals antigos em produto entrando na janela ou pouco fora dela (até 30 dias); os muito fora vão pro fim, como recuperação | O dono requalifica em 30 dias ou fecha como perdido |
| 4 | O resto, produto ainda dentro da janela | Manter contato |
| Confirmar | Outro vendedor (não o do deal) fechou o mesmo produto na conta depois de o deal abrir | Confirmar com a conta: mesmo pedido (juntar ou fechar como perdido) ou demanda separada (o deal volta pros passos). Nunca encerrar sem perguntar |

Recompra sem deal: pares conta e produto da carteira do vendedor na hora de recomprar e sem nenhum deal aberto no CRM (aba `Recompra sem deal`, 103 de 383) entram no Meu dia depois dos vivos, com a ação "abrir o deal e ligar" e um botão Feito. Onde já existe um deal a confirmar pro mesmo par, a aba manda confirmar esse deal em vez de abrir outro. É o relógio da conta, com ou sem CRM.

Deals sem conta: cinco por dia (`Hoje!B14`) entram na lista do vendedor depois dos vivos, vivos primeiro e depois pelo preço, com a ação "identificar a conta". Identificada no app, a conta entra em `sales_pipeline!J` e o deal passa a seguir as regras acima.

Cada deal mostra o porquê: o motivo do ICP da conta (receita ou setor contra a regra), o ritmo de recompra daquele produto naquela conta (intervalo médio, número de compras, última compra, e um aviso quando o atraso passa do dobro do ritmo), a idade do deal contra o ciclo normal e o limite, e, quando outro vendedor fechou o mesmo produto na conta depois de o deal abrir, quantas vezes, quem e há quantos dias. Esse último é o sinal mais forte que o dataset tem sobre conta sem dono: 464 dos 501 deals abertos em Engaging com conta (69 dos 89 vivos). O que ele não prova é que o pedido é o mesmo: no backtest esses deals fecharam ganhos em 58% contra 62% dos limpos. Por isso o bloco é Confirmar, não Encerrar.

Só deals limpos entram nos passos 1 a 4. Dentro de cada passo: **urgência da recompra** (dias até a janela; no passo 3 os muito vencidos por último), depois **valor do deal**, depois **tier de ICP**. A regra original era ICP antes de valor; o backtest, comparando só essas duas ordens sem a urgência na frente, mostrou 26% mais receita nos 18 primeiros com a mesma taxa de ganho, então inverti o desempate (chave em `Hoje!B13`). A urgência vem antes da chave: com ela, a ordem em uso ganha mais deals e menos receita (ver o backtest abaixo). Deal marcado "feito" hoje vai pro fim da lista de hoje (na planilha, pela chave de ordenação; o app só lê) e volta amanhã pelas regras. Deal confirmado como demanda separada sai do bloco Confirmar e volta pros passos.

## ICP (valor em jogo, não chance de ganhar)

- ICP 1: receita de US$ 3 bi ou mais, ou setor software (US$ 169 mil por conta nos 14 meses).
- ICP 2: receita entre US$ 1 e 3 bi (US$ 122 mil).
- ICP 3: abaixo de US$ 1 bi (US$ 84 a 100 mil).
- Um ICP só pras três regiões. Subsidiária, sede e ano de fundação não passaram no critério (20% a mais de receita, 5 contas ou mais).

## O que ficou de fora e por quê

- **MEDDPICC:** seis das oito letras não existem no CRM. Virou recomendação de campos.
- **Win rate por atributo:** não há sinal confiável neste arquivo. Entraria num CRM real.
- **Especializar GTXPro:** 24 vendedores vendem com a mesma taxa; o time com mais volume tem a menor. Não.
- **Encerrar deal atropelado sem perguntar:** a compra posterior de outro vendedor não prova que é o mesmo pedido (pode ser outro departamento, outra quantidade, compra recorrente), e o backtest não separa esses deals dos limpos. Virou confirmação, com o campo de "pedido" como recomendação de CRM.

## O backtest, e o que ele pode dizer

Aba `Backtest`, snapshot editável (30/09/2017): 1.401 deals em Engaging com conta abertos naquele dia. Top 18 por vendedor, exato (537 deals em toda ordem, empates desfeitos pela linha). Valor depois de ICP: 239 ganhos e US$ 815 mil. Acaso pareado por vendedor (mesmo N de cada um, com a taxa e a receita média dele): 215 e US$ 650 mil. Só preço: 221 e US$ 905 mil. Mais novo primeiro: 293 e US$ 688 mil. Ordem em uso (urgência, valor, ICP, atropelados no fim): 270 e US$ 624 mil. Leitura exploratória, escrita na própria aba: um snapshot, dado gerado, cortes de 57 e 138 dias calculados no arquivo inteiro, nenhuma prova de causa.

## Fontes

- SOP completo em português: [`sop-lead-scorer.md`](./sop-lead-scorer.md).
- Fórmulas e configuração da planilha, aba por aba: [`../solution/sheet`](../solution/sheet).
- Narrativa do processo: [`../process-log/00-narrativa.md`](../process-log/00-narrativa.md).
