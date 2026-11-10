# O que os dados sustentam (e o que não sustentam)

> Reproduzir: `python solution/data/clean.py` e depois `python solution/analysis/signal.py`.
> Todos os números abaixo saem de `analysis/signal_summary.json` e de `analysis/tables/`.
> Intervalos = 95% (Wilson). Testes = qui-quadrado de independência (conferido por permutação, 2.000 sorteios). Foram 18 variáveis testadas; corrigindo por Bonferroni, só passa p < 0,0028. "Poucos casos" = menos de 30 deals fechados no grupo.

## Resumo em 6 linhas

1. **Taxa de ganho geral: 63,2%** (4.238 Won em 6.711 fechados; IC 62,0–64,3%).
2. **Nenhum atributo do deal separa Won de Lost**: produto, setor, porte, país, região, manager, vendedor, conta e vendedor × produto ficam todos dentro do ruído.
3. **O histórico não prevê o futuro**: a taxa passada da conta ou do vendedor não muda a chance do próximo deal (teste fora do tempo).
4. **Só o tempo tem sinal**: deal que passa das 2 primeiras semanas ganha 67%; o que fecha antes ganha 54% (+13 pp, p ≈ 10⁻¹⁶). Depois de 15 dias, a taxa fica plana.
5. **O pipeline aberto está quase todo parado**: 81% dos deals em Engaging (1.291 de 1.589) estão abertos há mais tempo que qualquer deal já fechado (138 dias). E 68% dos abertos não têm conta.
6. **Os dados parecem sintéticos** (detalhes no fim). Isso muda o que dá para prometer no score.

## Período e data de referência

- `engage_date`: 2016-10-20 a 2017-12-27. `close_date`: **2017-03-01** a 2017-12-31.
- Não existe fechamento antes de março/2017. Deals engajados no fim de 2016 só aparecem se fecharam depois de março, e por isso parecem melhores (engajados em 2016T4 ganham 82%; fechados em 2017T1, que só tem março, ganham 82%). **É efeito do corte, não sinal**: 2017T2, T3 e T4 ficam em 61,7%, 61,4% e 60,3%.
- **"Hoje" = 2017-12-31**, o último dia com qualquer registro. Alternativas descartadas:
  - data real (2026): todo deal teria 8+ anos, e a idade perderia o sentido;
  - 2017-12-27 (último engajamento): diferença de 4 dias, sem efeito prático.
- Ressalva: 31/12/2017 é o último dia de um trimestre. Os abertos acabaram de passar pelo fechamento do 4º tri sem fechar (ver "Fim de trimestre").
- Para validar o score no histórico (backtest), dá para simular um "hoje" anterior (ex.: 2017-09-30) e ver o que aconteceu depois.

## O que NÃO tem sinal

| Variável | Faixa da taxa de ganho (grupos com 30+ deals) | p-valor | Leitura |
|---|---|---|---|
| Produto (7) | 60,3% (MG Advanced) a 64,8% (MG Special) | 0,37 | Nenhum IC exclui a média. GTK 500 tem só 25 fechados (60%, IC 41–77%) |
| Série (3) | 62,7% a 63,4% | 0,82 | — |
| Faixa de preço | 62,1% a 64,2% | 0,50 | Deal caro não perde mais |
| Setor (10) | 61,2% a 64,9% | 0,97 | — |
| Receita da conta (tercis) | 63,0% a 63,2% | 0,99 | Porte não importa |
| Funcionários (tercis) | 62,4% a 63,6% | 0,67 | — |
| Sede EUA × fora | 62,6% × 63,3% | 0,69 | — |
| Subsidiária × independente | 63,1% × 63,6% | 0,71 | — |
| Idade da empresa | 62,3% a 64,3% | 0,33 | — |
| Conta (85) | 53,1% a 75,0% | 0,94 | Só 2 de 85 com IC fora da média; o acaso daria ~4 |
| Vendedor (30) | 55,0% (Lajuana Vencill) a 70,4% (Hayden Neloms) | 0,26 | 2 de 30 com IC fora da média (o acaso daria ~1,5). A dispersão entre vendedores (3,7 pp) é a esperada se todos tivessem a mesma taxa (3,4 pp; p95 = 4,3 pp) |
| Manager (6) | 62,1% a 64,4% | 0,79 | — |
| Escritório regional (3) | 62,6% a 63,9% | 0,60 | — |
| Vendedor × produto (178 combinações) | 46,7% a 81,3% | 0,22 | 89 combinações têm menos de 30 casos. Das 89 com 30+, 6 têm IC fora da média; o acaso daria ~4,5 |
| Vendedor × setor (288) | 43,9% a 80,0% | 0,44 | 213 combinações com poucos casos |
| Dia da semana do engajamento | 60,7% a 66,0% | 0,24 | — |

