"""
01 — Exploração Inicial dos Dados: RavenStack
==============================================
Primeiro passo: entender a estrutura ANTES de analisar.
O CEO disse que "churn subiu" mas CS e Produto dizem que está tudo ok.
Preciso entender os dados pra saber quem está certo.

Decisão: Começar validando integridade das FKs entre tabelas.
Se os joins quebrarem, toda a análise downstream vai ser comprometida.
"""

import pandas as pd

# ── Carregando os 5 datasets ──────────────────────────────────────────
accounts = pd.read_csv('data/ravenstack_accounts.csv')
subs = pd.read_csv('data/ravenstack_subscriptions.csv')
usage = pd.read_csv('data/ravenstack_feature_usage.csv')
tickets = pd.read_csv('data/ravenstack_support_tickets.csv')
churn = pd.read_csv('data/ravenstack_churn_events.csv')

print("=" * 60)
print("SHAPES DOS DATASETS")
print("=" * 60)
for name, df in [('accounts', accounts), ('subscriptions', subs),
                  ('feature_usage', usage), ('support_tickets', tickets),
                  ('churn_events', churn)]:
    nulls = df.isnull().sum().sum()
    print(f"  {name:20s} → {df.shape[0]:>6,} rows x {df.shape[1]:>2} cols | nulls: {nulls}")

# ── Validação de integridade referencial ──────────────────────────────
# Isso é CRÍTICO — se tiver orphans, os merges vão perder dados
print("\n" + "=" * 60)
print("INTEGRIDADE REFERENCIAL")
print("=" * 60)

acc_ids = set(accounts.account_id)
sub_ids = set(subs.subscription_id)

checks = [
    ("subscriptions → accounts", subs.account_id.isin(acc_ids).all()),
    ("churn_events → accounts", churn.account_id.isin(acc_ids).all()),
    ("support_tickets → accounts", tickets.account_id.isin(acc_ids).all()),
    ("feature_usage → subscriptions", usage.subscription_id.isin(sub_ids).all()),
]
for label, ok in checks:
    status = "✓ OK" if ok else "✗ FALHOU"
    print(f"  {label:40s} {status}")

# ── Primeira descoberta importante ────────────────────────────────────
# Comparando churn_flag em accounts vs churn_events
# Minha hipótese inicial: deveriam bater 1:1
print("\n" + "=" * 60)
print("DESCOBERTA: GAP ENTRE CHURN_FLAG E CHURN_EVENTS")
print("=" * 60)

acc_churned = set(accounts[accounts.churn_flag].account_id)
event_accounts = set(churn.account_id)
overlap = acc_churned & event_accounts

print(f"  Contas flagged como churned:     {len(acc_churned):>4}")
print(f"  Contas com eventos de churn:     {len(event_accounts):>4}")
print(f"  Overlap (em ambos):              {len(overlap):>4}")
print(f"  Flagged mas sem evento:          {len(acc_churned - event_accounts):>4}")
print(f"  Evento mas NÃO flagged:          {len(event_accounts - acc_churned):>4}")

# Isso é ENORME. 277 contas churnearam E VOLTARAM (reativaram).
# O CEO vê 22% de churn. O real é que 70% das contas já passaram por churn.
# Esse gap explica a confusão: o churn_flag mostra o estado ATUAL,
# mas esconde todo o histórico de reincidência.

multi_churn = (churn.groupby('account_id').size() > 1).sum()
print(f"\n  Contas com MÚLTIPLOS churns:     {multi_churn:>4}")
print(f"  → Churn recorrente é um problema que ninguém está medindo")

# ── Distribuições básicas ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("DISTRIBUIÇÕES")
print("=" * 60)

print(f"\n  Churn rate (flag): {accounts.churn_flag.mean():.1%}")
print(f"\n  Indústrias:")
for ind, cnt in accounts.industry.value_counts().items():
    print(f"    {ind:20s} {cnt:>3} contas")

print(f"\n  Planos:")
for plan, cnt in accounts.plan_tier.value_counts().items():
    print(f"    {plan:20s} {cnt:>3} contas")

print(f"\n  Canais de aquisição:")
for ref, cnt in accounts.referral_source.value_counts().items():
    print(f"    {ref:20s} {cnt:>3} contas")

print(f"\n  Razões de churn:")
for reason, cnt in churn.reason_code.value_counts().items():
    print(f"    {reason:20s} {cnt:>3} eventos")

# ── Observações para o próximo passo ──────────────────────────────────
print("\n" + "=" * 60)
print("NOTAS PARA PRÓXIMO PASSO")
print("=" * 60)
print("""
1. O gap entre churn_flag e churn_events é o insight mais importante até agora.
   O CEO está olhando a métrica errada.

2. As razões de churn são bem distribuídas (features, support, budget, unknown,
   competitor, pricing) — não tem uma causa dominante óbvia.
   Preciso cruzar com segmentos pra ver se muda.

3. Tickets de suporte têm 41% de satisfaction_score nulo.
   Preciso decidir: dropar ou imputar. Vou investigar se são missing at random.

4. Próximo passo: criar master table com joins e features derivadas.
   Decisão: agregar por account_id (unidade de análise do CEO).
""")
