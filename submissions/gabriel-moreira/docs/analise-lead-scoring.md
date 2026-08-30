# Modelo de Lead Scoring — análise e implementação vigente

> **Base:** 8.800 oportunidades (out/2016–dez/2017), 85 contas, 7 produtos, 35 vendedores.  
> **Histórico:** 6.711 negócios fechados (4.238 ganhos / 2.473 perdidos) + 2.089 em aberto. Toda linha do CSV, com o `deal_stage` que o CRM registrou.

## Resumo executivo

**O achado que muda tudo:**

- **Nada prevê win/loss** — produto, setor, conta, porte, gerente, região, país **e vendedor**: tudo testado, nenhum estatisticamente significativo (permutação p entre 0,262 e 0,965; ver [docs/report.md](./report.md) §1, §2 e §12). Não há exceção.
- **Produto sozinho explica ~98% da variação de valor** — diferença de 487× entre preço mínimo e máximo.
- **Conclusão:** lead score baseado em "probabilidade de conversão" seria puro ruído. Score precisa ser de **valor esperado** — priorizar pelo tamanho do prêmio, não pela chance de ganhar, porque a chance é a mesma para todo mundo e o prêmio não é.

**39,6% da capacidade do time gasta em produtos que geram 5,4% da receita.**

---

## 1. Dados: o que não funciona, o que funciona

### 1.1 Win rate é constante em todo recorte firmográfico — vendedor incluído

| Atributo | P-valor | Conclusão |
|---|---|---|
| Setor | 0,965 | não significativo |
| Conta | 0,947 | não significativo |
| Produto | 0,374 | não significativo |
| Vendedor | 0,262 | não significativo |
| Gerente | 0,786 | não significativo (análise anterior, não reproduzida pelo backtest atual) |
| Todos os outros (região, país, porte, receita, idade empresa) | > 0,12 | nenhum muda ganho/perda |

Números de Setor/Produto/Conta/Vendedor reproduzidos por `validation/backtest.py` §2 (ver [docs/report.md](./report.md)), sobre os 6.711 negócios com desfecho registrado.

Os p-valores de permutação usam a correção add-one `(1+c)/(B+1)`, cujo piso com B=2.000 é 0,0005: a suíte reporta `p < 0,001` e nunca `p = 0,000`, que é impossível como probabilidade (`validation/permutation_tests._p_valor`).

"Não significativo" nesta tabela quer dizer **estes dados não sustentam afirmar um efeito** — não "está provado que não existe efeito". A diferença importa, e a leitura correta de cada número está em §1.1.2.

Modelos preditivos testados (regressão logística, gradient boosting, com/sem holdout temporal): **AUC 0,475–0,523** por atributo isolado e 0,500 combinada (equivalente a chute aleatório).

**Múltiplas comparações.** Seis testes de permutação rodam na suíte — os quatro acima e os dois do fit por vendedor (§1.1.1). Seis testes contra o corte de 0,05 sem correção levariam a chance de ao menos um falso positivo de 5% para 26,5%, então o backtest §2 reporta Holm (controla a chance de *qualquer* falso positivo) e Benjamini-Hochberg (controla a proporção de falsos positivos entre os rejeitados). Nenhum dos seis sobrevive a qualquer das duas — e nenhum precisaria: nenhum chega perto do corte nem sem correção. A correção fica registrada porque a família é o que dá sentido ao corte, não porque algum resultado dependa dela.

### 1.1.1 Não há afinidade vendedor×produto — a pergunta que a palavra "fit" faz

O mecanismo de redistribuição de carga produz um número chamado *fit*, e essa palavra faz uma afirmação específica: **este vendedor vai bem NESTE produto, acima do que o desempenho geral dele e a dificuldade geral do produto já explicam**. Testar isso exige um nulo que preserve os dois efeitos principais e negue só a interação. Dois testes, porque são duas perguntas:

| Nulo | Pergunta | vendedor×produto | vendedor×setor |
|---|---|---|---|
| **Global** — embaralha os rótulos de vendedor, produto/setor fixos por negócio | "Vendedor importa em algum grau?" | p = 0,588 | p = 0,545 |
| **Aditivo** — ajusta `logit(ganho) = α + β_vendedor + γ_dimensão` e sorteia desfechos desse modelo | "Existe afinidade além dos efeitos principais?" | p = 0,874 | p = 0,877 |

