"""10 — Testa a hipótese do Ronaldo: churn da Alemanha ligado à idade das contas (e a França seguiria o mesmo caminho) + barreira de idioma no suporte. Uso: python -I 10_pais_maturidade.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, ce, tk = r("accounts"), r("subscriptions"), r("churn_events"), r("support_tickets")
REF = pd.Timestamp("2024-12-31"); a["signup"] = pd.to_datetime(a.signup_date)
last_ev = pd.to_datetime(ce.churn_date).groupby(ce.account_id).max()
A = a.set_index("account_id"); A["idade_ref"] = (REF - A.signup).dt.days / 30.44
A["fim"] = np.where(A.churn_flag, A.index.map(last_ev), REF); A["fim"] = pd.to_datetime(A.fim).fillna(REF)
A["vida"] = (A.fim - A.signup).dt.days / 30.44   # meses de exposição (até o churn ou até 31/12/2024)
print(f"contas canceladas sem evento (vida = até a data de referência): {(A.churn_flag & A.index.map(last_ev).isna()).sum()}")
print(f"eventos de churn ANTES do signup: {(pd.to_datetime(ce.churn_date).values < ce.account_id.map(A.signup).values).sum()} de {len(ce)}")
print("\n=== por país: contas, canceladas, idade média (31/12/2024), churn por 100 contas-mês de exposição")
t = A.groupby("country").agg(contas=("churn_flag","size"), canc=("churn_flag","sum"), idade=("idade_ref","mean"), expo=("vida","sum"))
t["churn%"] = 100*t.canc/t.contas; t["por_100_contas_mes"] = 100*t.canc/t.expo
t["IC95"] = [f"{100*stats.binomtest(int(c),int(n)).proportion_ci()[0]:.0f}–{100*stats.binomtest(int(c),int(n)).proportion_ci()[1]:.0f}%" for c, n in zip(t.canc, t.contas)]
print(t.round(2).to_string())
de = A.country.eq("DE"); print(f"Fisher DE x resto: p={stats.fisher_exact(pd.crosstab(de, A.churn_flag).values)[1]:.3f}")
print(f"Spearman idade média x churn% entre os 7 países: rho={stats.spearmanr(t.idade, t['churn%'])[0]:.2f}, p={stats.spearmanr(t.idade, t['churn%'])[1]:.2f}")
print("\n=== idade x churn na base inteira (500 contas)")
A["faixa"] = pd.cut(A.idade_ref, [0,6,12,18,24,99], labels=["0–6","7–12","13–18","19–24","25+"])
g = A.groupby("faixa", observed=True).agg(contas=("churn_flag","size"), canc=("churn_flag","sum"), expo=("vida","sum"))
g["churn%"] = (100*g.canc/g.contas).round(1); g["por_100_contas_mes"] = (100*g.canc/g.expo).round(2); print(g.to_string())
print(f"  AUC idade -> churn_flag: {stats.mannwhitneyu(A[A.churn_flag].idade_ref, A[~A.churn_flag].idade_ref)[0]/(A.churn_flag.sum()*(~A.churn_flag).sum()):.3f}")
import statsmodels.formula.api as smf
A["DE"] = de.astype(int); A["cf"] = A.churn_flag.astype(int)
m = smf.logit("cf ~ idade_ref + DE", A).fit(disp=0); print("  logit churn ~ idade + DE:\n", m.summary2().tables[1][["Coef.","P>|z|"]].round(3).to_string())
print("\n=== França por faixa (n pequeno)")
fr = A[A.country=="FR"]; print(fr.groupby("faixa", observed=True).churn_flag.agg(["size","sum"]).to_string())
c, n = int(fr[fr.faixa=="13–18"].churn_flag.sum()), int((fr.faixa=="13–18").sum())
if n: lo, hi = stats.binomtest(c, n).proportion_ci(); print(f"  13–18 meses: {c}/{n}, IC95% {lo:.0%}–{hi:.0%}")
rest = A[(A.country!="FR") & (A.faixa=="13–18")]; print(f"  13–18 meses, outros países: {rest.churn_flag.sum()}/{len(rest)} ({rest.churn_flag.mean():.0%}) | Fisher FR x resto p={stats.fisher_exact([[c,n-c],[rest.churn_flag.sum(), len(rest)-rest.churn_flag.sum()]])[1]:.2f}")
print("\n=== renovação anual: o churn cai perto dos 12 meses de vida?")
paid = s[~s.is_trial].copy(); paid["start"] = pd.to_datetime(paid.start_date)
lastpaid = paid.sort_values("start").groupby("account_id").last(); A["freq"] = lastpaid.billing_frequency.reindex(A.index)
canc = A[A.churn_flag & A.index.map(last_ev).notna()]
for f_, gg in canc.groupby("freq"):
    print(f"  {f_}: {len(gg)} canceladas, vida no churn mediana {gg.vida.median():.1f} m; entre 11 e 13 meses: {gg.vida.between(11,13).mean():.0%}")
print(f"  esperado se uniforme em 0–24 meses: {2/24:.0%}")
ev = ce.merge(paid[["subscription_id","account_id","start","end_date","billing_frequency"]], on="account_id")
ev["cd"] = pd.to_datetime(ev.churn_date); ev["end"] = pd.to_datetime(ev.end_date)
ann = ev[(ev.billing_frequency=="annual") & ev.end.notna()]
near = ann.assign(d=(ann.cd-ann.end).dt.days.abs()).groupby("churn_event_id").d.min()
print(f"  eventos de contas com assinatura anual encerrada: {len(near)}; com fim de assinatura anual a ±30 dias: {(near<=30).mean():.0%}")
for f_ in ["annual","monthly"]:
    x = A[A.freq==f_]; print(f"  churn das contas cuja última assinatura paga é {f_}: {x.churn_flag.sum()}/{len(x)} ({x.churn_flag.mean():.1%})")
x = pd.crosstab(A.freq, A.churn_flag); print(f"  Fisher anual x mensal: p={stats.fisher_exact(x.values)[1]:.3f}")
print("\n=== hipótese de idioma: suporte nos países sem inglês (DE, FR) vs anglófonos")
tk["grupo"] = tk.account_id.map(A.country).isin(["DE","FR"]).map({True:"DE/FR", False:"anglófonos"})
tk["tem_nota"] = tk.satisfaction_score.notna()
q = tk.groupby("grupo").agg(tickets=("ticket_id","size"), resol_h=("resolution_time_hours","mean"), resp_min=("first_response_time_minutes","mean"), csat=("satisfaction_score","mean"), com_nota=("tem_nota","mean"), escalado=("escalation_flag","mean"))
print(q.round(3).to_string())
for col in ["resolution_time_hours","first_response_time_minutes","satisfaction_score"]:
    x1, x2 = tk[tk.grupo=="DE/FR"][col].dropna(), tk[tk.grupo!="DE/FR"][col].dropna(); print(f"  {col}: Mann-Whitney p={stats.mannwhitneyu(x1,x2).pvalue:.3f}")
print(f"  escalação: Fisher p={stats.fisher_exact(pd.crosstab(tk.grupo, tk.escalation_flag).values)[1]:.3f}")
print("  só DE:", tk[tk.account_id.map(A.country)=="DE"][["resolution_time_hours","first_response_time_minutes","satisfaction_score","escalation_flag"]].mean().round(2).to_dict())
print(f"  tickets por conta: DE {tk.account_id.map(A.country).eq('DE').sum()/de.sum():.1f} | geral {len(tk)/len(A):.1f}")
print("\n=== tábua de vida: risco mensal pela IDADE no momento (não pela idade hoje), separado por ano-calendário")
rows = []
for aid, x in A.iterrows():
    n = int(np.floor(x.vida)) + 1
    for m in range(n):
        d = x.signup + pd.Timedelta(days=30.44*m)
        rows.append((aid, x.country, m, d.year, bool(x.churn_flag and m == n-1)))
L = pd.DataFrame(rows, columns=["aid","pais","idade_m","ano","churn"])
L["faixa"] = pd.cut(L.idade_m, [-1,5,11,17,23,99], labels=["0–5","6–11","12–17","18–23","24+"])
h = L.pivot_table(index="faixa", columns="ano", values="churn", aggfunc=["mean","size"], observed=True)
print((100*h["mean"]).round(2).to_string()); print("  contas-mês:\n", h["size"].to_string())
print("  risco mensal por país (contas-mês, mesmo método):", (100*L.groupby("pais").churn.mean()).round(2).to_dict())
print("  idem, só 2024:", (100*L[L.ano==2024].groupby("pais").churn.mean()).round(2).to_dict())
print("\n=== conferência das 5 canceladas da França citadas no texto")
print(A.loc[["A-038089","A-ccc747","A-798a3f","A-72799b","A-117171"], ["country","plan_tier","freq","vida","idade_ref"]].round(1).to_string())
print("\n=== sensibilidade: 2024, sem as 35 canceladas sem evento (churn datado artificialmente em 31/12)")
sem = A.index[A.churn_flag & A.index.map(last_ev).isna()]
L24 = L[(L.ano==2024) & ~L.aid.isin(sem)]
for nome, cond in [("idade 0–11 m", L24.idade_m < 12), ("idade 12+ m", L24.idade_m >= 12)]:
    x = L24[cond]; print(f"  {nome}: {x.churn.sum()} churns em {len(x)} contas-mês = {100*x.churn.mean():.2f}%/mês")
y, o = L24[L24.idade_m >= 12], L24[L24.idade_m < 12]
print(f"  razão de taxas 12+/0–11: {y.churn.mean()/o.churn.mean():.2f} | teste binomial condicional p={stats.binomtest(int(y.churn.sum()), int(y.churn.sum()+o.churn.sum()), len(y)/(len(y)+len(o))).pvalue:.3f}")
print("  (idade, período e coorte não se separam: quem tem 12+ meses em 2024 é, por construção, das coortes de 2023)")
