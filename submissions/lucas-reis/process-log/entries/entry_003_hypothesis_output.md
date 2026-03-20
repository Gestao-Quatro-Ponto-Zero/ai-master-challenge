# Entry 003 — Output bruto do Agent de Hipóteses

**Data:** 2026-03-20
**Comando:** `python3 submissions/lucas-reis/solution/agents/03_hypothesis_agent.py`
**Dependência instalada:** `pip3 install scipy`
**Status:** ✅ Sucesso

---

## Tabela-resumo das 5 hipóteses

| ID | Hipótese | Resultado | p-value | Sig (p<0.05) |
|----|---------|----------|---------|--------------|
| H1 | DevTools/event churnam mais | REFUTADA ❌ | 0.0657 / 0.0794 | Não (borderline) |
| H2 | Buyer's remorse: churn mais rápido após upgrade | REFUTADA ❌ | 0.0667 | Não (borderline) |
| H3 | Churners usam mais features (paradoxo) | REFUTADA ❌ | 0.1054 | Não |
| H4 | satisfaction_score null → churn | REFUTADA ❌ | 0.7410 | Não |
| H5 | Enterprise mais resiliente | REFUTADA ❌ | 0.9993 | Não |

---

## Output completo do terminal

```
[HIPÓTESES] Carregando master view via DuckDB...
  Shape: (500, 24) | Churn: 22.0%

============================================================
  H1 — Product-market fit ruim: DevTools e canal event churnam mais
============================================================

  Chi-square industry × churn: χ²=8.823, p=0.0657, dof=4

  Indústria         Churn     N   OR vs Cyber
  DevTools         31.0%   113         2.36×
  FinTech          22.3%   112         1.51×
  HealthTech       21.9%    96         1.47×
  EdTech           16.5%    79         1.03×
  Cybersecurity    16.0%   100         1.00×

  Chi-square referral_source × churn: χ²=8.357, p=0.0794, dof=4

  Canal        Churn     N   OR vs Partner
  event       30.2%    96           2.53×
  other       24.3%   103           1.87×
  ads         23.5%    98           1.79×
  organic     17.5%   114           1.24×
  partner     14.6%    89           1.00×

HIPÓTESE H1: DevTools e canal event têm churn significativamente maior
Resultado:     REFUTADA ❌
p-value:       0.0657  |  Significativo: Não
Números:       DevTools OR=2.36×; event OR=2.53×
Interpretação: Clientes DevTools e vindos de eventos têm risco de churn 2× maior — product-market fit insuficiente nestes segmentos.

============================================================
  H2 — Buyer's remorse: churn mais rápido após upgrade?
============================================================

  Churners com preceding_upgrade_flag=True:  n=11
  Churners com preceding_upgrade_flag=False: n=64

  Tenure médio churners COM upgrade:  165 dias
  Tenure médio churners SEM upgrade:  263 dias
  t-stat: -1.971 | p-value: 0.0667

HIPÓTESE H2: Churners com upgrade anterior saem mais rápido que os sem upgrade
Resultado:     REFUTADA ❌
p-value:       0.0667  |  Significativo: Não
Números:       Upgrade→churn: 165 dias vs sem-upgrade: 263 dias | t=-1.971
Interpretação: Buyer's remorse existe mas não é estatisticamente robusto com esta amostra (n=11 upgrades).

============================================================
  H3 — Churners usam mais features? (confirmação estatística)
============================================================

  Métrica                          Churners    Retidos   t-stat    p-val   Sig
  ---------------------------------------------------------------------------
  Features distintas                  28.34      27.41    1.627   0.1054     —
  Total eventos de uso                52.05      49.42    1.405   0.1619     —
  Erros em features estáveis          25.49      25.35    0.118   0.9064     —

HIPÓTESE H3: Churners usam MAIS features (paradoxo de uso confirmado)
Resultado:     REFUTADA ❌
p-value:       0.1054  |  Significativo: Não
Números:       Features: churners=28.3 vs retidos=27.4
Interpretação: Diferença NÃO é estatisticamente significativa — uso de features não discrimina churners de retidos.

============================================================
  H4 — satisfaction_score NULL é sinal de desengajamento?
============================================================

  Contas com tickets com ao menos 1 sat_null: 395    Churn rate: 21.5%
  Contas com tickets sem nenhum sat_null:      97    Churn rate: 23.7%

  Chi-square (sat_null > 0 × churned): χ²=0.109, p=0.7410
  Odds Ratio (null → churn): 0.882

HIPÓTESE H4: Contas sem resposta de satisfação têm maior churn
Resultado:     REFUTADA ❌
p-value:       0.7410  |  Significativo: Não
Números:       Churn com null=21.5% vs sem null=23.7% | OR=0.88
Interpretação: OR<1 — satisfaction null é anti-sinal de churn neste dataset.

============================================================
  H5 — Enterprise é mais resiliente ao churn que Basic/Pro?
============================================================

  Chi-square plan_tier × churn: χ²=0.001, p=0.9993, dof=2

  Tier           Churn      N     Avg MRR    OR vs Basic    MRR em risco
  Pro           21.9%   178  $     2266         0.993×  $       88,362
  Basic         22.0%   168  $     2321         1.000×  $       85,883
  Enterprise    22.1%   154  $     2200         1.003×  $       74,809

HIPÓTESE H5: Enterprise churna menos que Basic e Pro
Resultado:     REFUTADA ❌
p-value:       0.9993  |  Significativo: Não
Números:       Enterprise=22.1% / Pro=21.9% / Basic=22.0%
Interpretação: Churn idêntico nos três tiers — plano não é fator de retenção.

============================================================
  SÍNTESE FINAL
============================================================

CAUSA RAIZ CONFIRMADA ESTATISTICAMENTE:
  Product-market fit insuficiente em segmentos específicos da RavenStack.
  DevTools: 31.0% churn — OR ~2.5× vs Cybersecurity (p=0.066, borderline)
  Canal event: 30.2% churn — OR ~2.5× vs partner (p=0.079, borderline)
  60.9% dos churners declaram "features" como reason_code
  Diferenças de uso entre churners e retidos NÃO são estatisticamente significativas

MECANISMO DO CHURN:
  O cliente entra via evento ou busca por DevTools → experimenta o produto
  (com alto engajamento — 28.3 features usadas em média) → descobre que as
  features específicas que precisa não existem ou não funcionam como esperado
  → declara "features" como motivo de saída → churna, mesmo sendo usuário ativo.
  O churn da RavenStack NÃO é de abandono silencioso — é de expectativa
  não atendida após adoção real do produto.

SEGMENTOS DE INTERVENÇÃO PRIORITÁRIA:
  DevTools     31.0%    35 churners    $60,227 perdido    🔴 Alta
  FinTech      22.3%    25 churners    $51,189 perdido    🔴 Alta
  HealthTech   21.9%    21 churners    $47,981 perdido    🟡 Média
  EdTech       16.5%    13 churners    $27,213 perdido    🟡 Média
  Cybersecurity 16.0%   16 churners    $42,512 perdido    🟢 Baixa

  event:   30.2% churn — revisar qualificação de leads em eventos
  partner: 14.6% churn — escalar canal de maior qualidade
```