O nulo global, sozinho, **não** responde pela afinidade: embaralhar destrói junto o efeito principal do vendedor, que entra inteiro na estatística. Só o nulo aditivo isola a interação — e contra ele a dispersão observada fica *abaixo* da simulada em ambas as dimensões: as células vendedor×produto são mais parecidas entre si do que um mundo sem afinidade nenhuma já produziria.

Uma armadilha de leitura que esta documentação já caiu: as 178 células vendedor×produto **não são 178 testes**. A dispersão é uma estatística *omnibus* — um único teste que agrega todas as células —, então não existe multiplicidade em nível de célula a corrigir. Reproduzido por `validation/backtest.py` §12.

**Conclusão:** nenhum atributo firmográfico discrimina conversão. O fit por vendedor continua existindo como mecanismo de redistribuição de carga ([docs/architecture.md §Carga e fit por vendedor](./architecture.md)) — nunca em `p̂`/SCORE — mas ele ordena candidatos, não mede mérito: a ressalva estatística acoplada a cada número que ele produz é obrigatória justamente porque não há sinal embaixo. Há sinal de *valor*, nenhum de *probabilidade condicional*.

### 1.1.2 Como ler estes p-valores

**O que o p-valor é:** a frequência com que o acaso sozinho — os rótulos embaralhados — produziria
uma diferença entre grupos **pelo menos tão grande** quanto a observada.

**O que ele não é.** As leituras abaixo já foram feitas sobre estes mesmos números, por esta
mesma documentação, e é por isso que estão escritas aqui:

- **`p` não é a probabilidade de o efeito existir.** `p = 0,262` para vendedor não diz "26% de
  chance de vendedor importar". Diz: se vendedor não importasse, 26% dos embaralhamentos já
  produziriam a dispersão que os dados mostram.
- **`p` alto não prova que o efeito não existe.** Ausência de evidência não é evidência de
  ausência: um efeito real, mas pequeno demais para 6.711 negócios, devolveria o mesmo `p` alto.
  A decisão de produto precisa apenas do enunciado mais fraco — *não há base para pôr o atributo
  em `p̂`* — e é só ele que está afirmado em toda esta documentação. Este bullet costumava parar
  aqui, como ressalva qualitativa; §1.1.3 agora quantifica exatamente quão pequeno o efeito
  precisaria ser para escapar.
- **`p = 0,000` não existe.** Com B = 2.000 reamostragens, o menor valor afirmável é
  1/(B+1) = 0,0005 (correção add-one). A suíte reporta `p < 0,001`; qualquer superfície que
  imprima `p = 0,000` está rodando o estimador antigo.

**Dois números de versões anteriores que ainda circulam.** Entre 2026-08-21 e 2026-08-29 esta
documentação reportou `sales_agent p = 0,000` e `vendedor×produto p = 0,041`, e chamou o primeiro
de "a exceção significativa". Nenhum dos dois descreve a população atual — e nenhum sustentava a
conclusão que lhe foi dada, nem na época:

| Número histórico | O que foi lido nele | Valor vigente |
|---|---|---|
| `sales_agent p = 0,000` | "vendedor prevê ganho/perda" | **p = 0,262** (§2) |
| `vendedor×produto p = 0,041` | "há afinidade vendedor×produto" | **p = 0,874** no nulo aditivo, 0,588 no global (§12) |

- **População — derruba os dois.** Ambos vinham do expurgo de 200 dias, que reclassificava 653
  oportunidades paradas como perdidas na carga. O expurgo só adiciona derrota e cai concentrado
  (χ² = 576,4, gl = 29, p < 0,0001 na distribuição entre carteiras; correlação **−0,794** entre
  fração expurgada e taxa de vitória resultante): idade de pipeline lida como habilidade de
  fechar. Removido do motor em 2026-08-29 e medido a cada execução no backtest §10.
