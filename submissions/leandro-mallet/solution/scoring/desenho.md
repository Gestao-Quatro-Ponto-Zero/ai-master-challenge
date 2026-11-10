# Desenho do score (proposta para decisão)

Status: **proposta** — os pontos marcados com **[DECIDIR]** esperam a escolha do Leandro.
Data de referência ("hoje"): **2017-12-31**, último dia com registro no dataset.
Números medidos sobre `data/raw/` com as regras de limpeza de `data/clean.py`. O script de validação vai reproduzir todos eles.

---

## 1. O que os dados mostram

### 1.1 A chance de ganhar é praticamente a mesma em todo lugar

Win rate geral: **63,2%** (4.238 Won / 6.711 fechados).

| Variável | Menor win rate | Maior win rate | Diferença |
|---|---|---|---|
| Produto (7) | 60,0% (GTK 500, n=25) | 64,8% (MG Special) | 4,8 pts |
| Setor (10) | 61,2% (finance) | 64,8% (marketing) | 3,6 pts |
| Porte por receita (tercis) | 63,0% | 63,2% | 0,2 pt |
| Porte por funcionários (tercis) | 62,4% | 63,6% | 1,2 pt |
| Escritório regional (3) | 62,6% | 63,9% | 1,3 pt |
| Manager (6) | 62,1% | 64,4% | 2,3 pts |

- **Vendedor:** win rate vai de 55% a 70%, mas o desvio entre vendedores (3,7 pts) é quase igual ao que o acaso sozinho produziria (3,2 pts com ~220 deals por vendedor).
- **Conta:** desvio de 4,8 pts contra 5,4 pts esperados só pelo acaso, ou seja, nenhum sinal.
- **Teste no tempo** (usar só o histórico anterior a cada deal, como seria na vida real): o win rate passado da conta, do vendedor e do vendedor × produto **não prevê** o resultado seguinte. Os quintis ficam todos entre 60% e 65%, sem ordem.
- **Idade do deal:** fotografando o pipeline no fim de cada mês (abr–nov/2017), deals novos e antigos ganham na mesma proporção (61%–71%, sem padrão estável).

**Conclusão:** um score de "probabilidade de fechar" montado com produto × setor × porte × vendedor ordenaria ruído. É o que uma IA faz sozinha a partir do brief, e o dado não sustenta isso.

### 1.2 O que de fato varia

**a) Valor.** O preço de tabela vai de US$ 55 (MG Special) a US$ 26.768 (GTK 500), uma diferença de 487×. O valor fechado acompanha a tabela: mediana de 99,8% do preço, 50% dos deals entre 93% e 106%.

**b) Idade do deal (dias desde o engajamento) diz se ele ainda está vivo e quando vai se decidir.** Fotografias do pipeline no fim de cada mês de abr a nov/2017 (13 mil deals-fotografia):

| Idade na fotografia | Resolveu (Won ou Lost) nos 30 dias seguintes | Nunca fechou até 31/12/2017 |
|---|---|---|
| 0–14 dias | 29% | 29% |
| 15–30 | 12% | 31% |
| 31–45 | 20% | 39% |
| 46–60 | 35% | 31% |
| 61–75 | 38% | 44% |
| **76–90** | **48%** | 43% |
| 91–105 | 32% | 66% |
| 106–120 | 20% | 80% |
| 121–138 | 3% | 97% |
| > 138 | 0% | 100% |

- Os deals perdidos morrem cedo (mediana de 14 dias até o Lost). Os ganhos fecham entre 45 e 120 dias (mediana de 57).
- **O deal mais longo que já fechou levou 138 dias.** O dataset permitiria ver ciclos de até 437 dias, então esse limite não vem do corte de datas.
- No pipeline aberto de hoje, **1.291 dos 1.589 deals em Engaging (81%) passaram de 138 dias**, ou seja, já são mais velhos que qualquer deal que fechou na história. Somam US$ 3,2 mi dos US$ 5,0 mi em aberto (preço de tabela). Desses, 340 passaram de 276 dias (o dobro do recorde).
- Por vendedor, a fatia de deals abertos acima de 138 dias vai de 38% a 88% (mediana de 71%).