**Teste fora do tempo** (`tables/out_of_time_*`): ordenei os deals pela data de fechamento e, para cada um, calculei a taxa de ganho **anterior** da conta (mínimo 10 deals) e do vendedor (mínimo 30).

| Quartil do histórico | Conta → próximo deal | Vendedor → próximo deal |
|---|---|---|
| Q1 (pior) | 63,6% | 62,0% |
| Q2 | 60,7% | 63,2% |
| Q3 | 62,3% | 62,2% |
| Q4 (melhor) | 60,1% | 60,3% |
| p-valor | 0,21 | 0,44 |

O melhor histórico não ganha mais; ganha até um pouco menos. "Vendedor bom" e "conta boa" não se sustentam como preditores.

**Implicação para o score:** um componente de "chance" baseado em produto × setor × porte, ajustado pelo vendedor (o plano original), não tem base nestes dados. Com suavização bem feita, todas as estimativas voltam para ~63%. Sem suavização, o score passaria ruído como se fosse informação, e o vendedor veria motivos falsos ("este setor fecha mais").

## O que TEM sinal

### 1. As duas primeiras semanas

Na coorte sem viés de corte (engajados de 2017-03-01 a 2017-08-15, 3.718 fechados):

| Tempo até fechar | Deals | Taxa de ganho | IC 95% |
|---|---|---|---|
| 0–14 dias | 1.737 | **54,2%** | 51,8–56,5% |
| 15 dias ou mais | 1.981 | **67,2%** | 65,1–69,3% |

p ≈ 3,5 × 10⁻¹⁶ (V de Cramér 0,13). A perda costuma ser rápida: metade dos Lost fecha em até 14 dias (mediana 14 contra 57 dos Won, na base toda).

Depois dos 15 dias, a taxa não sobe mais: 67,2% (≥15), 66,6% (≥30), 67,0% (≥60), 68,1% (≥90), 67,1% (≥120, n = 85). Na base inteira parece subir até 75% acima de 120 dias, mas isso vem do corte de 2016 e do fim de trimestre. **Não usar "mais velho = melhor".**

### 2. Fim de trimestre

| Mês do fechamento | Deals | Taxa de ganho |
|---|---|---|
| Mar, jun, set, dez | 2.574 | **80,7%** |
| Demais meses | 4.137 | **52,3%** |

p ≈ 10⁻¹²¹. 49% dos Won fecham em mês de fim de trimestre, contra 20% dos Lost. Quem fecha no fim do trimestre leva ~75 dias (mediana); quem fecha no meio leva ~11, e isso vale igual para Won e Lost.

O ciclo longo, portanto, é quase todo "esperou o fim do trimestre". Para deals abertos isso não vira chance individual (não há data prevista de fechamento). Serve como **contexto de calendário**: o próximo fim de trimestre é 31/03/2018.

### 3. Valor

- O valor de um Won fica perto do preço de tabela: `close_value / list_price` tem média 0,997, desvio 0,099, p5 = 0,83 e p95 = 1,16. Só 1,5% fecha exatamente no preço de tabela. **Preço de tabela é uma boa estimativa do valor do deal aberto (±10%).**
- Os preços vão de 55 (MG Special) a 26.768 (GTK 500), quase 500×. A receita ganha se concentra em GTX Pro (35%), GTX Plus Pro (26%) e MG Advanced (22%).
- Com a chance plana, "valor × chance" vira só "ordenar por valor", que o brief proíbe. A diferença tem que vir do tempo, do estado do deal e da qualidade do dado, e o valor precisa ser mostrado em faixas, não como o fator dominante.

## Pipeline aberto (o que o vendedor vai ver)