- **Estimador — muda o que era lícito afirmar.** `p = 0,000` foi lido como certeza de que há
  sinal; o máximo que aquela execução podia reportar era `p < 0,001`.
- **Nulo — derruba o `0,041` como evidência de fit.** Ele vinha do nulo global, que responde
  "vendedor importa em algum grau?" e não "existe afinidade?" (§1.1.1). Contra o nulo aditivo,
  0,874.
- **Multiplicidade — derruba o `0,041` mesmo aceitando o resto.** Sob Holm sobre os 6 testes da
  suíte, aquele valor precisaria ser ≤ 0,01. Some-se que o mesmo teste imprimiu `0,041` e `≈0,047`
  em duas execuções: com B = 2.000, essa casa decimal é ruído do estimador.

O registro completo de cada correção está em [`decisions-log.md`](../process-log/decisions-log.md),
entradas de 2026-08-29. Os valores vigentes são os desta seção e os de
[`report.md`](./report.md) §2, §10 e §12. As entradas antigas do log preservam o número que
imprimiram na época, cada uma com a correção anexada logo abaixo: são registro histórico, não
resultado atual.

### 1.1.3 Quão pequeno o efeito teria que ser para escapar — o poder dos testes

Um teste que não rejeita só é informativo junto com o seu poder. Sem essa conta, `p = 0,262`
é compatível com duas afirmações muito diferentes — "não há diferença entre vendedores" e "há
uma diferença grande e a amostra é pequena demais" — e a segunda seria cara: conversão a mais
sobre uma carteira inteira é receita. O backtest §14 mede onde fica a fronteira entre as duas.

**A amplitude que salta aos olhos é a amplitude que o acaso entrega.** O melhor vendedor converte
70,4% e o pior 55,0% — 15,42pp de diferença. Trinta carteiras *idênticas* com estes mesmos
tamanhos produzem 14,38pp de mediana (IC95 [9,90; 21,19]). A tabela crua não mostra habilidade;
mostra quantos negócios cada um fechou.

**Mas a dispersão verdadeira não é zero.** Descontando da variância observada a variância
binomial que os tamanhos de carteira já explicam — variância em excesso, a mesma técnica que
`scoring/fit.py` usa para derivar `k` —, sobra **τ̂ = 1,08pp** de desvio-padrão verdadeiro entre
vendedores: positivo, e equivalente a ~4,07pp entre o melhor e o pior. Um quarto do que a tabela
crua sugere, e não zero.

**E o teste não enxergaria τ̂.** O menor τ detectável em 80% das amostras é **3,04pp** — acima
de τ̂. A diferença plausível entre vendedores cai inteira na zona cega:

| Cenário verdadeiro | O teste detecta? |
|---|---|
| dispersão real τ = 1,0pp | 12,6% das amostras |
| dispersão real τ = 2,0pp | 39,0% |
| dispersão real τ = 3,0pp | 79,2% |
| dispersão real τ = 3,5pp | 90,2% |
| um vendedor +6,3pp ("10% a mais" relativo), escolhido *antes* de olhar o dado | 47,6% |
| um vendedor +10pp, escolhido *antes* de olhar o dado | 88,8% |

**As duas leituras extremas estão erradas, portanto.** Não cabe dizer "vendedor é irrelevante" —
τ̂ > 0, e um efeito nessa ordem vale receita sobre uma carteira inteira. Não cabe dizer "há um
sinal pequeno de vendedor" — τ̂ não se distingue de zero, e publicá-lo como medido seria vender
ruído como habilidade, exatamente o erro que §3.5 e o backtest §10 mostram o expurgo de 200 dias
cometendo. O enunciado sustentável é o do meio: **este histórico não consegue ver diferença entre
vendedores**, e o que ele exclui é só o efeito grande.

**Consequência.** Nenhuma no motor: vendedor continua fora de `p̂` e de SCORE, e o fit continua
sendo sugestão de redistribuição de carga com a ressalva acoplada. A consequência é de roadmap —
medir τ̂ exigiria ~2.000 negócios fechados por vendedor (9× o histórico atual) sob alocação
aleatorizada de leads. Aleatorizar remove o confundimento entre habilidade e qualidade da carteira
recebida; não remove a necessidade de amostra. Ver [`roadmap.md`](./roadmap.md) §3.

