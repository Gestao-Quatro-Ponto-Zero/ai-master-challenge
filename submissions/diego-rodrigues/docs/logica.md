# Lógica: o que a ferramenta usa, o que testou e o que descartou

Todo número aqui sai de `solution/avaliacao/numeros.py` (saída em `docs/numeros-saida.txt`).

## O que o teste mede

O backtest volta a seis datas do segundo semestre de 2017 (de 3 de julho a 20 de novembro). Em cada data, a ferramenta vê só o que existia naquele dia. O desfecho real, que só o teste enxerga, mede quanto cada política teria ganho nos 28 dias seguintes. Os cortes são de quatro semanas, então as janelas de medição não se sobrepõem.

Comparamos cinco políticas, cada uma escolhendo até 5 deals por vendedor:

- **Relógio** (a ferramenta): ordena pela fila e, dentro da fila, pelo valor esperado — preço de tabela multiplicado pela chance aprendida na faixa de idade e na altura do trimestre. Não é ordenar só pelo tempo: uma versão que ignorasse o valor e ordenasse só pela chance perde para preço e prazo (razão 0,66). O que vence preço e prazo é o valor ponderado pela chance, não o tempo sozinho.
- **Preço e prazo**: maior preço de tabela entre os vivos, com desempate pelo prazo. É a melhor alternativa simples que a equipe usaria hoje.
- **Preço, até 138 dias**: maior preço entre os deals com menos de 138 dias de idade. É o que a regra de ciclo sozinha faria.
- **Aleatório**: sorteio entre os vivos, média de 200 rodadas. Cada rodada sorteia com um número de controle fixo, então o resultado se repete.
- **Oráculo**: quem conhece o futuro. É o teto.

## Regras aceitas e a evidência

| Resultado | Valor |
|---|---|
| Valor ganho: relógio | US$ 1.097.324 |
| Valor ganho: preço e prazo | US$ 842.462 |
| Valor ganho: preço, até 138 dias | US$ 867.889 |
| Valor ganho: aleatório (média) | US$ 318.622 |
| Valor ganho: oráculo | US$ 2.666.327 |
| Taxa de acerto: relógio | 22,7% |
| Taxa de acerto: preço e prazo | 15,4% |
| Taxa de acerto: aleatório | 14,7% |

A ferramenta captura 41% do teto. Preço e prazo captura 32%.

Razão de valor ganho, relógio sobre preço e prazo: **1,30**, com intervalo de confiança de 95% entre **1,13** e **1,52**. O intervalo não cruza 1. A reamostragem é por vendedor, porque é o vendedor que torna os deals independentes entre si. Relógio sobre preço, até 138 dias: 1,26 (IC de 1,13 a 1,44).

O ciclo máximo (138 dias) e a tabela de destino por faixa de idade são aprendidos do histórico conhecido em cada data. A regra do fim do trimestre é diferente: o formato (fim do trimestre seguinte ao engajamento) é escolhido à mão; o histórico só decide se ela liga ou desliga (ver "Aprendido do histórico e configurado à mão" abaixo). A tabela de destino é calculada nas datas análogas (início de cada trimestre anterior); por isso uma faixa de idade alta com `p_decide` perto de zero é uma propriedade dessa posição no trimestre, não da idade isolada — na metade de um trimestre, a mesma faixa decide bem mais.

## Regras rejeitadas e o número que as derrubou

Teste: o atributo prediz se o deal ganha? Embaralhamos o resultado 1.000 vezes, dentro de cada mês do trimestre, e medimos a chance de o embaralhamento produzir uma diferença igual ou maior que a observada. Um p-valor abaixo de 0,05 indicaria sinal.

| Atributo | p-valor | Conclusão |
|---|---|---|
| Conta | 0,524 | sem sinal |
| Vendedor | 0,141 | sem sinal |
| Vendedor, controlado por gerente | 0,116 | sem sinal |
| Gerente | 0,482 | sem sinal |
| Região | 0,299 | sem sinal |
| Setor da conta | 0,541 | sem sinal |
| Porte da conta | 0,983 | sem sinal |
| Produto | 0,465 | sem sinal |
| Vendedor × produto | 0,485 | sem sinal |

Nenhum atributo chega a 0,05. Por isso nenhum entra como regra da ordem. Para a pergunta "quando este deal decide?", o atributo não ajuda; quem decide é o relógio do trimestre.

**Taxa de acerto relógio ÷ aleatório = 1,54.** Não usamos isso como métrica. A taxa de acerto muda com a taxa-base do negócio (cerca de 15% aqui), então a razão entre taxas exagera ou esconde o efeito. A métrica do projeto é valor ganho, com intervalo de confiança.

## O que "nenhum vencido foi ganho" prova, e o que não prova

