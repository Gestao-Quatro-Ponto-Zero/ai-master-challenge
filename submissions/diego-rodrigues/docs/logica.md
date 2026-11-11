# Lógica: o que a ferramenta usa, o que testou e o que descartou

Todo número aqui sai de `solution/avaliacao/numeros.py` (saída em `docs/numeros-saida.txt`).

## O que o teste mede

O backtest volta a cinco datas do segundo semestre de 2017 (de 3 de julho a 20 de novembro). Em cada data, a ferramenta vê só o que existia naquele dia. O desfecho real, que só o teste enxerga, mede quanto cada política teria ganho nos 28 dias seguintes. Os cortes são de quatro semanas, então as janelas de medição não se sobrepõem.

Comparamos cinco políticas, cada uma escolhendo até 5 deals por vendedor:

- **Relógio** (a ferramenta): ordena pela fila e pela posição dentro da fila.
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

A regra do trimestre e a janela de 138 dias são aprendidas do histórico conhecido em cada data. A tabela de destino por faixa de idade também. Ver a seção de configuração abaixo.

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

## Um vazamento que encontramos e removemos

No export, o campo de conta aparece preenchido em todos os 6.711 deals fechados e falta em 1.425 dos 2.089 abertos. Como nenhum fechado está sem conta, a ausência de conta carrega a informação do desfecho. Não sabemos o mecanismo exato de preenchimento do CRM; o que medimos é a consequência para o teste.

Por isso, os testes de atributos usam só deals com conta preenchida (3.001). Na primeira versão do teste, deals sem conta entravam, e o vendedor parecia ter sinal (p = 0,012). O sinal era do vazamento, não do vendedor. Regra para a ferramenta: presença ou ausência de conta nunca entra como sinal.

## Aprendido do histórico e configurado à mão

- **Aprendido, em cada data**: ciclo máximo (138 dias na data de referência), regra do fim do trimestre seguinte (ativa quando menos de 0,1% dos fechamentos passam do prazo), tabela de destino por faixa de idade e carga de referência por vendedor.
- **Configuração de operação**, em `solution/config.json`: 28 dias de horizonte, 5 deals por vendedor na lista do dia, chance mínima de 5% para entrar em "fechar", bordas das faixas de idade, mínimo de 30 observações por faixa, tolerância de 0,1% para a regra do trimestre, mínimo de 500 fechamentos para ativar essa regra.

Uma faixa com menos de 30 observações é juntada com a vizinha mais velha. Isso afeta uma data do backtest (31 de julho, faixas de 106 a 138 dias). Sem essa regra, o protótipo põe 1.887 deals em `fechar` nessa data; com ela, são 1.893. Os valores de ouro do protótipo foram mantidos onde a regra não mexe (relógio, preço e oráculo). O aleatório mudou porque passou a sortear por deal, e não por posição na lista.

## Fontes

- A regra do fim do trimestre seguinte vem da revisão pública do challenge (PR #242), citada no plano. **A conferência do conteúdo desse PR ainda não foi feita nesta versão.**
- O efeito de calendário discutido no PR #240 não foi conferido nesta versão.