**c) Conta preenchida.** **Nenhum dos 6.711 deals fechados (Won ou Lost) está sem conta.** No pipeline aberto, 1.425 dos 2.089 (68%) estão sem conta: 337 em Prospecting e 1.088 em Engaging.

**d) Fim de trimestre (contexto para o manager, fora do score).** Deals encerrados em mar/jun/set/dez ganham 80,7%. Nos outros meses, 52,3%. O volume de fechamentos é parecido em todos os meses: o time registra os ganhos no fim do trimestre e as perdas no meio.

### 1.3 Todos os atributos das 4 tabelas: o que foi testado e onde aparece

Teste de chance: a diferença entre o maior e o menor win rate dos grupos com 30 ou mais deals fechados (6.711 deals). Nenhum atributo fica de fora: o que não entra no score aparece na tela como contexto, com o número, para o vendedor e o manager verem que foi olhado.

| Tabela | Atributo | Resultado | Veredito | Onde aparece |
|---|---|---|---|---|
| products | `product` / `sales_price` | Win 60,3%–64,8% (4,5 pts); preço de US$ 55 a US$ 26.768; valor fechado = 97%–100% da tabela (mediana por produto) | Chance: ruído. **Valor: entra no score** | Componente `valor` + motivo |
| products | `series` | 62,7%–63,4% (0,7 pt) | Ruído | Detalhe do deal |
| accounts | `sector` | 61,2%–64,8% (3,7 pts) | Ruído | Detalhe do deal: "chance histórica no setor X: 61%, perto da média de 63%" |
| accounts | `revenue` (tercis) | 63,0%–63,2% (0,2 pt) | Ruído | Detalhe do deal (porte) |
| accounts | `employees` (tercis) | 62,4%–63,6% (1,2 pt) | Ruído | Detalhe do deal (porte) |
| accounts | `year_established` (tercis de idade) | 62,6%–64,2% (1,6 pt) | Ruído | Detalhe do deal |
| accounts | `subsidiary_of` (tem empresa-mãe) | 63,1% × 63,6% (0,6 pt) | Ruído | Detalhe do deal (grupo da conta) |
| accounts | `office_location` | 56%–75% (19 pts), mas cada país fora dos EUA é **uma conta só**; EUA 63,3% (n=5.555) × resto 62,6% (n=1.156) | Ruído (é o mesmo da conta) | Detalhe do deal |
| accounts | histórico da conta | 53%–75% (22 pts), desvio 4,8 pts contra 5,4 pts do acaso; win rate passado não prevê o seguinte (quintis 60%–65%, sem ordem) | Ruído | Detalhe do deal: "esta conta: X ganhos em Y, média do time 63%" |
| sales_teams | `sales_agent` | 55%–70% (15 pts), desvio 3,7 pts contra 3,2 pts do acaso; win rate passado não prevê o seguinte | Ruído | Visão do manager: win rate por vendedor com a faixa do acaso desenhada |
| sales_teams | `manager` | 62,1%–64,4% (2,3 pts) | Ruído | Filtro + visão do manager |
| sales_teams | `regional_office` | 62,6%–63,9% (1,4 pt) | Ruído | Filtro + visão do manager |
| pipeline | `account` vazia | 0 de 6.711 fechados sem conta; 68% dos abertos sem | **D2** | Flag `sem_conta` |
| pipeline | `engage_date` (idade) | Não muda a chance; muda quando o deal se decide e se ainda está vivo (tabela da seção 1.2) | **Entra no score** | Componente `tempo` + flags |
| pipeline | `deal_stage` | Prospecting não tem data de engajamento: não há como medir idade | Sem sinal | Aviso "sem dado de idade" |
| pipeline | `close_date` | Fim de trimestre: 80,7% × 52,3% | Fora do score (não existe para deal aberto) | Visão do manager |
| pipeline | `close_value` | 99,8% do preço de tabela na mediana | Justifica usar o preço como valor | Motivo do componente `valor` |