### 1.2 Valor é altamente previsível (R² = 0,98)

| Produto | Preço | % negócios | % receita | Win rate | EV por negócio |
|---|---:|---:|---:|---:|---:|
| GTK 500 | 26.768 | 0,4% | 4,0% | 0,60 | **16.061** |
| GTX Plus Pro | 5.482 | 11,1% | 26,3% | 0,64 | **3.525** |
| GTX Pro | 4.821 | 17,1% | 35,1% | 0,64 | **3.064** |
| MG Advanced | 3.393 | 16,2% | 22,2% | 0,60 | **2.047** |
| GTX Plus Basic | 1.096 | 15,7% | 7,1% | 0,62 | **681** |
| GTX Basic | 550 | 21,4% | 5,0% | 0,64 | **350** |
| MG Special | 55 | 18,2% | 0,4% | 0,65 | **36** |

**Leitura:** MG Special + GTX Basic = 39,6% dos negócios, 5,4% da receita. Um dia em GTK 500 rende 400× mais que um dia em MG Special. MG Special tem a *maior* taxa de conversão — armadilha perfeita para um score baseado em probabilidade.

### 1.3 Porte: o único firmográfico que importa, mas não para win rate

Porte não muda **chance de ganhar** (win rate plano em todos os portes), muda **volume de compra** (Enterprise compra 68% mais vezes que SMB, com ticket 12% maior).

| Porte | Negócios/conta | Ticket médio | Receita/conta |
|---|---:|---:|---:|
| SMB | 62,6 | 1.416 | 88.560 |
| Enterprise | 104,9 | 1.583 | **166.126** |

**Porte é sinal de potencial de CONTA, não de deal.** Setor tampouco separa ganho de perda: p = 0,965 no teste de permutação reproduzido pelo backtest §2 — o atributo com menos sinal de todos os testados.

---

## 2. A fórmula implementada

### 2.1 Princípio central

```
PRIORIDADE = p̂(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)

SCORE = percentile(PRIORIDADE vs. 4.238 ganhos históricos) × 100

CONFIANÇA = min(completude, suporte)  [dados? precedente?]

ESTADO = Priorizar | Acompanhar | Qualificar | Revisão em lote
```

**O que NÃO está na fórmula:** setor (p=0,965), conta (p=0,947), vendedor (p=0,262), produto (p=0,374), gerente (p=0,786), região, país, receita, idade empresa — todos testados, nenhum significativo, incluir seria codificar ruído como rigor. Setor não entra nem como condicionamento direto nem como multiplicador encolhido sobre `p̂` (ver §3.4). Vendedor entra num mecanismo à parte (fit por vendedor, sugestão de redistribuição de carga), nunca em `p̂`/SCORE.

### 2.2 Componentes

| Componente | Valor | Origem |
|---|---|---|
| **p̂ (taxa de vitória por produto)** | 0,632 para os sete | Encolhimento hierárquico: o nível de produto colapsa (`k = ∞`), então todo produto recebe a taxa global — a tradução em código de "produto não prevê ganho/perda" |
| **VALOR** | Preço de lista | Único preditor de receita (R² = 0,98); diferença 487× |
| **URGÊNCIA(idade)** | Função isotônica | Mediana ciclo: 57d; P95: 116d; censura: 138d (máximo observado) |

### 2.3 CONFIANÇA: separada de SCORE

Responde: "quanto dessa oportunidade eu realmente sei?"

```
completude = 100 × (engage_date · account · employees · sector · assigned_to) / 5

suporte:
  s_idade   = min(1, won_in_age_window / 50)
  s_product = min(1, closed_product / 50)
  
  com idade: suporte = 100 × (0,65·s_idade + 0,20·s_produto) / 0,85
  sem idade: suporte = 100 × s_produto
  
CONFIANÇA = min(completude, suporte)
```

`min`, não média — a metade mais fraca governa. Uma oportunidade com cadastro perfeito mas sem precedente histórico não é confiável.

---