- **2.089 abertos**: 500 Prospecting (sem `engage_date`, sem idade calculável) e 1.589 Engaging.
- **Sem conta: 1.425 (68%)**, sendo 1.088 Engaging e 337 Prospecting. Nenhum deal fechado está sem conta, então não dá para medir se a falta de conta muda a chance. É um problema de cadastro, e a ação é "identificar a conta".
- **Idade dos Engaging** em 31/12/2017: mediana 165 dias (p25 148, p75 263, máximo 423).

| Idade | Deals |
|---|---|
| 0–30 dias | 18 |
| 31–60 | 39 |
| 61–90 | 53 |
| 91–120 | 103 |
| 121–180 | 646 |
| 181–365 | 677 |
| mais de 365 | 53 |

- **1.291 Engaging (81%) estão abertos há mais de 138 dias**, o maior ciclo já visto num deal fechado, e 1.432 passaram do p90 dos Won (106 dias). Só 110 foram engajados nos últimos 90 dias. Pelo histórico, esses deals já deveriam ter fechado: ou foram esquecidos sem marcar Lost, ou o dado não representa um pipeline real. **É o achado mais útil para a "segunda-feira de manhã"**: a maior parte do pipeline precisa ser requalificada ou encerrada.
- Os abertos por vendedor vão de 31 a 194 (Darcel Schlecht tem 194). Por produto: GTX Basic 430, MG Special 428, GTX Pro 333, GTX Plus Basic 332, MG Advanced 328, GTX Plus Pro 223, GTK 500 15.
- Há um pico de engajamentos ainda abertos em julho/2017 (402, contra 100–250 nos meses vizinhos).

## Sinais de que os dados são sintéticos

- **Fim de semana**: 28,6% dos engajamentos e 28,4% dos fechamentos caem em sábado ou domingo, exatamente 2/7. Cada dia da semana fica entre 13,8% e 14,8%. Em vendas B2B reais, o fim de semana é quase vazio.
- **Vendedores iguais**: a variação da taxa entre vendedores é do tamanho que o acaso produziria se todos fossem idênticos.
- **Nenhum atributo importa**: produto, porte, setor e região sem efeito algum é raro num CRM real.
- **Valor com ruído simétrico** em torno do preço de tabela (sem desconto típico, sem arredondamento).
- **Abertos impossíveis**: nenhum deal fechado passou de 138 dias, mas 81% dos abertos passaram.
- **Ritmo de trimestre muito regular**: em todo mês de fim de trimestre há ~500–530 Won e ~110–140 Lost; nos outros meses, ~280–450 de cada.

A conclusão prática é que o resultado (Won/Lost) parece ter sido sorteado com a mesma probabilidade para todos, com uma regra de calendário por cima. Um score que "descobre" efeitos de setor ou vendedor aqui estaria vendendo ruído.

## Pontos de decisão para o Leandro

1. **Chance por segmento** (produto × setor × porte × vendedor): os dados não sustentam. Opções: (a) tirar do score e mostrar a taxa histórica só como contexto, rotulada "não muda a chance"; (b) manter com suavização forte, sabendo que vira ~63% para todo mundo.
2. **Tempo**: usar as duas faixas sustentadas ("ainda nas 2 primeiras semanas" = risco maior; "passou de 138 dias" = fora do padrão histórico → requalificar ou desistir). Não premiar a idade em si.
3. **Valor**: preço de tabela como valor esperado, mostrado em faixas, para o ranking não virar "ordenar por valor".
4. **Sem conta (68%)**: tratar como tarefa de cadastro (flag e ação), não como penalidade de chance, porque não há como medir o efeito.
5. **Fim de trimestre**: usar como contexto de calendário ("faltam X dias para o fechamento do trimestre"), não como chance por deal.
6. **Transparência**: dizer na documentação que os dados parecem sintéticos e que o score foi desenhado para não inventar sinal.

## Arquivos

- `signal.py`: análise completa (só pandas e numpy).
- `signal_summary.json`: todos os números deste documento.
- `tables/`: taxa de ganho por variável com IC e marcação de poucos casos (`win_rate_by_*.csv`), ciclo por produto e resultado, idade dos abertos, testes fora do tempo, coorte sem viés, fechamentos por mês.
