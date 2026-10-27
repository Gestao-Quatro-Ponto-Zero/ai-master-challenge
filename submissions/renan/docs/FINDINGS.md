# Achados (gerado por `npm run analyze`)

> Arquivo gerado automaticamente. Não editar à mão.

Base: 6.711 deals fechados · taxa de vitória 63,2% · data de referência 2017-12-31.

## 1. Quanto cada fator realmente separa ganhos de perdas

| Fator | Grupos | Taxa bruta (mín–máx) | Após descontar o ruído |
|---|---|---|---|
| Vendedor | 30 | 55,0% – 70,4% | 62,1% – 63,9% |
| Produto | 7 | 60,0% – 64,8% | 63,2% – 63,2% |
| Setor | 10 | 61,2% – 64,8% | 63,2% – 63,2% |
| Porte da conta | 3 | 62,5% – 64,2% | 63,2% – 63,2% |

Escritório: 62,6% – 63,9%. Manager: 62,1% – 64,4%.

### O vendedor é sinal ou ruído?

- Qui-quadrado das taxas por vendedor: 33,3 com 29 graus de liberdade (o esperado se todos tivessem a mesma taxa real é ≈ 29).
- Correlação da taxa do vendedor entre 1º e 2º semestre: 0,32 (29 vendedores com 30+ deals em cada semestre).
- Mesma correlação para vendedor × produto: -0,08 (70 pares com 15+ deals em cada semestre).

Valor fechado ÷ preço de tabela nos ganhos: p10 0.87 · mediana 1.00 · p90 1.12.

## 2. Tempo no pipeline

Ciclo dos perdidos: mediana de 14 dias. Ciclo dos ganhos: mediana de 57 e p75 de 88 dias. Maior ciclo já observado: 138 dias.

| Deal ainda aberto após | Chance de ganhar |
|---|---|
| 0 dias | 63,2% |
| 7 dias | 65,7% |
| 14 dias | 68,7% |
| 30 dias | 68,2% |
| 60 dias | 68,6% |
| 90 dias | 71,1% |
| 120 dias | 75,6% |

## 3. Fim de trimestre

Deals fechados no último mês do trimestre: 80,7% de vitória (2574 deals). Nos demais meses: 52,3% (4137 deals).

## 4. Pipeline aberto em 2017-12-31

| Momento | Deals | Valor de tabela |
|---|---|---|
| Prospecção | 500 | US$ 1.073.986 |
| Início | 7 | US$ 16.385 |
| Em andamento | 101 | US$ 205.234 |
| Reta final | 190 | US$ 471.946 |
| Parado | 1291 | US$ 3.198.664 |

81% dos deals em Engaging estão abertos há mais tempo que qualquer deal já fechado. Eles somam 64% do valor de tabela do pipeline aberto (US$ 4.966.215).

Se o vendedor apenas ordenasse o pipeline por preço, 47% do top 20% seriam deals parados.

## 5. Backtest

### Corte em 2017-06-30

Aprendeu com 2679 deals fechados até o corte; avaliou 970 deals abertos no corte (vitória real: 62,8%).

| Estratégia | AUC da chance | Receita no top 20% | % da receita total |
|---|---|---|---|
| Score (valor esperado) | 0.505 | US$ 730.338 | 50,7% |
| Ordenar por preço do produto | — | US$ 727.955 | 50,5% |
| Só tempo no pipeline | 0.504 | US$ 290.889 | 20,2% |
| Taxa bruta do vendedor | 0.508 | US$ 257.329 | 17,9% |
| Ordem aleatória | 0.491 | US$ 266.869 | 18,5% |

Nenhum deal estaria parado nesse corte.

### Corte em 2017-08-31

Aprendeu com 4091 deals fechados até o corte; avaliou 893 deals abertos no corte (vitória real: 71,3%).

| Estratégia | AUC da chance | Receita no top 20% | % da receita total |
|---|---|---|---|
| Score (valor esperado) | 0.557 | US$ 735.659 | 50,7% |
| Ordenar por preço do produto | — | US$ 724.381 | 50,0% |
| Só tempo no pipeline | 0.557 | US$ 299.507 | 20,7% |
| Taxa bruta do vendedor | 0.531 | US$ 290.595 | 20,0% |
| Ordem aleatória | 0.497 | US$ 276.063 | 19,0% |

Nenhum deal estaria parado nesse corte.

### Corte em 2017-09-30

Aprendeu com 4726 deals fechados até o corte; avaliou 935 deals abertos no corte (vitória real: 59,8%).

| Estratégia | AUC da chance | Receita no top 20% | % da receita total |
|---|---|---|---|
| Score (valor esperado) | 0.500 | US$ 587.484 | 46,9% |
| Ordenar por preço do produto | — | US$ 575.229 | 45,9% |
| Só tempo no pipeline | 0.500 | US$ 211.361 | 16,9% |
| Taxa bruta do vendedor | 0.493 | US$ 264.658 | 21,1% |
| Ordem aleatória | 0.484 | US$ 247.717 | 19,8% |

Nenhum deal estaria parado nesse corte.