## 3. Calibração: como cada número foi derivado

### 3.1 Taxa base: 63,15%

4.238 ganhos / 6.711 fechados = 63,15%. Uma população só — todo negócio que o CRM registra como fechado, e nenhum outro.

Os testes de diferença por setor, produto, conta, vendedor, região e gerente indicam p ≥ 0,262 — taxa efetivamente constante em todos esses recortes.

### 3.2 Urgência por idade (mediana de ciclo 57d, P95 116d)

Para cada negócio fechado: idade = close_date − engage_date, agrupado em faixas, calculadas duas curvas por regressão isotônica — `p_ganho(t)` = P(ganho | ainda aberto na idade t) e `risco(t)` = P(resolver nos próximos 30 dias | ainda aberto na idade t).

**Resultado:** `p_ganho(t)` **sobe** com a idade (0,632 → 0,751) — negócios mais antigos foram qualificados mais profundamente. O que a idade consome é a janela de decisão, e é isso que `risco(t)` mede. Por isso URGÊNCIA usa `risco(t)`, não um decaimento inventado sobre `p_ganho`.

Implementado como leitura em degraus dos breakpoints calibrados (`scoring/constants.py`):
```
URGÊNCIA — risco(t)
  idade 0–44     → 0,219
  idade 45–56    → 0,322
  idade 57–87    → 0,489
  idade 88–109   → 0,832
  idade ≥ 110    → 1,000
  Prospecting    → 0,47   (sem idade a medir)
  idade > 138    → 0,15   (censura: piso, não extrapolação)

p̂ — p_ganho(t) renormalizado por p̂_produto
  idade > 138    → 0,632  (censura: reverte ao prior global)
  idade > 120    → congela em p_ganho(120) = 0,751
```

Acima de 138 dias (máximo observado entre os fechados) extrapolar seria viés de censura: o motor reverte ao prior em vez de continuar a curva — forward-fill daria `p̂ = 0,751` justamente ao negócio mais parado do funil.

### 3.3 p̂ por produto: o nível colapsa, e é isso que deveria acontecer

Cada produto tem taxa bruta própria (0,60–0,65), mas a variância entre elas é **menor** que o ruído amostral esperado: variância em excesso −0,0012, logo `k = ∞` e o nível inteiro colapsa. Todo produto recebe a taxa global, 0,632. Amplitude de p̂ entre produtos: **0,00pp**.

`k` é derivado em tempo de carga via `shrinkage.level_stats`, sem nenhuma constante congelada, então esse colapso é resultado do cálculo e não uma decisão embutida — se uma recalibração futura encontrar sinal real por produto, o nível volta a contribuir sozinho.

**Isto é coerência, não perda.** A §1.1 diz que produto não prevê ganho/perda (p=0,374); seria contraditório o motor diferenciar p̂ por produto assim mesmo. O que separa os produtos no SCORE é preço — 487× de amplitude — não chance.

### 3.4 Setor: testado e mantido fora de p̂

Produto×setor tem variação bruta real (4–5pp) — e ela não sobrevive a nenhuma das duas validações que medem se essa variação carrega sinal:

| Evidência | Resultado |
|---|---|
| Variância em excesso do nível produto×setor | ≤ 0 → `k = ∞`: o nível colapsa, e o encolhimento estatisticamente correto é `1,000` |
| Validação cruzada 5-fold (logloss fora da amostra) | condicionar por produto×setor: 0,66974 · não condicionar: 0,66795 → **pior** |

Os 4–5pp de variação bruta são o que a variância amostral já explica sozinha em células dessa densidade — é exatamente o padrão que o teste de permutação por setor (p=0,965, §1.1) descreve. É o mesmo critério que mantém gerente, região, receita e idade da empresa fora da fórmula: setor não entra em `p̂`, em SCORE nem em suporte, em forma nenhuma.

Setor continua sendo lido fora do score: completude de CONFIANÇA, fit vendedor×setor da redistribuição de carga, `analysis_by_sector_detailed.csv` e filtros de interface. O histórico da decisão (setor chegou a entrar como ajuste de produto e foi retirado) está em [decisions-log.md](../process-log/decisions-log.md).

