# Entry 006 — Análise de feedback_text + Correção crítica do 60.9%

**Data:** 2026-03-20
**Comandos:** 4 queries DuckDB + investigação do cálculo do Agent 02
**Status:** ⚠️ BUG CRÍTICO ENCONTRADO E CORRIGIDO

---

## Motivação

A auditoria (Prompt 007) identificou que o campo `feedback_text` em `churn_events.csv`
nunca havia sido analisado. Ao executar as queries, a análise revelou um bug
metodológico de maior impacto: o número 60.9% que sustentava toda a narrativa
de causa raiz era matematicamente errado.

---

## Output das 4 queries

### Query 1 — Frequência dos textos (non-reactivation events, 75.1% de cobertura)

| feedback | total | % |
|----------|-------|---|
| too expensive | 140 | 34.6% |
| missing features | 140 | 34.6% |
| switched to competitor | 125 | 30.9% |

**Cobertura:** 405 de 539 eventos não-reativação têm feedback_text (75.1%).

**Observação imediata:** Apenas 3 categorias distintas, distribuição quase uniforme.
Em um dataset real, esperaríamos dezenas de variações de texto livre. A uniformidade
perfeita (34.6% / 34.6% / 30.9%) é um artefato sintético.

---

### Query 2 — feedback_text × reason_code

| reason_code | expensive | features | competitor |
|-------------|-----------|----------|------------|
| budget | 39.4% | 28.8% | 31.8% |
| competitor | 34.9% | 36.5% | 28.6% |
| **features** | **37.8%** | **31.1%** | **31.1%** |
| pricing | 34.9% | 31.7% | 33.3% |
| support | 34.7% | 38.7% | 26.7% |
| unknown | 25.0% | 40.6% | 34.4% |

**Descoberta crítica:** `feedback_text` e `reason_code` são **independentes**.
Alguém que escolheu `reason_code=features` escreveu "too expensive" em 37.8%
dos casos — mais do que "missing features" (31.1%). A proporção é ~33/33/33
em todos os grupos. **O campo feedback_text não adiciona informação discriminante
— é ruído sintético.** Nos concentraremos nos dados estruturados (reason_code).

---

### Query 3 — feedback × industry

| industry | top 1 feedback | % |
|----------|---------------|---|
| DevTools | too expensive | 37% |
| FinTech | too expensive | 36% |
| Cybersecurity | missing features | 39% |
| HealthTech | missing features | 40% |
| EdTech | switched to competitor | 40% |

Mesma distribuição uniforme. Sem padrão discriminante por indústria.

---

### Query 4 — MRR perdido por categoria

| feedback | contas | MRR perdido |
|----------|--------|-------------|
| too expensive | 140 | $327,939 |
| missing features | 140 | $320,380 |
| switched to competitor | 125 | $263,137 |

Total coberto pelo feedback_text: ~$911K de MRR. Distribuição proporcional ao volume.

---

## BUG CRÍTICO — O 60.9% era matematicamente errado

### O erro no Agent 02 (`ranking_causas`)

```python
# 02_cross_table_agent.py linha 433 — BUGADO:
feat_reason = (master['reason_code'] == 'features').sum()  # conta todos 500 accounts
causes.append(("Product gap", feat_reason, feat_reason / n_ch, ...))  # divide por 110

# CORRETO deveria ser:
feat_reason = (churners['reason_code'] == 'features').sum()  # só os 110 churned
```

O `master` DataFrame contém LEFT JOIN de `accounts` com `churn_events`. Contas
**retidas** (churn_flag=False) que tinham um evento histórico de cancelamento de
subscrição (mas reativaram) também têm `reason_code` preenchido na master view.

**Resultado:** `(master['reason_code'] == 'features').sum() = 67`
(inclui ~52 contas retidas com reason_code histórico + 15 churned com features)

**Divisor:** `n_ch = 110` churners

**Output bugado:** `67 / 110 = 60.9%`

### Números corretos (verificados via SQL)

