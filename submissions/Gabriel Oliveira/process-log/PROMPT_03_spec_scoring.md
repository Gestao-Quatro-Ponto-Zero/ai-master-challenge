# Prompt 03 — Spec do Scoring (AGENT-A + SKILL-02)

> **Prompt emitido:**

```
[AGENT: ARCHITECT] [SKILL: SPEC-DRIVEN]

Escreva SPEC da função score_deal(row, agent_winrate).
Requisitos não-negociáveis:
- Score 0-100
- 6 componentes com pesos informados por mim (passo uma tabela)
- Explicabilidade: retornar dict {componente: (subscore, label_ptBR)}
- Sem ML, só regras/MinMax
- Edge case: engage_date NaN → componente velocity=0 com label explicativa

Componentes e pesos:
- stage advancement 25%
- pipeline velocity 20%
- account size 20%
- product value 15%
- agent track record 15%
- deal value 5%

Saída: SPEC markdown, não código. Quero aprovar antes do build.
```

---

# SPEC — `score_deal(row, agent_winrate)`

**Status:** ✅ Aprovada para build (Prompt 04)
**Spec author:** AGENT-A (Architect mode)
**Grounded in:** `eda_report.txt` (Prompt 02) — todos os ranges numéricos são empíricos, não estimados

---

## 1. Propósito (1 frase)

Atribuir a cada **deal aberto** (stage `Prospecting` ou `Engaging`) um score 0–100 que represente
**prioridade de atenção do vendedor**, com um breakdown explicável em linguagem natural PT-BR.

## 2. Inputs

| Parâmetro | Tipo | Conteúdo |
|-----------|------|----------|
| `row` | `dict[str, Any]` | Uma linha do `sales_pipeline` já enriquecida com `revenue`, `employees`, `sales_price` (joins com accounts/products). Deve conter: `opportunity_id, sales_agent, product, account, deal_stage, engage_date (datetime | NaT), close_value` |
| `agent_winrate` | `dict[str, float]` | Mapa `{sales_agent: win_rate}` onde `win_rate ∈ [0,1]` calculado do histórico (`Won / (Won+Lost)`). Pode não conter o agente se for novo — ver edge E5 |
| `today` | `pd.Timestamp` *(opcional, default `pd.Timestamp.now()`)* | Referência temporal para idade do deal. Parametrizado para reprodutibilidade |

## 3. Output

```python
Tuple[int, Dict[str, Tuple[float, str]]]
```

- **score** (`int`): 0–100 — soma ponderada dos subscores, clipped e arredondado
- **breakdown** (`dict`): chaves são os 6 componentes, valores são tuplas `(subscore_0_100, label_ptBR)`

Exemplo canônico (para validação no build):

```python
{
  "stage":         (75.0, "Stage: Engaging — já passou por descoberta inicial"),
  "velocity":      (60.0, "Idade: 18 dias — dentro da janela ótima (15-60 dias)"),
  "account_size":  (80.0, "Conta: Technology, $42K receita, 320 funcionários"),
  "product_value": (40.0, "Produto: Analytics Plus ($3.200 ticket)"),
  "agent":         (65.0, "Vendedor: 58% histórico de fechamento"),
  "deal_value":    (30.0, "Valor: $1.490 esperado se fechar"),
}
# score final = 75×0.25 + 60×0.20 + 80×0.20 + 40×0.15 + 65×0.15 + 30×0.05 = 62.5 → 62
```

## 4. Critérios de Aceitação Mensuráveis

| # | Critério | Como validar |
|---|----------|--------------|
| AC1 | Todo deal aberto (`deal_stage ∈ {Prospecting, Engaging}`) recebe `score ∈ [0, 100]` | Rodar em todos os 4.708 deals abertos; nenhum score <0 ou >100 |
| AC2 | `breakdown` contém exatamente 6 chaves: `stage, velocity, account_size, product_value, agent, deal_value` | `assert set(breakdown.keys()) == {…}` |
| AC3 | Cada subscore ∈ [0, 100] e cada label é `str` não-vazia em PT-BR | Loop de validação |
| AC4 | Score final = `round(sum(subscore × weight))` com pesos [0.25, 0.20, 0.20, 0.15, 0.15, 0.05] | Recalcular e comparar |
| AC5 | Inputs idênticos produzem outputs idênticos (determinístico) | Rodar 2x, comparar |
| AC6 | Deal Won/Lost → `score=0` com label único `"deal já fechado/lost — fora do escopo de priorização"` | Filtrar e validar |
| AC7 | Deal com `engage_date=NaT` → `velocity=(0.0, "sem data de abertura — sem dados para maturação")`, outros componentes ainda calculados | Caso E1 |
| AC8 | Top 10 deals por score têm `deal_stage ∈ {Engaging}` predominantemente (>70%) | Sanity de ranking |
| AC9 | Nenhum hardcoded path ou nome de coluna inventado | `grep` no diff |

