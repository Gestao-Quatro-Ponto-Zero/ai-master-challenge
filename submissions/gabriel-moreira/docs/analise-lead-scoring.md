# Modelo de Lead Scoring — análise e implementação vigente

> **Base:** 8.800 oportunidades (out/2016–dez/2017), 85 contas, 7 produtos, 35 vendedores.  
> **Histórico:** 6.711 negócios fechados (4.238 ganhos / 2.473 perdidos) + 1.436 em aberto (após reclassificar 200+ dias como Lost).

## Resumo executivo

**O achado que muda tudo:**

- **Setor, porte, gerente, região e país não preveem win/loss** — tudo testado, nenhum estatisticamente significativo. **Vendedor é a exceção**: sinal fraco mas significativo na calibração de 2026-08-21 (p=0,000 sobre a população recalculada; ver [docs/report.md](./report.md) §2 e §12) — nunca usado em `p̂`, mas a base do mecanismo separado de fit por vendedor (sugestão de redistribuição de sobrecarga).
- **Produto sozinho explica ~98% da variação de valor** — diferença de 487× entre preço mínimo e máximo.
- **Conclusão:** lead score baseado em "probabilidade de conversão" seria puro ruído. Score precisa ser de **valor esperado** — priorizar pelo tamanho do prêmio, não pela chance de ganhar, porque a chance é a mesma para todo mundo e o prêmio não é.

**39,6% da capacidade do time gasta em produtos que geram 5,4% da receita.**

---

## 1. Dados: o que não funciona, o que funciona

### 1.1 Win rate é constante para produto/setor/conta — vendedor é a exceção (calibração de 2026-08-21)

| Atributo | P-valor | Conclusão |
|---|---|---|
| Setor | 0,917 | não significativo |
| Produto | 0,116 | não significativo |
| Conta | 0,935 | não significativo |
| Gerente | 0,786 | não significativo (análise anterior, não reproduzida pelo backtest atual) |
| **Vendedor** | **0,000** | **significativo** — sinal fraco, nunca usado em `p̂`; base do fit por vendedor |
| Todos os outros (região, país, porte, receita, idade empresa) | > 0,12 | nenhum muda ganho/perda |

Números de Setor/Produto/Conta/Vendedor reproduzidos por `validation/backtest.py` §2 (ver [docs/report.md](./report.md)); atualizados em 2026-08-21 após a reclassificação de 200 dias, que fez `Vendedor` passar de p=0,264 (não significativo) para p=0,000.

Modelos preditivos testados (regressão logística, gradient boosting, com/sem holdout temporal): **AUC 0,47–0,51** por atributo isolado (equivalente a chute aleatório).

**Conclusão:** produto, setor e conta não discriminam conversão. Vendedor carrega um sinal fraco e estatisticamente significativo, tratado à parte no mecanismo de fit por vendedor ([docs/architecture.md §Carga e fit por vendedor](./architecture.md)), nunca em `p̂`/SCORE. Há sinal de *valor*, nenhum de *probabilidade condicional* ligado a onde a oportunidade cai na hierarquia produto/setor/conta.

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

**Porte é sinal de potencial de CONTA, não de deal.** Setor, zero efeito significativo (p = 0,764).

---

## 2. A fórmula implementada

### 2.1 Princípio central

```
PRIORIDADE = p̂(produto, idade) × VALOR(produto, porte) × mult_setor(produto, setor)

SCORE = percentile(PRIORIDADE vs. 4.238 ganhos históricos) × 100

CONFIANÇA = min(completude, suporte)  [dados? precedente?]

ESTADO = Priorizar | Acompanhar | Qualificar | Revisão em lote
```

**O que NÃO está na fórmula:** setor (p=0,917), gerente (p=0,786), região, país, receita, idade empresa — todos testados, nenhum significativo, incluir seria codificar ruído como rigor. Vendedor **é** testado e mostra sinal fraco mas significativo (p=0,000) — por isso entra num mecanismo à parte (fit por vendedor), nunca em `p̂`/SCORE.

### 2.2 Componentes

| Componente | Valor | Origem |
|---|---|---|
| **p̂ (taxa de vitória por produto)** | 0,58–0,65 | Encolhimento hierárquico em direção a 0,575 global; evita overfitting em amostras pequenas |
| **VALOR** | Preço de lista | Único preditor de receita (R² = 0,98); diferença 487× |
| **URGÊNCIA(idade)** | Função isotônica | Mediana ciclo: 57d; P95: 116d; censura: 138d (máximo observado) |
| **mult_setor** | ±15% | Encolhimento conservador por decisão do produto; nunca afeta roteamento ESTADO |

### 2.3 CONFIANÇA: separada de SCORE

