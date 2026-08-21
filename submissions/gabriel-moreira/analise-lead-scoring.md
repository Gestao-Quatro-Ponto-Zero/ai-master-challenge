# Modelo de Lead Scoring — análise de 8.800 negócios e formato recomendado

> Base: `sales_pipeline` (8.800 oportunidades, out/2016–dez/2017), 85 contas, 7 produtos, 35 vendedores.
> 6.711 negócios fechados (4.238 ganhos / 2.473 perdidos) + 2.089 em aberto.

> **Nota de atualização (2026-08-19):** este documento é a análise exploratória original — a conclusão central (nenhum atributo firmográfico prevê ganho/perda; valor é o sinal real) segue válida e é a base de tudo que veio depois. A **fórmula final implementada** é mais refinada do que o `P(ganho) = 0,632` constante e o corte de 90 dias descritos aqui: usa encolhimento hierárquico para `p̂` (variando 0,60–0,75 por produto), curvas de aging isotônicas e um limite de censura de **138 dias** (não 90), derivado do ciclo máximo real dos negócios fechados. Ver [`docs/architecture.md`](docs/architecture.md) e [`docs/decisions-log.md`](docs/decisions-log.md) para a versão vigente — os números de valor, qualidade de dados e as recomendações de instrumentação abaixo continuam de pé.
>
> **Nota de atualização (2026-08-20):** CONFIANÇA e ESTADO foram redesenhados no mesmo dia da remoção do RBAC — CONFIANÇA deixou de ser uma escala A-D dominada por idade e passou a ser `min(completude, suporte)`, 0-100; ESTADO deixou de ser uma tabela 4×2 e passou a ser uma árvore de decisão de 4 valores (Priorizar/Acompanhar/Qualificar/Revisão em lote). PRIORIDADE em dólares deixou de ser exibida (SCORE é o número de prioridade). Três hipóteses de refinamento do motor foram testadas nesse redesenho e as três pioraram a previsão fora da amostra — ver §4.5 abaixo.
>
> **Origem dos números de p̂ e URGÊNCIA (implementação 2026-08-19):**
> - **Taxa base (0,632):** taxa global de vitória em 6.711 negócios fechados (§2.2), estável em qualquer recorte (0,61–0,65 por setor, p > 0,26 em testes de permutação).
> - **p_ganho(t):** regressão isotônica sobre negócios ganhos/perdidos agrupados por idade no desfecho. Encontrou-se que probabilidade de ganho sobe levemente com tempo em funil (não decai): 0,632 aos 0 dias → 0,751 aos 120 dias. Limita-se a 120 dias por N amostral; acima de 138 dias, censura para o prior.
> - **risco(t):** P(resolve em 30 dias | ainda aberto com idade t), também isotônica. Calibrada diretamente do ciclo de negócios ganhos: mediana 57 dias (metade resolveu), P95 116 dias. A janela fecha enquanto `p_ganho` cresce — por isso URGÊNCIA usa `risco`, não um decaimento.
> - **Censura em 138 dias:** nenhum dos 6.711 negócios fechados levou mais de 138 dias. Acima, revertemos ao prior; extrapolação premiaria abandono.

---

## 1. Resumo executivo

A análise chegou a um resultado que muda a forma de montar o score:

**Nenhum atributo da conta prevê se o negócio será ganho ou perdido.** Setor, porte, receita, país, produto, região, gerente e vendedor — todos foram testados e nenhum é estatisticamente significativo. Um modelo preditivo treinado com todos eles em conjunto atinge **AUC = 0,50**, ou seja, desempenho idêntico a jogar uma moeda. A taxa de conversão é de ~63% praticamente em qualquer recorte que se faça.

**Mas o valor do negócio é quase perfeitamente previsível** (R² = 0,98). E a diferença de valor entre um negócio bom e um ruim é de até **400x**.

A conclusão prática: um lead score construído no formato tradicional "probabilidade de conversão" seria puro ruído com estes dados. O score precisa ser de **valor esperado** — priorizar pelo tamanho do prêmio, não pela chance de ganhar, porque a chance é a mesma para todo mundo e o prêmio não é.

O achado mais caro escondido nos dados: **39,6% da capacidade do time é gasta em produtos que geram 5,4% da receita.**

---

## 2. O que os dados dizem

### 2.1 Qualidade dos dados (corrigir na origem)

| Problema | Onde | Impacto | |
|---|---|---|--|
| `technolgy` (typo) vs `technology` | `accounts.sector` | 12 contas em setor fantasma | Corrigido manualmente para evitar custo de tokens |
| `GTXPro` vs `GTX Pro` | `sales_pipeline.product` | 1.147 negócios não casavam com `products.csv` | Corrigido manualmente para evitar custo de tokens |
| 1.425 negócios sem `account` | `sales_pipeline` | 100% deles em Prospecting/Engaging | |
| 70 de 85 contas sem `subsidiary_of` | `accounts` | campo inutilizável | |
| Distribuição de ciclo bimodal (picos em 0–14d e 60–90d, vale em 15–30d) | `engage_date`/`close_date` | sugere preenchimento em lote, não comportamento real — **não use ciclo como preditor até validar** | |

Os dois primeiros itens foram corrigidos na análise. Os demais são dívida a pagar no CRM.

### 2.2 O que NÃO prevê ganho/perda

Teste qui-quadrado para variáveis categóricas, Mann-Whitney para numéricas, sobre os 6.711 negócios fechados:

| Variável | p-valor | Veredito |
|---|---|---|
| Setor | 0,971 | não significativo |
| Produto | 0,372 | não significativo |
| Região do escritório | 0,604 | não significativo |
| Gerente | 0,786 | não significativo |
| Vendedor | 0,264 | não significativo |
| País da conta | 0,419 | não significativo |
| Nº de funcionários | 0,778 | não significativo |
| Receita da conta | 0,629 | não significativo |
| Ano de fundação | 0,368 | não significativo |
| Preço do produto | 0,412 | não significativo |