## 5. Especificação dos 6 Componentes

Cada componente segue o template: **input → hipótese → lógica → label**.

### 5.1 — Stage Advancement (peso 25%)

- **Input:** `row["deal_stage"]`
- **Hipótese (H1 da EDA):** deals em `Engaging` convertem mais que `Prospecting` porque já passaram da fase de descoberta
- **Lógica:** mapping ordinal (não MinMax — variável discreta):
  - `Engaging` → subscore 100
  - `Prospecting` → subscore 50
  - `Won` / `Lost` → subscore 0 (e função retorna score=0 global, ver AC6)
- **Label:** `"Stage: {stage} — {descrição}"`
  - `Engaging` → `"já passou por descoberta inicial"`
  - `Prospecting` → `"contato inicial ainda em prospecção"`

### 5.2 — Pipeline Velocity (peso 20%)

- **Input:** `row["engage_date"]` (datetime | NaT), `row["deal_stage"]`, `today`
- **Hipótese (H2 da EDA, REFINADA):** idade crua NÃO discrimina Won vs Lost (EDA mostrou 61≈61 dias).
  Logo, avalio **maturação relativa à janela ótima** derivada da mediana de fechamento (~62 dias,
  IQR 32–91).
- **Lógica (piecewise, não MinMax puro):**
  - `engage_date = NaT` → subscore 0, label específico (edge E1)
  - `idade = (today - engage_date).days`
  - `15 ≤ idade ≤ 60` → subscore 100 (janela ótima)
  - `idade < 15` → subscore linear `idade/15 × 60` (deal muito novo, ainda maturando)
  - `60 < idade ≤ 90` → subscore linear descrescente de 100→60 (esquentando)
  - `idade > 90` → subscore linear decrescente de 60→0 em 90 dias adicionais (esfriou; clip em 0)
- **Label:** `"Idade: {idade} dias — {ótimo/maturando/esquentando/frio}"`

### 5.3 — Account Size (peso 20%)

- **Input:** `row["revenue"]`, `row["employees"]` (já em row por join com accounts)
- **Hipótese (H4):** contas maiores (receita/funcionários) geram deals maiores e mais estratégicos
- **EDilight ranges:** `revenue ∈ [1.881, 287.787]` (mediana 23.968); `employees ∈ [8, 5.720]`
- **Lógica:**
  - `sub_revenue = MinMax(revenue, 1881, 287787) × 100`
  - `sub_employees = MinMax(log1p(employees), log1p(8), log1p(5720)) × 100` (log por causa do range amplo)
  - `subscore = (sub_revenue + sub_employees) / 2`
- **Edge E3:** conta não encontrada → subscore 25 (neutral, abaixo da média), label `"Conta: dados indisponíveis"`
- **Label:** `"Conta: {industry}, ${revenue} receita, {employees} funcionários"`

### 5.4 — Product Value (peso 15%)

- **Input:** `row["sales_price"]` (depois de join com products por `product`)
- **Hipótese:** produtos de ticket maior têm maior payoff se fecharem
- **Range EDA:** 7 produtos, preços `$800` (CRM Connect) a `$25.000` (GTX Enterprise)
- **Lógica:** `subscore = MinMax(sales_price, 800, 25000) × 100`
- **Edge E4:** produto não encontrado → subscore 25, label `"Produto: dados indisponíveis"`
- **Label:** `"Produto: {product} (${sales_price} ticket)"`

### 5.5 — Agent Track Record (peso 15%)

- **Input:** `row["sales_agent"]`, `agent_winrate`
- **Hipótese (H3, CONFIRMADA pela EDA):** vendedor com win rate maior converte mais. Faixa observada
  **42% a 67%** (dispersão de 25 p.p.) — discrimina significativamente
- **Lógica:** `subscore = MinMax(win_rate, 0.4237, 0.6696) × 100`
- **Edge E5:** agente novo (não no dict) → subscore 50 (média neutra), label `"Vendedor: novo, sem histórico ainda"`
- **Label:** `"Vendedor: {win_rate_pct}% histórico de fechamento"`

### 5.6 — Deal Value (peso 5%)

- **Input:** `row["close_value"]` (para deals abertos, é **valor esperado**, não realizado — ver EDA:
  Engaging mean $2.141, Prospecting mean $2.239)
- **Hipótese:** deals de maior valor justificam mais atenção
- **Lógica:** `subscore = MinMax(close_value, 0, 21578) × 100` (range observado em deals não-Won)
- **Edge E6:** `close_value = 0` em deal aberto → subscore 10 (floor baixo, não zero — para não
  mascarar deals com outros componentes altos), label `"Valor: ainda não atribuído"`
- **Label:** `"Valor: ${close_value} esperado se fechar"`

## 6. Pré-computação (responsabilidade do caller, não da função)

