"""
03 — Análise de Causa Raiz
===========================
Aqui é onde o diagnóstico real acontece. As partes 01 e 02 foram preparação.

Pergunta central: "O que está causando o churn de verdade?"

Hipóteses a testar:
1. É um segmento específico? (indústria, país, canal)
2. É um tier de MRR? (mid-market squeeze?)
3. O uso realmente cresceu como o CEO disse?
4. Tickets de suporte predizem churn?
5. Há padrão temporal? (aceleração?)

Spoiler: as médias mascaram tudo. O problema está nos segmentos.
"""

import pandas as pd
import numpy as np

master = pd.read_csv('data/master_churn_analysis.csv')
churn = pd.read_csv('data/ravenstack_churn_events.csv')
usage = pd.read_csv('data/ravenstack_feature_usage.csv')
subs = pd.read_csv('data/ravenstack_subscriptions.csv')
tickets = pd.read_csv('data/ravenstack_support_tickets.csv')

churn['churn_date'] = pd.to_datetime(churn['churn_date'])
tickets['submitted_at'] = pd.to_datetime(tickets['submitted_at'])

# ══════════════════════════════════════════════════════════════════════
# FINDING 1: CHURN ESTÁ ACELERANDO EXPONENCIALMENTE
# ══════════════════════════════════════════════════════════════════════
# Isso é a coisa mais importante que o CEO precisa ver.
# Não é só "churn subiu" — é uma curva exponencial.

print("FINDING 1: ACELERAÇÃO DO CHURN")
print("-" * 50)

churn['quarter'] = churn['churn_date'].dt.to_period('Q')
quarterly = churn.groupby('quarter').agg(
    events=('churn_event_id', 'count'),
    refunds=('refund_amount_usd', 'sum')
)

for q, row in quarterly.iterrows():
    print(f"  {q}: {row.events:>3} eventos | ${row.refunds:>8,.0f} refunds")