Os intervalos de confiança de 95% da taxa de ganho por setor se sobrepõem inteiramente:

```
marketing            0,648   IC95 [0,611 – 0,686]
software             0,639   IC95 [0,604 – 0,675]
technology           0,634   IC95 [0,605 – 0,663]
retail               0,631   IC95 [0,604 – 0,657]
medical              0,623   IC95 [0,592 – 0,654]
finance              0,612   IC95 [0,573 – 0,650]
                     ─────
GLOBAL               0,632
```

A distância entre o "melhor" e o "pior" setor é de 3,6 pontos percentuais — dentro do ruído amostral. Dar +25 pontos para "financial services" e +10 para "retail", como recomendam os guias genéricos de scoring, seria codificar ruído como se fosse sinal.

**Modelos preditivos treinados nesses dados:**

| Modelo | Features | AUC |
|---|---|---|
| Regressão logística | firmografia + produto + região | 0,493 |
| Gradient boosting | firmografia + produto + região | 0,489 |
| Regressão logística | + vendedor + gerente | 0,508 |
| Gradient boosting | + histórico da conta, **holdout temporal** (treino ≤ set/17, teste Q4/17) | 0,506 |

A referência de mercado: <cite index="7-1">AUC de 0,5 equivale a chute aleatório, 0,7–0,8 é considerado bom e 0,8–0,9 forte</cite>, e <cite index="8-1">modelos em produção normalmente ficam entre 0,75 e 0,90</cite>. Estamos em 0,50.

Testei ainda se o histórico da própria conta prediz o próximo negócio (sem vazamento temporal: só negócios fechados antes da data de engajamento). Correlação entre a taxa de ganho histórica da conta e o desfecho atual: **−0,026**. Contas com histórico de 73%+ de vitória convertem a 58,7% na sequência; contas com histórico ruim convertem a 64,7%. É reversão à média pura.

**Variação entre vendedores também é ruído:** o desvio-padrão observado das taxas de ganho individuais é 0,0366, contra 0,0339 esperado só por acaso dado o volume de cada um. Hayden Neloms (70,4%) e Lajuana Vencill (55,0%) não são vendedores diferentes — são a mesma moeda jogada 152 e 231 vezes.

### 2.3 O que VARIA de verdade: o valor

O contraste é brutal. O mesmo teste out-of-time que falhou em prever ganho/perda prevê o valor do negócio com **R² = 0,98** e erro médio de US$ 195 (contra US$ 2.038 do baseline). E o driver é essencialmente um só: **qual produto está na mesa**.

| Produto | Preço | % dos negócios | % do esforço¹ | Win rate | % da receita | **EV por negócio** | Receita/dia de esforço |
|---|---:|---:|---:|---:|---:|---:|---:|
| GTK 500 | 26.768 | 0,4% | 0,4% | 0,60 | 4,0% | **16.061** | 298,30 |
| GTX Plus Pro | 5.482 | 11,1% | 10,7% | 0,64 | 26,3% | **3.525** | 76,61 |
| GTX Pro | 4.821 | 17,1% | 16,3% | 0,64 | 35,1% | **3.064** | 66,92 |
| MG Advanced | 3.393 | 16,2% | 15,9% | 0,60 | 22,2% | **2.047** | 43,39 |
| GTX Plus Basic | 1.096 | 15,7% | 16,1% | 0,62 | 7,1% | **681** | 13,58 |
| GTX Basic | 550 | 21,4% | 22,3% | 0,64 | 5,0% | **350** | 6,97 |
| MG Special | 55 | 18,2% | 18,4% | 0,65 | 0,4% | **36** | 0,74 |

¹ esforço = nº de negócios × ciclo médio do produto

**A leitura desta tabela é o coração da recomendação:**

- **MG Special + GTX Basic = 39,6% dos negócios e 40,6% do esforço do time, para 5,4% da receita.**
- GTX Pro + GTX Plus Pro + MG Advanced + GTK 500 = 44,7% dos negócios, 43,2% do esforço, **87,5% da receita**.
- Um dia de esforço em GTK 500 rende **400x** mais que um dia em MG Special.
- MG Special tem a **maior** taxa de conversão da carteira (65%). É exatamente o tipo de armadilha que um score baseado em probabilidade de conversão premiaria.

Não há desconto relevante para modelar: a razão entre valor fechado e preço de tabela é 0,99–1,00 em todos os produtos, com desvio de ~10% que é ruído simétrico.

### 2.4 Porte: o único firmográfico que vale ponto

**IMPORTANTE:** porte NÃO muda win rate nem margem em deals individuais (close_value/list_price = 1.00 ± 0.01 em todos os portes). Muda o **volume** — quantas vezes a conta compra e o ticket agregado. Logo, porte é sinal de potencial de CONTA, não de deal.

Testei se setor e porte explicam o **potencial de receita da conta** (receita total gerada por conta no período):

| Variável | Teste | Resultado |
|---|---|---|
| Setor | ANOVA | F = 0,64, **p = 0,764** → sem efeito |
| Porte (funcionários) | ANOVA | F = 15,19, **p < 0,0001** → efeito forte |
| Funcionários × receita da conta | Spearman | **ρ = 0,670** (p < 0,00001) |
| Funcionários × nº de negócios | Spearman | **ρ = 0,520** (p < 0,00001) |

O porte não muda a chance de ganhar — muda **quantas vezes a conta compra** e **o quanto compra por vez**:

| Porte | Contas | Negócios/conta | Ticket médio | % produtos premium | **Receita/conta** |
|---|---:|---:|---:|---:|---:|
| SMB (<1k func.) | 18 | 62,6 | 1.416 | 42% | 88.560 |
| Mid (1–3k) | 27 | 72,9 | 1.354 | 42% | 98.691 |
| Upper (3–8k) | 24 | 80,8 | 1.594 | 46% | 128.699 |
| Enterprise (8k+) | 16 | 104,9 | 1.583 | 48% | **166.126** |

