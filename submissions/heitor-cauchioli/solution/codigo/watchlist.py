"""
RavenStack - Watchlist diária de risco de churn (janela de 60 dias)
Uso:  python3 watchlist.py [pasta_com_csvs] [data_de_corte AAAA-MM-DD]
Gera: watchlist_contas.csv (uma linha por conta, ordenada por perda esperada)

Lógica (validada nos dados de 2023-2024):
- Toda assinatura nos primeiros 60 dias de vida tem risco de churn ~2,4x maior
  que uma assinatura madura (H2-2024: 3,13% vs 1,32% do MRR por mês).
- A perda esperada em 90 dias de cada conta = soma, por assinatura ativa, de
  MRR x probabilidade de cancelar em 90 dias, usando a taxa da fase de vida.
- As taxas são recalculadas a cada execução com os últimos 6 meses de dados,
  então o modelo se ajusta se o onboarding melhorar (ou piorar).
"""
import sys, pandas as pd, numpy as np

pasta = sys.argv[1] if len(sys.argv) > 1 else "."
s = pd.read_csv(f"{pasta}/ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
a = pd.read_csv(f"{pasta}/ravenstack_accounts.csv", parse_dates=["signup_date"])
t = pd.read_csv(f"{pasta}/ravenstack_support_tickets.csv", parse_dates=["submitted_at"])
u = pd.read_csv(f"{pasta}/ravenstack_feature_usage.csv", parse_dates=["usage_date"])
CUT = pd.Timestamp(sys.argv[2]) if len(sys.argv) > 2 else s.start_date.max()
JANELA = 60

# 1) Calibra taxas mensais de churn (ponderadas por MRR) nos últimos 6 meses
def taxas(cut):
    novo = [0, 0]; maduro = [0, 0]
    for m in pd.period_range(cut - pd.DateOffset(months=6), cut - pd.DateOffset(months=1), freq="M"):
        st, en = m.start_time, m.end_time
        act = s[(s.start_date < st) & (s.end_date.isna() | (s.end_date >= st))]
        is_new = (st - act.start_date).dt.days <= JANELA
        ch = act.end_date <= en
        for alvo, msk in ((novo, is_new), (maduro, ~is_new)):
            alvo[0] += (act.mrr_amount * ch)[msk].sum(); alvo[1] += act.mrr_amount[msk].sum()
    return novo[0] / novo[1], maduro[0] / maduro[1]

h_novo, h_maduro = taxas(CUT)

# 2) Assinaturas ativas na data de corte
act = s[(s.start_date <= CUT) & (s.end_date.isna() | (s.end_date > CUT))].copy()
act["idade_dias"] = (CUT - act.start_date).dt.days
act["na_janela"] = act.idade_dias <= JANELA
act["primeira_da_conta"] = act.subscription_id.isin(
    s.sort_values("start_date").groupby("account_id").head(1).subscription_id)
p90_novo = 1 - (1 - h_novo) ** 2 * (1 - h_maduro)          # ~2 meses na janela + 1 maduro
p90_maduro = 1 - (1 - h_maduro) ** 3
act["perda_esperada_90d"] = act.mrr_amount * np.where(act.na_janela, p90_novo, p90_maduro)
act["mrr_janela"] = act.mrr_amount * act.na_janela

A = act.groupby("account_id").agg(
    mrr_ativo=("mrr_amount", "sum"),
    assinaturas_ativas=("subscription_id", "size"),
    mrr_na_janela=("mrr_janela", "sum"),
    assinaturas_na_janela=("na_janela", "sum"),
    assinatura_mais_nova_dias=("idade_dias", "min"),
    perda_esperada_90d=("perda_esperada_90d", "sum"),
)

# 3) Contexto para o CSM (não entra no score - não tem poder preditivo comprovado)
sig = a.set_index("account_id").signup_date
s["vida"] = (s.end_date - s.start_date).dt.days
precoce = s[s.churn_flag & (s.vida <= JANELA) & (s.end_date > CUT - pd.Timedelta(days=180)) & (s.end_date <= CUT)]
A["cancelamentos_precoces_180d"] = precoce.groupby("account_id").size().reindex(A.index).fillna(0).astype(int)
tv = t[(t.submitted_at >= t.account_id.map(sig)) & (t.submitted_at <= CUT) & (t.submitted_at > CUT - pd.Timedelta(days=90))]
A["tickets_90d"] = tv.groupby("account_id").size().reindex(A.index).fillna(0).astype(int)
uu = u.merge(s[["subscription_id", "account_id"]], on="subscription_id")
uu = uu[(uu.usage_date >= uu.account_id.map(sig)) & (uu.usage_date <= CUT) & (uu.usage_date > CUT - pd.Timedelta(days=90))]
seats = act.groupby("account_id").seats.sum()
A["uso_por_assento_90d"] = (uu.groupby("account_id").usage_count.sum().reindex(A.index).fillna(0) / seats).round(2)

A = A.join(a.set_index("account_id")[["account_name", "industry", "country", "plan_tier"]])
A["perda_esperada_90d"] = A.perda_esperada_90d.round(0)
A = A.sort_values("perda_esperada_90d", ascending=False)

# 4) Prioridade: P1 = maior exposição na janela (top 10% de MRR na janela), P2 = alguma assinatura na janela, P3 = base madura
corte_p1 = A.loc[A.mrr_na_janela > 0, "mrr_na_janela"].quantile(0.80)
A["prioridade"] = np.select(
    [A.mrr_na_janela >= corte_p1, A.mrr_na_janela > 0], ["P1", "P2"], "P3")
A["acao_sugerida"] = np.select(
    [A.prioridade == "P1", A.prioridade == "P2"],
    ["Ligação do CSM em 48h + plano de adoção das novas assinaturas",
     "Sequência de onboarding (e-mail + webinar) e checagem no dia 30"],
    "Rotina normal de CS")
cols = ["account_name", "industry", "country", "plan_tier", "prioridade", "mrr_ativo", "mrr_na_janela",
        "assinaturas_na_janela", "assinatura_mais_nova_dias", "perda_esperada_90d",
        "cancelamentos_precoces_180d", "tickets_90d", "uso_por_assento_90d", "acao_sugerida"]
A[cols].to_csv("watchlist_contas.csv")
print(f"Corte: {CUT.date()} | taxa mensal janela {h_novo:.2%} vs madura {h_maduro:.2%}")
print(A.prioridade.value_counts().to_string())
print(f"Perda esperada 90d total: ${A.perda_esperada_90d.sum():,.0f} | P1: ${A[A.prioridade=='P1'].perda_esperada_90d.sum():,.0f}")