print("""
  Q1/2023:   6 eventos
  Q4/2024: 251 eventos  → 42x em 2 anos
  Isso não é ruído — é uma crise acelerando.
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 2: DEVTOOLS SANGRA MAIS QUE TODOS
# ══════════════════════════════════════════════════════════════════════

print("FINDING 2: DEVTOOLS É O SEGMENTO QUE SANGRA")
print("-" * 50)

by_industry = master.groupby('industry').agg(
    contas=('account_id', 'count'),
    churn_rate=('churn_flag', 'mean'),
    mrr_perdido=('mrr_at_risk', 'sum')
).sort_values('churn_rate', ascending=False)

for ind, row in by_industry.iterrows():
    print(f"  {ind:15s} | {row.contas:>3} contas | churn: {row.churn_rate:.0%} | MRR perdido: ${row.mrr_perdido:>8,.0f}")

print("""
  DevTools (31%) tem quase o dobro de EdTech/Cybersecurity (16%).
  Mas atenção: FinTech e HealthTech também estão acima de 20%.
  O problema não é só DevTools — é que DevTools é o pior caso.
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 3: CANAL DE AQUISIÇÃO IMPORTA MAIS QUE PLANO
# ══════════════════════════════════════════════════════════════════════

print("FINDING 3: EVENTOS TRAZEM CLIENTES QUE NÃO FICAM")
print("-" * 50)

by_ref = master.groupby('referral_source').agg(
    contas=('account_id', 'count'),
    churn_rate=('churn_flag', 'mean'),
    mrr_perdido=('mrr_at_risk', 'sum')
).sort_values('churn_rate', ascending=False)

for ref, row in by_ref.iterrows():
    print(f"  {ref:15s} | {row.contas:>3} contas | churn: {row.churn_rate:.0%} | MRR perdido: ${row.mrr_perdido:>8,.0f}")

by_plan = master.groupby('plan_tier').agg(
    churn_rate=('churn_flag', 'mean')
)
print(f"\n  Enquanto isso, churn por PLANO:")
for plan, row in by_plan.iterrows():
    print(f"    {plan:15s} | churn: {row.churn_rate:.0%}")

print("""
  Eventos: 30% churn. Partners: 15%. O dobro.
  Plano (Basic/Pro/Enterprise): ~22% uniforme.

  CONCLUSÃO: o canal de aquisição é um driver muito mais forte
  que o plano. A empresa está investindo em eventos que trazem
  clientes de baixa qualidade.
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 4: MID-MARKET SQUEEZE
# ══════════════════════════════════════════════════════════════════════

print("FINDING 4: MID-MARKET ($1K-$2.5K MRR) É O TIER MAIS VULNERÁVEL")
print("-" * 50)

master['mrr_tier'] = pd.cut(master['avg_mrr'],
    bins=[0, 500, 1000, 2500, 5000, 40000],
    labels=['<$500', '$500-1K', '$1K-2.5K', '$2.5K-5K', '$5K+'])

by_mrr = master.groupby('mrr_tier', observed=True).agg(
    contas=('account_id', 'count'),
    churn_rate=('churn_flag', 'mean'),
    mrr_perdido=('mrr_at_risk', 'sum')
)

for tier, row in by_mrr.iterrows():
    print(f"  {str(tier):10s} | {row.contas:>3} contas | churn: {row.churn_rate:.0%} | MRR perdido: ${row.mrr_perdido:>8,.0f}")

# Cross: reason code x mrr tier
churn_with_mrr = churn.merge(master[['account_id', 'mrr_tier']], on='account_id')
ct = pd.crosstab(churn_with_mrr.mrr_tier, churn_with_mrr.reason_code)
print(f"\n  Razoes de churn por MRR tier:")
print(ct.to_string())

print("""
  $1K-$2.5K domina TODAS as razoes de churn.
  Sao 275 contas (55% da base) com 26% de churn.
  "Grandes demais para self-service, pequenas demais para enterprise."
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 5: CEO ESTÁ ERRADO — USO NÃO CRESCEU
# ══════════════════════════════════════════════════════════════════════
# O CEO disse: "o time de produto diz que o uso da plataforma cresceu"
# Vamos verificar com dados.

print("FINDING 5: VALIDANDO CLAIM DO CEO")
print("-" * 50)

sub_map = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_acc = usage.merge(sub_map, on='subscription_id')
usage_acc = usage_acc.merge(master[['account_id', 'churn_flag']], on='account_id')
usage_acc['usage_date'] = pd.to_datetime(usage['usage_date'])
usage_acc['half'] = np.where(usage_acc.usage_date < '2024-07-01', 'H1_2024', 'H2_2024')

usage_trend = usage_acc.groupby(['churn_flag', 'half']).agg(
    avg_count=('usage_count', 'mean'),
    avg_duration=('usage_duration_secs', 'mean')
)
print(usage_trend.to_string())

print("""
  Retidos H1 vs H2 2024:
    usage_count: 10.02 -> 9.99  (CAIU)
    duration:    3061  -> 2984   (CAIU 2.5%)

  Churned H1 vs H2 2024:
    usage_count: 10.02 -> 10.04 (flat)
    duration:    3035  -> 3063   (flat)

  VEREDICTO: O CEO esta errado. O uso NAO cresceu.
  Na verdade, CAIU ligeiramente para os retidos.
  O time de Produto pode estar olhando uso agregado (que
  sobe com mais contas) em vez de uso per-account.
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 6: SUPORTE NÃO DIFERENCIA CHURNED DE RETIDOS
# ══════════════════════════════════════════════════════════════════════

print("FINDING 6: SUPORTE — POR QUE CS DIZ QUE 'TA OK'")
print("-" * 50)

tickets_with_churn = tickets.merge(master[['account_id', 'churn_flag']], on='account_id')
support = tickets_with_churn.groupby('churn_flag').agg(
    resolution_h=('resolution_time_hours', 'mean'),
    first_resp_min=('first_response_time_minutes', 'mean'),
    satisfaction=('satisfaction_score', 'mean'),
    escalation_pct=('escalation_flag', 'mean'),
    satisfaction_null=('satisfaction_score', lambda x: x.isnull().mean())
)
print(support.to_string())

print("""
  Satisfacao churned (4.01) > retidos (3.97). Contraintuitivo?
  Nao necessariamente. Possibilidades:

  1. Clientes que vao embora por budget/competitor estao satisfeitos
     com o suporte — o problema nao e atendimento, e pricing/features.

  2. 40% dos scores sao null — os insatisfeitos podem simplesmente
     nao responder a pesquisa (non-response bias).

  O CS esta tecnicamente certo: a satisfacao TA ok.
  Mas isso nao significa que nao ha problema de churn.
  Sao problemas DIFERENTES.
""")

# ══════════════════════════════════════════════════════════════════════
# FINDING 7: FEEDBACK DE TEXTO — SIMPLES MAS DIRETO
# ══════════════════════════════════════════════════════════════════════

print("FINDING 7: O QUE OS CLIENTES DIZEM AO SAIR")
print("-" * 50)

feedback = churn[churn.feedback_text.notna()]['feedback_text']
print(f"  Feedbacks preenchidos: {len(feedback)}/{len(churn)} ({len(feedback)/len(churn):.0%})")
for text, cnt in feedback.value_counts().items():
    pct = cnt / len(feedback) * 100
    print(f"  [{cnt:>3}x | {pct:>4.0f}%] {text}")

print("""
  3 categorias claras:
  - "too expensive" (36%) → pricing/budget problem
  - "missing features" (34%) → product gap
  - "switched to competitor" (30%) → competitive pressure

  Note: 25% nao deixaram feedback (148 nulls).
  A distribuicao e uniforme — nao ha uma causa dominante unica.
  Isso reforça que o churn e multifatorial e precisa de
  intervencoes diferentes por segmento.
""")

# ══════════════════════════════════════════════════════════════════════
# SÍNTESE: CAUSA RAIZ
# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("SINTESE: POR QUE O CHURN SUBIU?")
print("=" * 60)
print("""
1. O churn esta ACELERANDO (42x em 2 anos) — nao e flutuacao,
   e uma tendencia exponencial que precisa de intervencao urgente.

2. DevTools e o segmento mais afetado (31%) mas o problema e
   amplificado pelo canal de aquisicao: clientes de EVENTOS
   churnam 2x mais que de PARTNERS.

3. O mid-market ($1K-$2.5K MRR) concentra 55% da base e tem
   a maior taxa de churn (26%). Essas contas caem no gap
   entre self-service e enterprise.

4. O CEO esta vendo metricas erradas:
   - "Uso cresceu" — FALSO (caiu ligeiramente per-account)
   - "Satisfacao ta ok" — VERDADE mas irrelevante (o problema
     nao e suporte, e pricing/features/competitive pressure)
   - "Churn e 22%" — INCOMPLETO (70% das contas ja churnearam
     pelo menos uma vez, 175 churnearam mais de uma vez)

5. O feedback dos clientes confirma: 36% saem por preco,
   34% por features faltando, 30% por competidor.
   Nao ha uma bala de prata — precisa de acoes diferenciadas.
""")