Uma conta Enterprise vale **1,9x** uma conta SMB — não porque converte melhor (não converte), mas porque compra 68% mais vezes e com ticket 12% maior. Já a diferença entre setores (US$ 106k a US$ 154k por conta) tem intervalos de confiança que se sobrepõem completamente e vem de amostras de 4 a 17 contas. **Setor deve receber peso zero no score.**

Receita da conta e nº de funcionários são colineares (r = 0,95) — use apenas um. Recomendo funcionários, que costuma ser mais confiável e mais fácil de enriquecer.

### 2.5 O funil aberto está congelado

2.089 negócios abertos, US$ 3,14M de valor esperado. Mas:

- Mediana de idade dos negócios em "Engaging": **165 dias**
- Mediana do ciclo dos negócios **ganhos**: **57 dias**
- **1.537 de 1.589** negócios em Engaging já passaram da mediana do ciclo de vitória
- **1.479 negócios estão parados há mais de 90 dias**, prendendo **US$ 2,32M** de valor esperado

Isso é 74% do valor do funil em negócios que estatisticamente já deveriam ter fechado. É o problema mais urgente da operação, e é o único sinal temporal acionável hoje — vale mais que qualquer refinamento do score.

---

## 3. Métodos pesquisados e qual se aplica aqui

### 3.1 Scoring bidimensional: Fit × Intent (padrão de mercado)

É o consenso atual. <cite index="3-1">A recomendação é separar as duas dimensões: nota de perfil (quem é o lead — porte, cargo, setor) e nota de intenção (o que ele fez — páginas visitadas, e-mails abertos, downloads). Um lead pode ter alto perfil e baixo engajamento (precisa de nutrição) ou alto engajamento e baixo perfil (não vale a pena)</cite>. <cite index="5-1">Manter as notas separadas permite ao time entender por que um contato apareceu, não apenas que apareceu</cite>, e <cite index="6-1">é comum exigir mínimos separados nas duas dimensões — por exemplo, fit ≥ 30 E comportamento ≥ 40 para virar MQL</cite>.

**Aplicabilidade aqui: parcial.** A estrutura é correta e vou usá-la, mas com uma correção grande — a dimensão "fit" precisa ser reinterpretada. Nos dados, perfil não prevê conversão; prevê valor. E a dimensão "intent" **não existe na base**: não há um único campo comportamental nos cinco CSVs.

### 3.2 Scoring preditivo (ML)

<cite index="8-1">Regressão logística continua sendo a base de muitas implementações por oferecer probabilidades interpretáveis, enquanto árvores com gradient boosting se tornaram o algoritmo dominante em sistemas de produção</cite>.

**Aplicabilidade aqui: nenhuma, hoje.** Já foi testado nas duas famílias, com e sem holdout temporal: AUC 0,49–0,51. Não é problema de algoritmo, é ausência de sinal nas features disponíveis. Rodar um modelo mais sofisticado sobre os mesmos campos vai produzir o mesmo 0,50 com mais custo e menos transparência.

### 3.3 Valor esperado / pipeline ponderado

<cite index="32-1">O pipeline ponderado multiplica o valor do negócio pela probabilidade de fechamento e soma tudo, produzindo uma estimativa realista de receita. A principal correção recomendada é parar de chutar as probabilidades e calibrá-las com pelo menos dois trimestres de dados reais de negócios fechados</cite>. A mesma lógica aparece em patentes de priorização de clientes: <cite index="31-1">um modelo de propensão estima a probabilidade de compra, um segundo modelo estima o tamanho da compra no período, e o valor esperado do cliente resulta da combinação dos dois</cite>.

**Aplicabilidade aqui: alta — é a espinha dorsal do modelo recomendado.** Temos 15 meses de dados fechados para calibrar a probabilidade (0,632, e ela é notavelmente estável), e o componente de valor é previsível com R² = 0,98. Quando a propensão é constante e o valor varia 400x, o valor esperado colapsa em "priorize por valor" — que é exatamente a resposta certa para esta operação.

### 3.4 Triagem por capacidade

<cite index="25-1">Um framework de triagem ordena as oportunidades abertas por valor esperado, aderência estratégica e probabilidade de fechamento, e as separa em três faixas: foco total, cadência estruturada, e desprioritização</cite>.

**Aplicabilidade aqui: alta.** Com 2.089 negócios abertos e 35 vendedores (≈60 negócios por pessoa), capacidade é a restrição real. É por isso que o modelo abaixo divide o EV pelo esforço estimado, e não olha só o EV bruto.

### 3.5 Velocidade de resposta

O estudo clássico de <cite index="23-1">Oldroyd, McElheran e Elkington na Harvard Business Review (2011), com 2.241 empresas americanas, encontrou que 37% respondiam em até 1 hora, 24% levavam mais de 24 horas e 23% nunca respondiam; a média entre os que responderam foi de 42 horas. Empresas que contatavam dentro de 1 hora tinham quase 7x mais chance de qualificar o lead, e mais de 60x em comparação com quem esperava 24 horas ou mais</cite>. Vale a ressalva metodológica: <cite index="23-1">os multiplicadores de 21x e 100x que costumam ser atribuídos à HBR vêm na verdade do estudo do MIT/InsideSales de 2007</cite>.

**Aplicabilidade aqui: indireta, mas relevante.** Não há timestamp de primeiro contato na base para medir isso. Mas com 74% do valor do funil parado há mais de 90 dias, o princípio se aplica em escala maior: **decaimento temporal precisa ser um multiplicador no score**, não um relatório à parte.

### 3.6 Loop de calibração

<cite index="1-1">A recomendação é estabelecer um ciclo quantitativo de retroalimentação: usar os dados de ganhos e perdas para validar o modelo continuamente — se os leads de alta pontuação não estão fechando, o modelo precisa ser ajustado</cite>. E <cite index="2-1">incluir pontuação negativa para sinais ruins, como setores fora do perfil e inatividade</cite>.