| reason_code | Churners (n) | % dos 110 churners |
|-------------|-------------|-------------------|
| sem evento churn registrado | 35 | **31.8%** |
| budget | 17 | 15.5% |
| pricing | 16 | 14.5% |
| features | 15 | **13.6%** |
| support | 14 | 12.7% |
| competitor | 7 | 6.4% |
| unknown | 6 | 5.5% |

### Impacto na narrativa

O número 60.9% aparecia em:
- TL;DR do executive_report.md
- Seção "Causa raiz: product-market fit segmental"
- executive_summary_1page.md
- Todos os entries anteriores (001–005)

**O que muda:**
- A causa "features" NÃO domina — é empatada com budget e pricing (~14–15% cada)
- 31.8% dos churners não têm NENHUM evento registrado em churn_events (silenciosos)
- Budget + pricing combinados = 30% — pricing é provavelmente a maior causa combinada
- **O que NÃO muda:** os achados segmentais (DevTools 31%, event 30.2%) são calculados
  diretamente de `accounts.churn_flag × industry/referral` — sem dependência do reason_code.
  Estas evidências permanecem válidas e são agora a principal evidência da análise.

### A narrativa corrigida

**Antes (errada):** "60.9% dos churners saíram por features — causa única dominante"

**Correta:** "O churn da RavenStack é multicausal e sem causa única dominante.
Budget+pricing concentram ~30% dos casos declarados, features ~14%, support ~13%.
31.8% dos churners não deixaram nenhum registro de motivo. O sinal mais forte
e verificável são os segmentos: DevTools (31% churn) e canal event (30%) churnam
2× mais que Cybersecurity (16%) — OR=2.36–2.53×, independente do reason_code."

---

## Impacto no executive_report.md

**Precisa ser atualizado:**
1. TL;DR — remover "60.9%", substituir por narrative multicausal
2. Seção "Causa raiz" — corrigir números, reposicionar segmental como evidência primária
3. Seção "O que os dados mostram" — tabela de reason_code corrigida
4. executive_summary_1page.md — remover "60.9%"

**O que NÃO muda no relatório:**
- DevTools 31% vs Cybersecurity 16% (OR=2.36×) ← sinal mais robusto
- Canal event 30.2% vs partner 14.6% (OR=2.53×)
- $710K MRR em risco (calcula de multi-signal, não de reason_code)
- As 3 ações prioritárias (baseadas nos segmentos, não no reason_code)
- Seção "O que NÃO fazer" (baseada em hipóteses refutadas)
- Contas específicas (A-e43bf7, etc.)
- AUC=0.34 como descoberta diagnóstica

---

## Parágrafo para inserir no executive_report.md

> **Nota metodológica — razões de saída:**
> A análise dos reason_codes declarados (disponível em 68% dos churners)
> não revela causa única dominante: budget (15.5%), pricing (14.5%),
> features (13.6%) e support (12.7%) estão praticamente empatados.
> 31.8% dos churners saíram sem deixar nenhum registro de motivo.
> Uma análise inicial havia identificado erroneamente "60.9% declaram features"
> devido a um bug de denominador que incluía contas retidas — corrigido nesta versão.
> A evidência mais robusta de causa raiz permanece segmental:
> DevTools churna a 31% vs 16% de Cybersecurity (OR=2.36×),
> independente de qualquer reason_code.

---

## Conclusão

O campo `feedback_text` é ruído sintético (3 categorias uniformes, sem correlação
com reason_code). Ele não acrescenta informação nova.

O bug do 60.9% é a descoberta mais importante desta análise: corrige o principal
claim quantitativo do relatório e reposiciona a evidência segmental (DevTools/event)
como o argumento central, mais robusto porque não depende de dados de reason_code
com bugs de coleta/cálculo.

Esta correção é um exemplo exato de "o que a IA não faria sozinha" — o Agent 02
calculou e reportou 60.9%, os Agents 03–05 repetiram o número sem questionar.
Foi necessário análise manual do código para identificar o erro.
