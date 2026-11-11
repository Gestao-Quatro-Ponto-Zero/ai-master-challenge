# Resumo executivo

Todo número desta página sai de `solution/avaliacao/numeros.py` e do build de referência (01/01/2018). O que é premissa está declarado como premissa.

## Medido: três quartos do pipeline aberto já não fecha

Dos **US$ 4.966.215** de preço de tabela em negócios abertos, **US$ 3.656.299 (73,6%)** estão em negócios que passaram da janela de decisão observada. Isso não é projeção: nos seis cortes do teste de volta ao passado, **734 negócios distintos** foram classificados como vencidos, e **nenhum deles foi ganho** — nem nas quatro semanas seguintes, nem em momento nenhum do restante do export.

O forecast da operação é construído sobre esse volume. Sobram **115 negócios vivos**, com **US$ 235.930** de preço de tabela, distribuídos em **17 dos 35 vendedores** do cadastro.

Há ainda **500 negócios em Prospecting**, somando **US$ 1.073.986**, que não têm data de engajamento registrada. Não é possível estimar quando decidem, porque não se sabe quando começaram. É o maior bloco de valor sobre o qual a ferramenta não opina.

## Medido: priorizar pela janela de decisão rende mais que priorizar por valor

Priorizar pelo relógio do trimestre captura **1,30 vez** o valor da melhor alternativa honesta — ordenar por preço de tabela e prazo, que é o que a operação faz hoje —, com intervalo de confiança de 95% entre **1,13 e 1,52**. O intervalo não cruza 1, então a diferença não é ruído. A taxa de acerto é de **22,7%** contra **15,4%**.

A vantagem não é uniforme: o relógio vence em cinco dos seis cortes, e perde no corte de 23/10/2017. O que sustenta a conclusão é o intervalo de confiança, não a repetição corte a corte.

Nenhum atributo do negócio prevê quem ganha. Conta, vendedor, gerente, região, setor, porte e produto foram testados contra o resultado real, e nenhum ficou abaixo de 0,05 de p-valor (`docs/logica.md`). A ferramenta não diz quem ganha, porque o dado não sustenta essa afirmação. Ela diz quando negócios semelhantes costumam decidir.

## Premissa: a conta de horas, como ponto de equilíbrio

A diferença medida entre as duas ordens é de **US$ 1.416 por vendedor a cada quatro semanas** (US$ 254.862 no total, 30 vendedores, seis cortes). Esse é o valor que a ferramenta precisa não consumir em tempo de vendedor para se pagar.

Quanto isso vale em horas depende do custo-hora, que não temos. A conta fica assim: a US$ 25 a hora, o ponto de equilíbrio é de 57 horas por vendedor a cada quatro semanas; a US$ 50, são 28 horas; a US$ 100, são 14 horas. A ferramenta é uma lista aberta na segunda-feira, bem abaixo de qualquer um desses limites — mas a conta só fecha de verdade com o custo-hora real da operação.

**A ressalva que importa:** os US$ 1.416 vêm de simulação sobre dados históricos, não de operação real. É exatamente isso que o piloto de `docs/experimento.md` mede, com grupo de controle.

## A frase para a diretoria

> Três quartos do pipeline que entra no forecast não fecham mais, e isso é medido: dos 734 negócios que o histórico classificaria como vencidos, nenhum foi ganho. O que sobra vivo são 115 negócios em 17 dos 35 vendedores. Priorizar esses negócios pela janela de decisão rende 1,30 vez o que priorizar por valor rende, com intervalo de confiança que não cruza 1. Em 90 dias medimos esse ganho com grupo de controle antes de expandir.

## O que o próximo passo mede

O piloto sorteia negócios dentro de cada vendedor, usando cada vendedor como seu próprio controle. A métrica primária é a taxa de decisão em 28 dias, cuja base medimos em **17,3%**. Valor ganho entra como métrica secundária e não pode ser critério de aceite: detectá-lo exigiria 109 vendedores por braço, e a operação tem 30.