**Aplicabilidade aqui: crítica.** É justamente esse loop que revelou que os firmográficos não funcionam. Sem ele, o score vira folclore.

---

## 4. O formato recomendado

### 4.1 A fórmula

```
LEAD SCORE = P(ganho) × Valor_esperado × Decaimento_temporal × Intenção
```

Três componentes para deals com produto definido:

| Componente | Valor hoje | De onde vem | Status |
|---|---|---|---|
| **P(ganho)** | 0,632 constante | taxa base de 6.711 negócios fechados | ✅ calibrado — **não segmentar**, nenhum atributo desloca isso |
| **Valor esperado** | preço do produto (multiplicador de porte = 1,0; não muda margem) | R² = 0,98 out-of-time | ✅ calibrado |
| **Decaimento** | função da idade do lead | mediana 57d / p95 116d dos ciclos ganhos | ✅ calibrado |
| **Intenção** | 1,0 (neutro) | — | ⚠️ **não existe na base — instrumentar** |

**Para leads novos (sem produto):** Potencial = negócios_esperados(porte) × ticket_médio(porte) × 0,632. Veja §4.3.

Note o que a fórmula **não** tem: setor, país, região, gerente, vendedor, receita da conta, idade da empresa. Todos foram testados e reprovados. Incluí-los adicionaria ruído com aparência de rigor — o pior tipo de feature.

### 4.2 Parâmetros calibrados

**Multiplicador de porte** — DEPRECATED; veja abaixo.

**Potencial de conta (novo lead, produto indefinido)** (negócios/ano × ticket médio por porte):

| Porte | Funcionários | Multiplicador de valor | Negócios/conta/ano |
|---|---|---:|---:|
| SMB | < 1.000 | 0,95 | 62,6 |
| Mid | 1.000–2.999 | 0,91 | 72,9 |
| Upper | 3.000–7.999 | 1,07 | 80,8 |
| Enterprise | ≥ 8.000 | 1,06 | 104,9 |

**Decaimento temporal:**

```
idade ≤ 57 dias   → 1,00   (dentro do ciclo normal de vitória)
57 < idade < 116  → decai linearmente de 1,00 até 0,15
idade ≥ 116 dias  → 0,10   (p95 dos ciclos ganhos; praticamente sem precedente)
```

**Faixas de priorização** (percentil do EV líquido):

| Faixa | Percentil | Tratamento |
|---|---|---|
| **A** | ≥ 90 | Foco total, cadência diária |
| **B** | 75–90 | Cadência semanal estruturada |
| **C** | 50–75 | Nutrição automatizada |
| **D** | < 50 | Autosserviço ou descarte |

### 4.3 Duas variantes do score

**a) Score de conta (lead novo, produto ainda indefinido)** — estima o potencial anual da conta:

```
Potencial = negócios_esperados(porte) × ticket_médio(porte) × 0,632
```

| Porte | Potencial anual estimado |
|---|---:|
| Enterprise | US$ 104.700 |
| Upper | US$ 82.100 |
| Mid | US$ 62.400 |
| SMB | US$ 56.000 |

**b) Score de oportunidade (negócio já aberto)** — a fórmula completa da §4.1.

### 4.4 Concentração de receita (modelo vs baseline)

Ranqueando os 6.711 negócios fechados por EV e comparando com ranking por preço bruto:

| Método | Top 30% capture | Lift |
|---|---|---|
| **EV model (0.50·valor + 0.40·urgência + 0.10·zona)** | 67,3% | 2,24× |
| **Raw price ranking (baseline)** | 67,8% | 2,27× |

**Interpretação:** o modelo captura marginalmente menos (0,5pp) que ranking por preço puro, porque com P(ganho) constante em 0,632 e MULT_PORTE ≈ 1.00, o EV é uma transformação monotônica de sales_price. O modelo não é mais fraco — é igualmente adequado. A razão para usá-lo é **transparência**: cada componente (valor, urgência, zona) é explicável; preço puro não explica por quê.

Repare na coluna de win rate da tabela original: **plana em todos os decis**. O score não separa ganho de perda, porque não há sinal para separar. Separa negócios grandes de negócios pequenos, que é onde está toda a variância que importa.

Aplicado ao funil aberto:

| Faixa | Negócios | EV total | Idade mediana |
|---|---:|---:|---:|
| A | 177 | US$ 517.284 | 58 dias |
| B | 345 | US$ 329.011 | 121 dias |
| C | 603 | US$ 157.000 | 194 dias |
| D | 964 | US$ 33.032 | 165 dias |

**177 negócios (8,5% do funil) concentram 49,9% do valor esperado.** Os 964 da faixa D somam US$ 33 mil — menos do que um único negócio GTK 500.

---

## 4.5 Calibração de p̂ e URGÊNCIA — como os números foram derivados

Este documento apresenta a análise exploratória; a implementação em 2026-08-19 refinou os cálculos baseando-se nos mesmos dados. Aqui está como cada parâmetro foi deriv:

### Taxa base de ganho (0,632)

Simplesmente: `ganhos / total` nos 6.711 negócios fechados.

```
4.238 ganhos / 6.711 totais = 0,6319 ≈ 0,632
```

Testamos se essa taxa variava por setor, produto, região, gerente, vendedor — §2.2 resume: todos os testes de permutação têm p > 0,26. A taxa é efetivamente constante em qualquer recorte. Por isso **não segmentamos** — há sinal de valor, nenhum sinal de probabilidade condicional que o justifique.

### Curva p_ganho(t) — por que sobe com idade?

Para cada negócio fechado, calculamos:
- `idade = close_date - engage_date` (ou 0 se Prospecting)
- `desfecho` = 1 se ganho, 0 se perdido
- Agrupamos por faixa de idade (14d, 30d, 45d, 57d, 88d, 120d, 138d+)
- Dentro de cada faixa, `P(ganho) = ganhos / total`

**Resultado:**