---

## 2. Proposta de score (0–100)

Ideia central: **o score não finge prever quem ganha.** Ele organiza a semana do vendedor com três perguntas que os dados respondem:
1. **Quanto vale?**
2. **Está na hora de decidir ou já morreu?**
3. **O deal está qualificado?**

Soma de componentes visíveis, para o vendedor ver de onde vem cada ponto:

| Componente (chave no contrato) | Pontos | Regra | Por quê |
|---|---|---|---|
| `valor` | 0–45 | `45 × (ln preço − ln 55) / (ln 26.768 − ln 55)`, sobre o preço de tabela do produto | O valor fechado ≈ preço de tabela. A escala log impede que o GTK 500 esmague todo o resto: GTX Basic ≈ 17, MG Advanced ≈ 30, GTX Pro ≈ 32, GTK 500 = 45 |
| `tempo` | 0–35 | `35 × (taxa de resolução em 30 dias da faixa de idade) / (taxa da melhor faixa)`, curva calculada pelas fotografias do histórico. Acima de 120 dias = 0. Prospecting (sem data de engajamento) usa a faixa 0–14 | Põe no topo o que está na janela de decisão (46–90 dias) e zera o que a história diz que não fecha mais |
| `conta` | 0 ou 20 **[DECIDIR D2]** | Opção A: 20 se a conta está preenchida. Opção B: não pontua, vira tarefa (ver D2) | Nenhum deal fechado está sem conta, mas isso pode ser artefato do gerador dos dados |
| `chance` | 0 (só exibida) | Win rate histórico **[DECIDIR]** | Ver D1 |

Pontuação máxima: GTK 500, conta preenchida, 76–90 dias = 100.

### Flags
- `esfriando`: Engaging com 91–120 dias (dali em diante, 2 em cada 3 não fecham).
- `parado`: Engaging com mais de 120 dias (≥ 97% não fecharam).
- `sem_conta`: conta vazia.
- `sem_data`: Prospecting, sem data de engajamento.

### Ação
| Ação | Regra **[DECIDIR D4]** | Deals hoje (aprox.) |
|---|---|---|
| `desistir` | Engaging com mais de 276 dias (o dobro do deal mais longo que já fechou) | 340 |
| `requalificar` | `parado` até 276 dias; com D2 = A, também `sem_conta` | ~950 (D2 = B) a ~1.400 (D2 = A) |
| `focar` | O resto, ordenado pelo score; com D2 = B, o deal sem conta fica aqui com a tarefa de cadastro | ~250 (D2 = A) a ~800 (D2 = B) |

O app mostra o top 5 de `focar` por vendedor e a lista de requalificar/desistir. Na mediana, cada vendedor tem 23 deals vivos e 79 abertos no total.

### Motivos (`reasons`): 2 ou 3 frases montadas a partir dos componentes
- "Produto GTX Pro (US$ 4.821): um dos 3 mais valiosos do catálogo."
- "Está no dia 82: nesta fase, 48% dos deals se resolvem no próximo mês."
- "Parado há 165 dias: nenhum deal desta idade fechou até hoje."
- "Conta não preenchida: nenhum deal fechou sem conta. Identifique o cliente."

---

## 3. Como vamos validar (`scoring/validacao.md`)

Valor em log mais uma curva de idade é uma fórmula simples, e qualquer um que olhe os dados chega perto dela. O que tem de sustentar o score é a validação. Por isso ela compara a fila com regras simples que um vendedor usaria sem ferramenta, e **o resultado é publicado como sair, inclusive se o score perder**.

Backtest com fotografias no fim de cada mês, de abr a nov/2017. Em cada fotografia, o score usa **só** o que se sabia naquela data (curva de idade e preços), e o resultado é conferido depois.