Responde: "quanto dessa oportunidade eu realmente sei?"

```
completude = 100 × (engage_date · account · employees · sector · assigned_to) / 5

suporte:
  s_idade   = min(1, won_in_age_window / 50)
  s_product = min(1, closed_product / 50)
  
  com idade: suporte = 100 × (0,75·s_idade + 0,25·s_produto)
  sem idade: suporte = 100 × s_produto
  
CONFIANÇA = min(completude, suporte)
```

`min`, não média — a metade mais fraca governa. Uma oportunidade com cadastro perfeito mas sem precedente histórico não é confiável.

---

## 3. Calibração: como cada número foi derivado

### 3.1 Taxa base: 57,55%

Histórico: 6.711 fechados organicamente = 4.238 ganhos / 6.711 = 63,15%.

Quando 653 oportunidades abertas ≥200 dias são reclassificadas como Lost (política de abandono), a taxa se reposiciona: 4.238 / (4.238 + 3.126 reclassificados) = 57,55%.

Os testes de diferença por setor, produto, conta, região, gerente indicam p > 0,12 — taxa efetivamente constante nesses recortes. Vendedor é a exceção (p=0,000) — ver §1.1.

### 3.2 Urgência por idade (mediana 57d, P95 116d)

Para cada negócio fechado: idade = close_date − engage_date, agrupado em faixas, calculado P(ganho | faixa) por regressão isotônica.

**Resultado:** P(ganho) sobe com idade — negócios mais antigos foram qualificados mais profundamente. Acima de 138 dias (máximo observado), impossível extrapolar sem viés de censura.

Implementado como:
```
idade ≤ 57 dias      → 1,00
57 < idade < 116     → decaimento linear 1,00 → 0,15
idade ≥ 116 dias     → 0,15
idade > 138 dias     → prior global (0,575)
```

### 3.3 p̂ por produto: encolhimento, não discriminação

Cada produto tem taxa própria (0,58–0,65), calculada como ganhos/(ganhos+perdidos), encolhida em direção ao prior global com força `k` derivada dos dados via `shrinkage.level_stats` (a constante congelada `K_PRODUTO` foi removida em 2026-08-21).

**O encolhimento não é discriminação real** — é proteção contra overfitting. Produtos com amostras pequenas (`GTK 500`, 35 fechados) devem ser puxados em direção ao prior, não tratados como padrão estabelecido.

### 3.4 mult_setor: ±15%, encolhido

Produto×setor tem variação real (4–5pp) — mas **validação cruzada piora** se usado direto para condicionar p̂. Mesmo assim foi implementado com salvaguardas:
- Encolhimento pesado em direção a `p̂_produto` (constante `K_SETOR=25`, não à taxa global)
- Teto ±15%
- Neutro (1,0) quando setor desconhecido (68,7% do funil)
- **Nunca afeta URGÊNCIA, CONFIANÇA ou roteamento ESTADO** — é refinamento marginal de política

### 3.5 Reclassificação 200+ dias (2026-08-21)

653 oportunidades abertas ≥200 dias são reclassificadas como `Lost` em memória (CSV nunca reescrito).

**Impacto:** taxa base global 63,15% → 57,55%; amplitude entre produtos 4,8pp → 17pp.

**Integridade:** curvas de idade (`p_ganho`, `risco`) continuam calibradas só sobre 6.711 fechados organicamente — nunca reclassificados (evita que o sistema aprenda "velho = perde" de um rótulo que ele próprio atribuiu).

---

## 4. Faixas operacionais

| Faixa | Score | Negócios | EV total |
|---|---:|---:|---:|
| **A** | ≥90 | 177 | US$ 517K |
| **B** | 75–90 | 345 | US$ 329K |
| **C** | 50–75 | 603 | US$ 157K |
| **D** | <50 | 964 | US$ 33K |

**177 oportunidades (12% do funil) concentram 50% do valor.**

---

## 5. Validação e monitoramento

**Antes de usar:**
- Backtest out-of-time (não validação cruzada aleatória)
- Lift por decil deve ser ≥3× entre extremos
- Calibração: score 60% deve fechar 60%

**Depois de usar:**
- Revisão trimestral de preços e mix
- Monitorar taxa base — se sair de 0,55–0,60, recalibrar
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

Código de calibração: `scoring/probability.py`, `scoring/urgency.py`, `scoring/setor.py`, `scoring/fit.py`

Backtest reproduzível: `validation/backtest.py` (seções 6–8: três hipóteses rejeitadas; seção 10: reclassificação de 200d; seção 11: integridade de circularidade; seção 13: auditoria de CSVs exportados)

Histórico de decisões: `decisions-log.md` (cada mudança documentada com motivação)

Arquitetura técnica: `architecture.md`