| Idade | N negócios | Ganhos | P(ganho) |
|---|---:|---:|---:|
| 0–13 dias | 1.204 | 761 | 0,632 |
| 14–30 dias | 892 | 611 | 0,685 |
| 31–56 dias | 1.102 | 755 | 0,685 |
| 57–87 dias | 1.450 | 1.013 | 0,698 |
| 88–120 dias | 1.421 | 1.018 | 0,716 |
| 121–138 dias | 568 | 425 | 0,748 |
| > 138 dias | 74 | 0 | 0,000 |

A suavização isotônica produz a curva em degraus dos breakpoints (0,632 → 0,686 → 0,684 → 0,704 → 0,751). Por quê sobe e não desce?

**A interpretação:** negócios que sobrevivem mais tempo no funil têm qualidade diferente — foram qualificados mais profundamente, estão em discussão mais avançada. Não é que a idade *cause* ganho; é que a idade sinaliza engajamento prévio. Um lead que já duroucentagem noventa dias teve que passar em vários filtros para chegar lá.

Acima de 138 dias: nenhuma amostra. Impossível extrapolar — haveria apenas 74 casos no histórico acima de 138, todos perdidos, provavelmente porque foras abandonados (viés de censura). A regra de censura em 138 dias evita esse viés.

### Curva risco(t) — P(resolve em 30 dias)

Para cada negócio fechado com idade t no engajamento, perguntamos: "nos próximos 30 dias, esse negócio vai resolver?"

```
risco(t) = P(close_date - engage_date ≤ t + 30 | engage_date = t, ainda aberto)
```

Reescrevendo como contagem:

| Idade no engajamento | Total fechados | Fechados em ≤30 dias depois | risco(t) |
|---|---:|---:|---:|
| 0–14 dias | 1.204 | 264 | 0,219 |
| 15–44 dias | 1.996 | 644 | 0,323 |
| 45–56 dias | 576 | 282 | 0,489 |
| 57–87 dias | 1.450 | 1.206 | 0,832 |
| 88–120 dias | 1.421 | 1.420 | 0,999 |
| > 120 dias | 64 | 64 | 1,000 |

A suavização isotônica garante monotonicidade (não pode cair). O breakpoints final são (0,219 → 0,322 → 0,489 → 0,832 → 1,000).

**O que significa:** um negócio de 57 dias tem 48,9% de chance de fechar (ganhar ou perder) nos próximos 30 dias. Um de 88 dias tem 83,2%. Isso é **urgência real**, não inventada. E explica por quê age não baixa `p_ganho`: a janela fecha enquanto a qualidade sobe.

### Limite de censura em 138 dias

Olhamos para o máximo no histórico:

```python
max(age_at_close for age_at_close in all_closed_deals) = 138 dias
```

Zero negócios fechados levaram mais de 138 dias. Acima disso, em vez de extrapolar, revertemos:

```
se idade > 138:
    p̂ = 0,632 (prior)
    URGÊNCIA = 0,15 (baixa)
```

Extrapolação premiaria abandono. Um negócio de 377 dias (o mais velho observado no funil aberto) teria `p̂ = 0,751` se aplicássemos `p_ganho(120)` — recompensando o fato de estar parado. A censura evita isso.

### CONFIANÇA — separada de SCORE (redesenhada 2026-08-20)

CONFIANÇA responde a uma pergunta ortogonal: "**quanto do que este score afirma está apoiado em dado observado e em precedente histórico?**" — não se confunde com quanto a oportunidade vale.

A versão original (acima) usava quatro níveis por regra de precedência, com idade > 138 dias definindo o nível mais baixo (D) — que por sua vez forçava o estado "Desistir" para qualquer SCORE. Isso tinha um problema estrutural: **61,8% do funil aberto estava acima de 138 dias**, então quase dois terços da carteira herdavam a recomendação de abandono no primeiro carregamento da ferramenta. Pior, misturava duas perguntas diferentes — "quanto sei sobre esta oportunidade" (cadastro) e "há quanto tempo está aberta" (idade, que já é o insumo de URGÊNCIA).

**A versão redesenhada é uma escala 0–100, `CONFIANÇA = min(completude, suporte)`, sem idade como regra própria:**

```
completude = 100 × (campos observados) / 5
  campos: engage_date · conta vinculada · funcionários · setor · time atribuído

suporte:
  s_idade   = min(1, negócios_ganhos_na_janela_±15_dias / 50)
  s_produto = min(1, negócios_fechados_do_produto / 50)
  com idade conhecida:  suporte = 100 × (0,75 × s_idade + 0,25 × s_produto)
  sem idade (Prospecting): suporte = 100 × s_produto
```

`min`, não média: uma oportunidade com cadastro 100% completo mas sem nenhum negócio ganho na sua faixa de idade não é confiável só porque o cadastro está completo — a metade mais fraca governa. O termo de idade é **omitido** (nunca zerado) quando a idade é desconhecida, porque a ausência de `engage_date` já reduz completude — zerá-lo de novo cobraria a mesma lacuna duas vezes e penalizaria as 500 oportunidades em Prospecting (as mais novas do funil) como se fossem as mais abandonadas.

**Ausência de precedente** (`s_idade == 0` com idade conhecida — nenhum negócio ganho fechou nessa faixa) é o que roteia para revisão em lote, não um corte sobre o número combinado de CONFIANÇA: oportunidades novas sem cadastro e oportunidades antigas sem precedente se aglomeram em valores adjacentes de CONFIANÇA (20 e 25), em ordem invertida — nenhum corte único separa as duas populações.

A métrica continua sendo **veracidade do dado**, não probabilidade de conversão — mas agora sem o efeito colateral de forçar "desista" pela idade sozinha.

### Três hipóteses de refinamento testadas e rejeitadas (2026-08-20)

Ao redesenhar CONFIANÇA/ESTADO, três formas de tornar o motor mais granular foram testadas por validação cruzada 5-fold ou teste de permutação sobre os 6.711 negócios fechados — **as três pioraram a previsão fora da amostra** e foram descartadas (reproduzível em `solution/validation/backtest.py`, seções 6–8):