**Filas comparadas** (mesmos deals, mesma fotografia):
- **Score** proposto.
- **Por valor**: preço de tabela, do maior para o menor.
- **Mais novo primeiro**: menor idade desde o engajamento.
- **Acaso**: ordem aleatória (média de 1.000 sorteios).

**Medidas**, para cada fila, sobre o top 20% e o top 5 por vendedor:
1. **Valor ganho capturado:** fatia do valor ganho nos 90 dias seguintes que estava no topo da fila.
2. **Deals que se decidem:** taxa de resolução (Won ou Lost) nos 30 dias seguintes.
3. **Deals mortos no topo:** fatia do topo que nunca fechou até 31/12/2017.
4. **Win rate** do topo, publicado como sai (esperado: igual em todas as filas, porque a chance é plana).

Intervalo de confiança por bootstrap sobre as 8 fotografias, para não chamar de vitória uma diferença que cabe no acaso.

**Checagens extras:**
- **Cada atributo da seção 1.3 contra o resultado real:** a mesma tabela regerada pelo script, com o teste no tempo (só o histórico anterior a cada deal) para conta, vendedor, vendedor × produto e região.
- **Correlação score × preço.** Se passar de ~0,9, o score virou "ordenar por produto caro" e os pesos precisam ser revistos.
- **Flags:** os deals marcados `parado`/`esfriando` de fato não fecharam?
- **Hoje:** quantos deals do top 5 "só por valor" de cada vendedor estão parados há mais de 120 dias. É o tempo que o vendedor perderia sem o score.
- **Prospecting (500 deals, sem data de engajamento):** não há sinal de idade para eles. A tela vai dizer isso em vez de dar uma nota de tempo inventada.

Saída: `data/scored/deals_scored.json` (contrato do PLANO-SESSOES, sem mudança de chaves) + `scoring/validacao.md` com as tabelas.

---

## 4. Decisões para o Leandro

- **D1 — Chance de ganhar.** Proposta: peso 0, exibida como contexto ("chance histórica: 63%, igual para todo tipo de deal"). Alternativa: peso pequeno (10 pts) com win rate por produto suavizado, sabendo que a diferença é ruído. **Nas duas opções**, todos os atributos das 4 tabelas continuam testados e visíveis (seção 1.3): cada um com o número, no detalhe do deal (setor, porte, idade e grupo da conta, histórico da conta, país) ou na visão do manager (vendedor com a faixa do acaso, região, manager, fim de trimestre). A validação (seção 3) publica o teste de cada atributo contra o resultado real. Tirar a chance do score não esconde dado: mostra que ele foi olhado e por que não muda a ordem.
- **D2 — Deal sem conta (68% do pipeline aberto).** O histórico de win rate da conta não tem sinal, então sai do score em qualquer caso. As duas opções:

  | | A. Pontos (conta preenchida = 20) | B. Tarefa, sem mexer na ordem |
  |---|---|---|
  | Como funciona | `conta` vale 0 ou 20 no score | `conta` não pontua; flag `sem_conta` e tarefa "identificar o cliente" ao lado do deal |
  | Efeito na fila | 1.425 dos 2.089 abertos perdem 20 pontos e caem na fila | A ordem vem só de valor e tempo; deal sem conta continua podendo ser foco |
  | Base | Nenhum dos 6.711 deals fechados está sem conta | Os dados não dizem por que só os abertos estão sem conta, e isso pode ser regra do gerador, não do processo de venda |
  | Risco | Punir a ordem por um campo que talvez seja só cadastro atrasado | Deixar no topo um deal que talvez não esteja qualificado |

  Nas duas opções a chave `conta` continua no contrato (na B, vale 0 para todos e o app mostra a tarefa), então o app não muda.
- **D3 — Pesos.** Proposta com D2 = A: valor 45, tempo 35, conta 20. Com D2 = B: valor 55, tempo 45.
- **D4 — Cortes de ação.** Proposta: `parado` acima de 120 dias → requalificar; acima de 276 dias → desistir.