### 3.5 Nenhuma régua de idade vira desfecho

A calibração usa só desfecho registrado. Nenhuma oportunidade em aberto é convertida em perda por
régua de idade, por mais parada que esteja: um `Lost` atribuído por nós não é um dado, é uma decisão
nossa entrando na taxa que o motor aprende — e ela não cairia por igual entre produtos e carteiras,
então viraria diferença de p̂ e "desempenho" de vendedor onde o dado observado não tem nenhuma
(mecanismo quantificado em `validation/backtest.py` §10, que recalcula o cenário a cada execução
**sem aplicá-lo**; §11 trava por teste que nenhum desfecho da calibração foi atribuído por nós).

As 653 oportunidades paradas há ≥200 dias são pontuadas como qualquer outra: acima da censura de
138 dias `p̂` reverte ao prior e URGÊNCIA vai ao piso de 0,15, então elas afundam na fila por
aritmética. A contagem aparece na tela de metodologia como limitação de dados ("o CRM não registra
abandono"). Se a operação quiser uma regra de abandono, ela precisa ser um evento registrado no CRM
— ver [roadmap.md](./roadmap.md).

---

## 4. Faixas operacionais

Sobre as 2.089 oportunidades abertas (PRIORIDADE em dólares, valor em risco — calculada e exportada, nunca exibida ao vendedor):

| Faixa | Score | Negócios | PRIORIDADE total | % do valor em risco |
|---|---:|---:|---:|---:|
| **A** | ≥90 | 98 | US$ 315K | 31,4% |
| **B** | 75–90 | 260 | US$ 338K | 33,7% |
| **C** | 50–75 | 377 | US$ 186K | 18,6% |
| **D** | <50 | 1.354 | US$ 165K | 16,4% |

**98 oportunidades (4,7% do funil) concentram 31,4% do valor em risco; as 358 das faixas A+B (17,1%) concentram 65,0%.**

A faixa D é grande porque o funil inteiro está aqui — inclusive as 653 paradas há ≥200 dias, que a censura de idade empurra para o fundo. Elas não somem da conta; só param de disputar o topo.

---

## 5. Validação e monitoramento

**Antes de usar:**
- Backtest out-of-time (não validação cruzada aleatória)
- Lift por decil deve ser ≥3× entre extremos
- Calibração: score 60% deve fechar 60%

**Depois de usar:**
- Revisão trimestral de preços e mix
- Monitorar taxa base — se sair de 0,60–0,66, recalibrar (é o gatilho de emergência declarado em `scoring/constants.py`)
- Se setor ou região começarem a aparecer como significativos, suspeite de mudança operacional (novo mercado, nova campanha), não do modelo

---

## 6. O que não foi implementado (falta comportamental)

O modelo atual extrai 98% do sinal disponível *mas* deixa de fora toda a dimensão comportamental — não há timestamps de contato, respostas, mudanças de etapa, recência, canal de origem.

Isso é a razão pela qual AUC foi 0,50 com todos os preditores que temos: firmografia sozinha prevê tamanho, não conversão.

Com 3–6 meses instrumentando:
1. Timestamp de mudanças de etapa
2. Data e canal de primeiro contato
3. Número de interações e data da última
4. Origem do lead (inbound/outbound/indicação/evento)
5. Cargo e senioridade do contato
6. Motivo de perda (campo estruturado)

…o componente p̂ deixa de ser constante e passa a ser a saída de um modelo real. Aí o score fica completo.

---

## Referências

Código de calibração: `scoring/shrinkage.py`, `scoring/curves.py`, `scoring/model.py`, `scoring/fit.py`

Backtest reproduzível: `validation/backtest.py` (seções 6–8: três hipóteses rejeitadas; seção 10: guarda contra desfecho atribuído por régua de idade, medido e não aplicado; seção 11: ausência de desfecho atribuído na calibração; seção 13: auditoria de CSVs exportados)

Histórico de decisões: [`../process-log/decisions-log.md`](../process-log/decisions-log.md) (cada mudança documentada com motivação)

Arquitetura técnica: [`architecture.md`](./architecture.md)