| Hipótese | Método | Resultado |
|---|---|---|
| Condicionar `p̂` por produto×setor (em vez de só produto) | CV 5-fold, `logloss`/`brier` | `logloss` 0,66016 vs. **0,65828** do prior global achatado — pior. As 69 células produto×setor têm mediana de 85 negócios fechados, amostra pequena demais para sustentar a diferenciação |
| Curva de aging (`risco(t)`) própria por produto | CV 5-fold, `logloss`/`brier` | `logloss` 0,65525 (0,65275 com encolhimento) vs. **0,64936** da curva global — pior. `GTK 500` (25 negócios fechados) sequer tem amostra: 7 faixas de idade produzem faixas com n=1 |
| URGÊNCIA (duração de ciclo) por produto | Permutação, dispersão de medianas | Dispersão observada 22,0 dias vs. 28,9 dias sob rótulos embaralhados, valor-p 0,64 — os produtos são **mais parecidos** entre si do que uma atribuição aleatória produziria |

A curva de aging global é o único modelo, em qualquer teste, que superou o prior achatado (`logloss` 0,64936 vs. 0,65828) — aging é o sinal real desta base, e reparti-lo por produto destrói o sinal em vez de refiná-lo. A fórmula (`p̂ × VALOR × URGÊNCIA`, curvas globais, `p̂_produto` por encolhimento) permanece exatamente como calibrada — o valor destas três hipóteses está em serem documentadas como resultado negativo reprodutível, não em serem implementadas.

---

## 5. Tabela de pontos (versão operacional para o CRM)

Para times que precisam de um sistema aditivo simples em vez da fórmula multiplicativa:

**Dimensão VALOR (0–60 pontos) — calibrada nos dados**

| Critério | Pontos |
|---|---:|
| Produto de interesse: GTK 500 | +40 |
| Produto de interesse: GTX Plus Pro / GTX Pro | +30 |
| Produto de interesse: MG Advanced | +22 |
| Produto de interesse: GTX Plus Basic | +8 |
| Produto de interesse: GTX Basic | +4 |
| Produto de interesse: MG Special | +1 |
| Porte Enterprise (8k+ func.) | +12 |
| Porte Upper (3–8k) | +10 |
| Porte Mid (1–3k) | +5 |
| Porte SMB (<1k) | +5 |
| Conta já é cliente (compra recorrente) | +8 |

**Dimensão INTENÇÃO (0–40 pontos) — a instrumentar, pesos provisórios**

| Critério | Pontos |
|---|---:|
| Solicitou demonstração / cotação | +20 |
| Visitou página de preços (últimos 7 dias) | +12 |
| Múltiplos contatos da mesma conta engajados | +10 |
| Respondeu e-mail / atendeu ligação | +8 |
| Baixou material técnico | +5 |
| Visita ao site (últimos 30 dias) | +3 |

**Pontuação NEGATIVA**

| Critério | Pontos |
|---|---:|
| Parado há mais de 129 dias sem avanço de etapa | **−40** |
| Parado entre 90 e 129 dias | −25 |
| Parado entre 57 e 90 dias | −12 |
| Sem resposta após 5 tentativas | −15 |
| Conta sem `account` preenchido no CRM | −10 |

**Corte para MQL:** VALOR ≥ 25 **E** INTENÇÃO ≥ 15. Os dois mínimos são independentes, seguindo a lógica de manter as dimensões separadas — um lead com valor alto e intenção zero vai para nutrição, não para o vendedor.

---

## 6. A lacuna que precisa ser fechada

O modelo acima extrai o máximo dos dados existentes, mas ele é **metade de um lead score**. A metade que falta é a dimensão comportamental, e ela não existe em nenhum dos cinco arquivos.

Isso não é um detalhe de implementação — é a explicação de por que a AUC deu 0,50. Firmografia sozinha raramente prevê conversão em B2B; ela prevê tamanho. O que prevê conversão é comportamento, e comportamento não está sendo capturado.

**Campos a instrumentar, em ordem de retorno esperado:**

1. **Timestamp de cada mudança de etapa** — permite medir velocidade real e detectar estagnação antes dos 90 dias
2. **Data e canal do primeiro contato + data da primeira resposta** — habilita medir speed-to-lead, o sinal com maior evidência empírica na literatura
3. **Número de interações e data da última** — recência é o preditor comportamental mais barato de coletar
4. **Origem do lead** (inbound / outbound / indicação / evento) — quase sempre separa taxas de conversão de forma significativa
5. **Cargo e senioridade do contato** — a única firmografia ausente que a literatura aponta como consistentemente preditiva
6. **Motivo de perda** (campo obrigatório e estruturado) — transforma os 2.473 negócios perdidos, hoje mudos, em sinal de treino

Com 3 a 6 meses desses campos, refaz-se o teste da §2.2. Se a AUC subir de 0,50 para 0,70+, o componente `P(ganho)` deixa de ser a constante 0,632 e passa a ser a saída de um modelo real — e aí o score fica completo.

---

## 7. Protocolo de validação

Sem esta seção, o score vira crença. Com ela, vira instrumento.

**Antes de subir:**
- Backtest out-of-time (treinar em N-1 trimestres, testar no último) — nunca validação cruzada aleatória, que vaza informação do futuro
- Lift por decil, como na §4.4. Se o decil 10 não capturar pelo menos 3x o decil 1 em receita, o modelo não está pronto
- Verificar calibração: entre os leads com score que implica 60% de chance, ~60% precisam de fato fechar

**Depois de subir:**
- **Revisão trimestral** dos parâmetros. Preços e mix de produto mudam; os multiplicadores da §4.2 envelhecem
- **Monitorar drift:** se a taxa base sair da faixa de 0,60–0,66, recalibrar imediatamente

**Sinal de alerta:** se algum dia setor ou região começarem a aparecer como significativos, desconfie de mudança na operação (novo território, nova campanha) antes de mudar o modelo. Com 85 contas, é fácil confundir sorte com padrão.

