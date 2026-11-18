"""Zumbis por escritorio x mes de inicio; a conta nos deals abertos e informativa?"""
from common import *
from scipy import stats
d = load(); d["zombie"] = (~d.closed).astype(int)
e = d[d.engage_date.notna()]; em = e.engage_date.dt.to_period("M")
print("taxa de nunca-fechados por escritorio x mes de inicio"); print(e.pivot_table(index=em, columns="regional_office", values="zombie", aggfunc="mean").round(3))
print("n iniciados"); print(e.pivot_table(index=em, columns="regional_office", values="zombie", aggfunc="size"))
print("n zumbis"); print(e.pivot_table(index=em, columns="regional_office", values="zombie", aggfunc="sum"))
# os 3 vendedores sem nenhum deal aberto
print(d[d.sales_agent.isin(["Donn Cantrell", "Garret Kinder", "Reed Clapper"])].groupby(["sales_agent", "regional_office", "manager"]).deal_stage.value_counts().unstack())
# vendedores no cadastro sem nenhum deal
t = pd.read_csv(scoring.DATA_DIR / "sales_teams.csv"); print("sem deals:", t[~t.sales_agent.isin(d.sales_agent)].to_string())
# conta nos abertos: par vendedor x conta ja visto, por coorte de inicio e escritorio
cl = d[d.closed]; pairs = set(zip(cl.sales_agent, cl.account))
terr = cl.groupby("sales_agent").account.nunique()
op = d[d.deal_stage.isin(["Engaging", "Prospecting"])].copy()
op["coorte"] = np.where(op.deal_stage == "Prospecting", "prospect", np.where(op.engage_date >= "2017-10-01", "Q4", np.where(op.engage_date >= "2017-07-01", "Q3", "ate Q2")))
op["par_visto"] = [(a, c) in pairs for a, c in zip(op.sales_agent, op.account)]
op["sem_conta"] = op.account.isna()
print(op.groupby("coorte").agg(n=("sem_conta", "size"), sem_conta=("sem_conta", "mean")).round(3))
print(op[~op.sem_conta].groupby("coorte").agg(n=("par_visto", "size"), par_visto=("par_visto", "mean")).round(3), "| esperado ao acaso:", round(terr.mean() / 85, 3))
print(op.groupby(["regional_office"]).agg(n=("sem_conta", "size"), sem_conta=("sem_conta", "mean")).round(3))
# quanto dos abertos Q4 deveria fechar, pelos analogos? deals iniciados no trimestre, abertos no ultimo dia do trimestre
for q_end, q_start in [("2017-06-30", "2017-04-01"), ("2017-09-30", "2017-07-01"), ("2017-03-31", "2017-01-01")]:
    s = scoring.open_at(d, pd.Timestamp(q_end)); s = s[s.engage_date >= q_start]
    print(q_end, "abertos iniciados no trimestre:", len(s), "fecham depois:", round(s.close_date.notna().mean(), 3), "ganhos:", round((s.deal_stage == "Won").mean(), 3),
          "| por escritorio fecham:", s.close_date.notna().groupby(s.regional_office).mean().round(2).to_dict())
q4 = op[op.coorte == "Q4"]
print("Q4 abertos hoje:", len(q4), q4.groupby("regional_office").size().to_dict())
# teste: sem_conta ~ coorte, vendedor, escritorio, produto (abertos Engaging)
en = op[op.deal_stage == "Engaging"]
for c in ["coorte", "sales_agent", "regional_office", "manager", "product"]:
    tb = pd.crosstab(en[c], en.sem_conta); ch, p, _, _ = stats.chi2_contingency(tb); print("sem_conta x", c, "chi2=%.1f p=%.3f" % (ch, p))
est = en[en.engage_date < "2017-10-01"]
for c in ["sales_agent", "regional_office", "manager", "product"]:
    tb = pd.crosstab(est[c], est.sem_conta); ch, p, _, _ = stats.chi2_contingency(tb); print("[estourados] sem_conta x", c, "chi2=%.1f p=%.3f n=%d" % (ch, p, len(est)))
print("idade mediana estourados: sem conta", (TODAY - est[est.sem_conta].engage_date).dt.days.median(), "com conta", (TODAY - est[~est.sem_conta].engage_date).dt.days.median(),
      stats.mannwhitneyu((TODAY - est[est.sem_conta].engage_date).dt.days, (TODAY - est[~est.sem_conta].engage_date).dt.days))
# distribuicao de contas nos abertos e uniforme?
ac = op.account.dropna().value_counts(); print("contas nos abertos: uniforme? chi2", stats.chisquare(ac.reindex(pd.read_csv(scoring.DATA_DIR / "accounts.csv").account, fill_value=0)))
acf = cl.account.value_counts(); print("contas nos fechados: uniforme? chi2", stats.chisquare(acf))
