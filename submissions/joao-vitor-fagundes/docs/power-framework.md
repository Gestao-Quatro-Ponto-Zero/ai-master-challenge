# POWER: Framework de priorização de oportunidades

O POWER transforma o histórico do CRM em um perfil explicável para o vendedor. Ele preserva quatro leituras quantitativas (P, O, W e E), consolida a ordem de atuação no POWER Priority e usa R para recomendar a próxima ação.

> A documentação visual, com fórmulas, legendas, exemplos e limitações, está em [`power-framework.pdf`](./power-framework.pdf) e [`power-framework.html`](./power-framework.html). A implementação reproduzível está em [`../solution/scripts/build_power_dataset.py`](../solution/scripts/build_power_dataset.py).

## PP: POWER Priority

Pergunta: considerando qualidade histórica, capacidade de execução, frescor e valor, qual oportunidade o vendedor deve priorizar?

A leitura do framework permanece sempre `P → O → W → E → R`: POWER. Dentro da equação, a hierarquia de influência definida pelo negócio é `P > E > W > O`. Ela é convertida em fatores pelo inverso da posição de importância:

| Pilar | Posição | Importância relativa | Fator inteiro |
|---|---:|---:|---:|
| P: Propensity | 1 | `1` | 12 |
| O: Opportunity Value | 4 | `1/4` | 3 |
| W: Warmth | 3 | `1/3` | 4 |
| E: Execution Fit | 2 | `1/2` | 6 |

Multiplicar `1`, `1/2`, `1/3` e `1/4` por 12 produz `12`, `6`, `4` e `3`. Como a soma dos fatores é 25:

`PP = (12P + 3O + 4W + 6E) / 25`

Equivalência: P contribui com 48%, E com 24%, W com 16% e O com 12%. Esses percentuais não foram escolhidos individualmente: derivam da ordem declarada. A ordem continua sendo uma decisão de negócio e deve ser validada com resultados futuros.

Exemplo real: oportunidade `FZWU2I30`, The New York Inquirer:

`PP = (12 × 64,85 + 3 × 20,48 + 4 × 53,88 + 6 × 64,50) / 25 = 57,69`

R não entra na equação. Ele interpreta PP e as evidências de P/O/W/E para recomendar a próxima ação.

## P: Propensity

Pergunta: negócios historicamente semelhantes costumam ser ganhos?

- Histórico: somente oportunidades `Won` e `Lost` disponíveis antes da oportunidade avaliada.
- Perspectivas: setor, produto, tier de ticket e match completo.
- Taxa por perspectiva: `T_x = Won_x / (Won_x + Lost_x)`.
- Força da amostra: `C_x = min(casos_x / 30, 1)`.
- Score: média das taxas ponderada pela força de cada histórico, em escala de 0 a 100.
- Ausência de histórico vira “indisponível”, nunca zero.

## O: Opportunity Value

Pergunta: qual é o impacto econômico potencial da oportunidade?

- Valor disponível antes do fechamento: preço de catálogo do produto.
- Score: `OV = 100 × valor_da_oportunidade / maior_valor_do_catálogo`.
- Tier automático: os preços distintos são ordenados e distribuídos por posição entre Bronze, Prata, Ouro e Diamante usando `1 + piso(4 × (posição − 1) / quantidade_de_preços)`.
- Os limites são relativos ao catálogo de cada empresa; não existem cortes universais em dólares.

No dataset, a faixa de US$ 55 a US$ 26.768 é real e foi validada contra o catálogo original. A distância entre os scores preserva essa diferença econômica.

## W: Warmth

Pergunta: há quanto tempo o negócio está em andamento e quão comum é um ciclo permanecer aberto por esse período?

- Base: os 6.711 ciclos encerrados.
- Score: `WS = 100 × ciclos_com_duração_maior_ou_igual_à_idade / total_de_ciclos`.
- Temperaturas: Quente, Morna, Fria e Estagnada são derivadas dos quartis empíricos dos ciclos; oportunidades em `Prospecting` ficam como “Sem contato”.
- Warmth mede frescor temporal, não intenção do comprador, pois o dataset não possui última atividade.

## E: Execution Fit

Pergunta: qual experiência histórica o vendedor possui com aquele perfil de negócio?

- Critérios atuais: mesmo produto, mesmo setor e mesmo tier de ticket.
- Fit por critério: `F_x = 100 × ganhos_do_vendedor_x / atuações_do_vendedor_x`.
- Score: média simples apenas dos critérios calculáveis.
- As quantidades de atuações e ganhos permanecem visíveis; baixa amostra não é apresentada como incompetência.

Company Fit não entra na v0.6: a cobertura de contas é parcial e as bandas firmográficas ainda não foram definidas e validadas.

## R: Recommendation

Pergunta: qual é a próxima melhor ação para este vendedor?

R é carregado automaticamente quando o vendedor abre a oportunidade. O modelo recebe somente o POWER Profile, suas evidências e o contexto disponível e devolve duas informações: uma ação de uma palavra e uma frase imperativa de até 24 palavras. O resultado é armazenado por `opportunity_id + input_hash + prompt_version`; se já existir uma versão válida, o sistema reutiliza o registro sem chamar o modelo novamente.

## Priorização no CRM

O pipeline preserva as quatro etapas como colunas simultâneas. Dentro de cada coluna, o POWER Priority ordena do maior PP para o menor: `PP = (12P + 3O + 4W + 6E) / 25`. Se P ou E estiver indisponível por falta de histórico, o PP também fica indisponível e aparece no fim da própria etapa, nunca convertido em zero. R não altera essa ordem.

## Cobertura da versão 0.6

| Componente | Oportunidades com resultado |
|---|---:|
| P: Propensity | 7.795 / 8.800 |
| O: Opportunity Value | 8.800 / 8.800 |
| W: Warmth | 8.800 / 8.800 |
| E: Execution Fit | 7.742 / 8.800 |
| R: Recommendation | Automático na primeira abertura e reutilizado por cache |

## Limites principais

- O dataset não possui atividades, stakeholders, origem do lead, motivo de perda ou histórico de mudança de estágio.
- Produto e tier de ticket são correlacionados nesta base; a redundância deve ser medida antes de uso em produção.
- P é um índice histórico explicável, não uma probabilidade calibrada.
- E mede experiência observada, não qualidade absoluta do vendedor.
- PP expressa prioridade relativa segundo a hierarquia de influência `P > E > W > O`, sem alterar a leitura POWER; sua capacidade de produzir lift deve ser validada fora da amostra.
- PP ordena oportunidades dentro da etapa atual; não foi treinado como classificador de `Won` versus `Lost`. Em etapas encerradas, sua leitura é de expansão ou reativação, não de previsão retrospectiva.
- R recomenda; a decisão permanece humana.