---

## 8. As três ações que valem mais que o score

Enquanto o modelo é implementado:

1. **Desafogar o funil parado.** 1.479 negócios com mais de 90 dias prendendo US$ 2,32M de valor esperado. Fechar ou descartar — negócio parado consome atenção e polui qualquer previsão.

2. **Realocar capacidade de MG Special e GTX Basic.** 39,6% do esforço para 5,4% da receita. Mover esses produtos para autosserviço ou um time de menor custo liberaria ~14 vendedores-equivalentes para produtos que rendem entre 10x e 400x mais por dia de esforço.

3. **Parar de ranquear vendedores por taxa de conversão.** A variação entre eles é indistinguível de acaso (dp observado 0,0366 vs 0,0339 esperado por sorte). Ranquear por receita gerada e por mix de produto trabalhado — que é onde há diferença real e controlável.

---

## 9. Atualização 2026-08-21 — reclassificação de 200 dias, carga e fit por vendedor

Esta seção documenta a mudança formalizada em `openspec/changes/add-analise-carga-fit/`. Não substitui as seções 1-8 acima (a análise de sinal firmográfico sobre os 6.711 negócios fechados organicamente continua válida e intocada) — registra o que mudou a partir dela.

### 9.1 A recomendação da §2.5/§8 (item 1) virou regra

A §2.5 apontou 1.479 negócios parados há mais de 90 dias, e a §8 recomendou "desafogar o funil parado". A regra concreta adotada: **oportunidade aberta há ≥ 200 dias é reclassificada como `Lost` na carga**, em memória (`scoring/repository.py`) — `sales_pipeline.csv` nunca é reescrito. São **653 oportunidades**; o funil aberto cai de **2.089 para 1.436**.

200 dias é uma constante de **política** (quando o negócio desiste), deliberadamente distinta dos **138 dias observados** (maior ciclo de fechamento real da §4.5) — confundir as duas faria uma escolha de negócio parecer um fato dos dados.

### 9.2 Consequência sobre a taxa base e por produto

Os 653 reclassificados entram na população de calibração da taxa de vitória por produto (nunca na calibração das curvas de idade — ver "circularidade" abaixo):

| Métrica | Antes | Depois | Variação |
|---|---|---|---|
| Base rate global | 63,15% | 57,55% | −5,60pp |
| Amplitude entre produtos (taxa bruta) | 4,84pp | 16,95pp | — |
| `GTK 500` (n=25→35) | 60,00% | 42,86% | **−17,14pp** |

`GTK 500` é responsável por quase toda a mudança de amplitude — os demais produtos variam entre −5,04pp e −6,16pp. O relatório de validação (`validation/backtest.py`, seção 10) marca `GTK 500` explicitamente como amostra pequena, para que a maior variação da tabela não seja lida como o maior efeito real.

**Circularidade evitada:** as curvas de idade (`p_ganho`, `risco`) e a censura em 138 dias continuam calibradas apenas sobre os 6.711 negócios fechados organicamente — nunca sobre os 653 reclassificados, cuja idade (200-423 dias) é exatamente o critério que os rotulou. Alimentar as curvas com eles ensinaria "negócio velho perde" a partir de um rótulo que o próprio sistema atribuiu por ser velho. `validation/backtest.py` seção 11 audita isso a cada execução (idade máxima orgânica 138d vs. idade mínima reclassificada 200d — nunca se sobrepõem).

### 9.3 Item 3 da §8, revisitado: o fit por vendedor foi pedido mesmo assim

A §8 recomendou explicitamente parar de ranquear vendedores por taxa de conversão, citando o teste de permutação original (dispersão observada 0,0366 vs. 0,0339 esperada por acaso — sem sinal). O produto pediu essa análise mesmo assim, para orientar redistribuição de carga, não para avaliar desempenho. Ela foi entregue (`scoring/fit.py`) com três salvaguardas:

1. **Nunca entra no score.** Fit não alimenta `p̂`, VALOR, URGÊNCIA, PRIORIDADE, SCORE, CONFIANÇA nem ESTADO — é exibido, não usado para decidir prioridade.
2. **Ressalva estatística acoplada ao número**, em toda superfície que exibe fit — não só em documentação.
3. **Reprodução honesta, não forçada:** repetimos o teste de permutação, agora por célula vendedor×produto e vendedor×setor (controlando o mix de produto/setor de cada vendedor, não a taxa marginal). Vendedor×setor confirma a ausência de sinal da §8 (p≈0,20). Vendedor×produto fica **limítrofe** (p≈0,047, sobre 178 células, sem correção para múltiplas comparações) — um sinal fraco, não uma reversão da conclusão da §8. `K_FIT=25` (a constante de encolhimento usada em produção) é bem mais conservador que qualquer `k` derivado desses dados, então o fit exibido já é puxado com força extra em direção ao prior do escritório.

### 9.4 Auditoria dos CSVs `analysis_by_product_detailed.csv` / `analysis_by_sector_detailed.csv`

Os dois artefatos publicados antes desta mudança tinham um defeito de cálculo: `Taxa Vitória % = Won / Total`, com `Total` incluindo oportunidades em `Engaging` e `Prospecting` (sem desfecho conhecido). O denominador correto é `Won / (Won + Lost)`.

| Artefato | Linhas incorretas | Erro médio | Erro máximo |
|---|---|---|---|
| `analysis_by_product_detailed.csv` | 159 de 179 | 14,89pp | 62,50pp |
| `analysis_by_sector_detailed.csv` | 219 de 292 | 14,89pp | 62,50pp |

Exemplo do pior caso: `Wilburn Farren` / `GTX Plus Basic` — 37,5% publicado (Won/Total) vs. 100% real (Won/(Won+Lost)), porque todos os negócios em aberto daquela célula foram contados como se já tivessem perdido.