A função recebe `row` já enriquecida. O caller (`score_pipeline.py` ou o app) é responsável por:

1. Carregar `accounts.csv` → dict `{account_id: {revenue, employees, industry, …}}`
2. Carregar `products.csv` → dict `{product: {sales_price, …}}`
3. Carregar `sales_teams.csv` → dict `{sales_agent: {manager, regional_office}}`
4. Computar `agent_winrate` do `sales_pipeline.csv` (Won / (Won+Lost)) estratificado por agente
5. Fazer join de `revenue`, `employees`, `industry`, `sales_price` em cada row
6. Converter `engage_date` e `close_date` com `format='%m/%d/%Y'` (ver EDA, armadilha A1)
7. Filtrar deals abertos (`deal_stage ∈ {Prospecting, Engaging}`) antes de chamar `score_deal`

Decisão arquitetural: manter `score_deal` pura e testável — sem I/O de arquivos dentro dela.

## 7. Edge Cases Catalog

| # | Cenário | Comportamento |
|---|---------|---------------|
| E1 | `engage_date = NaT` | velocity=(0, "sem data de abertura — sem dados para maturação"); outros componentes normais |
| E2 | `deal_stage = Won` ou `Lost` | retorna `(0, {"_": (0, "deal já fechado/lost — fora do escopo de priorização")})` global |
| E3 | `account` não em accounts | account_size=(25, "Conta: dados indisponíveis") |
| E4 | `product` não em products | product_value=(25, "Produto: dados indisponíveis") |
| E5 | `sales_agent` não em agent_winrate | agent=(50, "Vendedor: novo, sem histórico ainda") |
| E6 | `close_value = 0` em deal aberto | deal_value=(10, "Valor: ainda não atribuído") |
| E7 | Deal brand-new (`idade=0`) | velocity=(0, "Idade: 0 dias — recém-criado, sem maturação") |
| E8 | `close_value` negativo ou outlier (>3× max) | clipa para max, log de warning |

## 8. Dependências

- `numpy` (para `log1p`, clip)
- `pandas` (apenas para `Timestamp` no cálculo de idade)
- **NÃO usar** `sklearn`, `scipy` ou qualquer ML nesta versão

## 9. Não-Goals (explícito)

Estes são **fora** desta SPEC (poderiam ser versão 2):

- ❌ Treinar modelo preditivo (Gradient Boosting, Logit) para comparar —— fica como diferencial posterior, se houver tempo
- ❌ Calibrar pesos por regressão — pesos são definidos por hipótese de negócio + EDA, não otimizados
- ❌ Ajuste por sazonalidade ou cohort temporal
- ❌ Feature de concentração de pipeline por agente (citada no Prompt 01 como feature AI Master não-óbvia — fica como follow-up)
- ❌ Probabilidade de fechamento calibrada (score é **prioridade de atenção**, não probabilidade)

## 10. Sanity checks pós-build

Após implementar (Prompt 04), validar:

1. **Distribuição de scores:** Попsa não deve ser bimodal extrema (todos 0 ou todos 100 = bug)
2. **Correlação com outcome histórico:** aplicar função em deals já Won/Lost (usando `engage_date`
   eixtente, ignorando E2) e verificar que Won scores > Lost scores em média (sanity indireto)
3. **Top 10:** ao menos 7 dos top-10 deals por score devem ser `Engaging` (xAC8)
4. **Edge E1 test:** rodar função em row sintética com `engage_date=NaT` e validar label
5. **Determinismo:** rodar 2x → idêntico (xAC5)

---

## Decisões humanas críticas nesta SPEC

1. **Stage é mapping ordinal, não MinMax** — variável discreta, MinMax não se aplica
2. **Velocity é piecewise, não MinMax** — hipótese de janela ótima (refinada da EDA que refutou
   H2 em forma crua)
3. **Account employees usa log1p** — range 8 a 5720 é demasiado; raw MinMax esmagaria ao fundo
4. **Account size = média dos dois subscores** — receita e funcionários são proxies complementares
5. **Edge E5 (agente novo) → subscore 50**, não 25 — premiar novos com score médio neutro evita
   punir injustamente novos vendedores (decisão de equity de produto)
6. **Won/Lost não são prioritizáveis** — score_deal retorna 0 com label único, deixando o caller
   filtrar. Evita poluir UI com "deals já fechados" ranqueados
7. **Score é prioridade de atenção, não probabilidade** — documentado em Non-Goals para evitar
   mal-entendido pelo vendedor

---

_Estado do harness após Prompt 03:_
- Agent: ARCHITECT ✅ (modo thinker, output em markdown)
- Skill: SPEC-DRIVEN ✅ (propósito, inputs, ACs, edge cases, dependências, não-goals)
- Spec aprovada para o build do Prompt 04
- Próximo prompt: **Prompt 04 — Build da função `scoring.py`** (AGENT-B against this spec)