Dos 734 negócios distintos classificados como vencidos nos seis cortes, nenhum foi ganho em momento algum do export — nem nos 28 dias seguintes ao corte, nem depois. A afirmação é exata, mas o que ela mostra é mais estreito do que parece: 733 dos 734 nunca chegaram a fechar (seguem em `Engaging` até o fim do export, sem `close_date`), e o único que fechou foi perdido — exatamente o fechamento fora do prazo que serviu para aprender a regra do trimestre. Então "nenhum foi ganho" não é uma confirmação independente de que a regra está certa; é o mesmo fato do dado visto pelos dois lados (o fechamento que define a regra e os negócios que a regra classifica). Dentro deste export, negócio que passa do fim do trimestre seguinte simplesmente para de se mover — não sabemos se ele seria perdido, reaberto ou se o padrão é artefato do gerador sintético (ver `docs/limitacoes.md`).

## Um vazamento que encontramos, e reduzimos

No export, o campo de conta aparece preenchido em todos os 6.711 deals fechados e falta em 1.425 dos 2.089 abertos. Como nenhum fechado está sem conta, a ausência de conta carrega a informação do desfecho. Não sabemos o mecanismo exato de preenchimento do CRM; o que medimos é a consequência para o teste.

Por isso, os testes de atributos usam só deals com conta preenchida (3.001). Na primeira versão do teste, deals sem conta entravam, e o vendedor parecia ter sinal (p = 0,012). O sinal era do vazamento, não do vendedor. Regra para a ferramenta: presença ou ausência de conta nunca entra como sinal.

**Isso reduz o vazamento, mas não o remove por completo.** `recortar` não apaga o campo `account` nos negócios que, numa data de corte, ainda não têm desfecho conhecido: como a conta só existe no export final, filtrar "deals com conta preenchida" ainda condiciona numa informação que só existe depois do desfecho — da mesma categoria do problema que o filtro tentou resolver, só que residual. O efeito provável é na taxa-base da permutação, não no p-valor (o filtro é igual para todos os grupos comparados), mas é uma limitação do dataset que não conseguimos contornar por inteiro, e não só do método de teste.

Um segundo ponto menor, sem efeito sobre o resultado em produção: `motor/carregar.py` decide se descarta os deals em Prospecting sem data comparando a data de referência com a maior data de fechamento de todo o export carregado — no backtest, isso usa o export completo (passado e futuro do corte), não só o que seria conhecido naquela data. Em produção, o export carregado é sempre o atual, então essa comparação não vaza futuro de verdade; no backtest, é uma inconsistência entre o que o motor "vê" e o que ele usaria para essa decisão específica.

## Aprendido do histórico e configurado à mão

- **Aprendido, em cada data**: ciclo máximo (138 dias na data de referência), se a regra do fim do trimestre está ativa (ativa quando menos de 0,1% dos fechamentos passam do prazo), tabela de destino por faixa de idade e carga de referência por vendedor. O que é aprendido aqui é o liga/desliga e os números, não o formato da regra.
- **Escolhido à mão e confirmado pelo histórico**: o formato "fim do trimestre seguinte ao engajamento" é uma hipótese de calendário nossa, testada contra o dado — não uma regra que o dado descobriu sozinho. A evidência dentro deste export é forte (6.710 dos 6.711 fechamentos conhecidos cabem nela), mas é uma hipótese confirmada, não uma regra aprendida do zero. Dizer "aprendida, não escrita à mão" para essa metade é impreciso; o correto é "a forma é nossa, o liga/desliga é do dado".
- **Configuração de operação**, em `solution/config.json`: 28 dias de horizonte, 5 deals por vendedor na lista do dia, chance mínima de 5% para entrar em "fechar", bordas das faixas de idade, mínimo de 30 observações por faixa, tolerância de 0,1% para a regra do trimestre, mínimo de 500 fechamentos para ativar essa regra.

Uma faixa com menos de 30 observações é juntada com a vizinha mais velha. Isso afeta uma data do backtest (31 de julho, faixas de 106 a 138 dias). Sem essa regra, o protótipo põe 1.887 deals em `fechar` nessa data; com ela, são 1.893. Os valores de ouro do protótipo foram mantidos onde a regra não mexe (relógio, preço e oráculo). O aleatório mudou porque passou a sortear por deal, e não por posição na lista.

## Fontes

- A regra do fim do trimestre seguinte é medida aqui (1 fechamento depois do prazo em 6.711). Não a atribuímos a outra submissão: a descrição do PR #242 que lemos fala do achado de que negócios vencidos não ganham, não dessa regra. Só creditaremos se o código do PR for conferido.
- O PR #240 (submissão de outro participante) foi lido apenas pela descrição, que não menciona efeito de calendário. Não citamos o que ele descartou.