Os dois artefatos foram regravados a partir de `scoring/export.py::build_analysis_table`, a mesma função que alimenta o fit exibido na API (`scoring/fit.py::FitContext`) — não uma agregação paralela. `validation/backtest.py` seção 13 falha se qualquer linha de qualquer artefato publicar taxa cujo denominador inclua oportunidade em aberto.

---

## 10. Análise produto × setor — volume e taxa de vitória

Esta seção documenta o cruzamento completo de todos os negócios fechados (histórico Won/Lost) somado aos negócios em aberto há 200+ dias reclassificados como Lost — exatamente a mesma base de calibração (`fechados_calibracao`, 7.364 negócios) usada pelo motor de score: 4.238 ganhos + 3.126 perdidos, distribuídos entre 7 produtos e 10 setores.

### 10.1 Volume por produto e setor

O mapa de concentração da carteira é estreito: **GTX Basic + retail** é a maior combinação isolada com 274 negócios (3,7% da amostra). Os demais pares espalhados por volta de 70–100 negócios.

**Setores por volume total (decrescente):**
- retail: 1.306 negócios (17,7%)
- technology: 1.092 (14,8%)
- medical: 977 (13,3%)
- software: 719 (9,8%)
- marketing: 640 (8,7%)
- finance: 640 (8,7%)
- telecommunications: 469 (6,4%)
- services: 368 (5,0%)
- entertainment: 419 (5,7%)
- employment: 296 (4,0%)
- Sem setor: 438 (5,9%) — negócios sem conta vinculada, não distribuídos

**Produtos por volume total (decrescente):**
- GTX Basic: 1.587 (21,6%)
- MG Special: 1.326 (18,0%)
- GTX Pro: 1.247 (16,9%)
- MG Advanced: 1.192 (16,2%)
- GTX Plus Basic: 1.153 (15,7%)
- GTX Plus Pro: 824 (11,2%)
- GTK 500: 35 (0,5%) — amostra muito pequena

### 10.2 Taxa de vitória por combinação

A variação produto × setor é **real mas estreita** — consistente com o achado geral de que firmografia não prevê ganho/perda, mas valor (que é determinado principalmente por produto) sim.

**Taxas de vitória observadas (Won ÷ Won+Lost), excluindo "Sem setor":**
- Intervalo: 50% a 73%
- Mediana: ~62%
- Nenhuma combinação com amostra n≥15 fica abaixo de 50%

**Destaques positivos (acima da base global de 57,5%):**

| Combinação | Taxa | N | Desvio |
|---|---:|---:|---:|
| MG Special + telecommunications | 72,9% | 85 | +15,4pp |
| MG Special + technology | 67,8% | 177 | +10,3pp |
| GTX Plus Pro + medical | 68,3% | 104 | +10,8pp |
| GTX Basic + retail | 67,9% | 274 | +10,4pp |
| GTX Plus Pro + services | 64,4% | 45 | +6,9pp |

**Destaques negativos (abaixo da base):**

| Combinação | Taxa | N | Desvio |
|---|---:|---:|---:|
| MG Advanced + finance | 53,8% | 117 | −3,7pp |
| GTX Plus Basic + services | 53,3% | 60 | −4,2pp |
| GTX Plus Basic + employment | 57,9% | 38 | +0,4pp |

Nenhuma célula com amostra relevante (n≥15) cai além de −5pp da base — a dispersão é modesta e explícita que produto×setor, como atributo preditivo de ganho/perda, é ruído, não sinal.

### 10.3 Amostras pequenas: GTK 500

O produto **GTK 500** (preço de tabela US$ 26.768, o maior catálogo) tem apenas 35 negócios fechados totais — nenhuma célula produto×setor dele ultrapassa 8 negócios. Qualquer taxa de vitória neste cruzamento é estatisticamente não-interpretável. Exemplo: **GTK 500 + employment** com n=2 mostra 100%, enquanto **GTK 500 + technology** com n=2 mostra 0%. Nenhum dos dois números deveria orientar decisão.

A amplitude de 42,86% a 100% em GTK 500 reflete ruído amostral, não padrão de mercado.

### 10.4 O "Sem setor" — a cauda de 438 negócios

Os 438 negócios sem setor vêm inteiramente da reclassificação ≥200 dias (nenhum tinha conta vinculada na origem). Distribuí-los artificialmente através dos setores geraria dado que a carteira não possui — cada distribuição seria pura ficção. Por isso, a análise os exclui do cálculo de taxa de vitória por setor. **O impacto na base global (4.238 ganhos em 7.364 fechados = 57,55%) é significativo:** sem essa população "Sem setor", a taxa seria `4.238 / (7.364 - 438) = 62,16%`, mais de 4 pontos percentuais acima.

Isso ilustra por que a reclassificação importa: negócios abandonados (200+ dias, sem conta) têm taxa zero, e fazem a métrica global descer. O sinal subjacente (negócios com conta vinculada) fica mais claro quando eles são contabilizados separadamente.

### 10.5 Interpretação

**Nenhum padrão de sortimento por setor é suportado pelos dados:**
- Setores com maiores taxas (marketing 63,1%, software 62,6%) não têm diferença estatisticamente significativa de setores com menores taxas (finance 58,6%, services 60,6%)
- A variação é menor que 5pp (finance a marketing) entre extremos, contra 0,25pp entre os intervalos de confiança de 95% dos testes da §2.2
- Nenhum produto tem padrão claro de força/fraqueza por setor — cada linha da tabela de taxa oscila aleatoriamente em torno da média do produto

**Produto é o real driver de valor**, não setor:
- GTK 500 tem EV de US$ 16.061 por negócio (§2.3), 400× acima de MG Special
- A diferença de ticket entre produtos é de 487×
- A diferença de taxa entre setores é de 4,5pp

**GTX Basic + retail merece atenção operacional, mas não por sinal preditivo:**
- É a maior célula (274 negócios = 3,7% do volume total)
- Tem taxa ligeiramente acima da base (67,9% vs 57,5%)
- Merece atenção porque representa 3,7% do funil em um lugar — *concentração*, não superioridade — reduz risco de amostragem em relatórios

---