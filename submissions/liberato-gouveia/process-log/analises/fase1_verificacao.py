"""Fase 1: verificação da análise inicial (itens A, B, D, E, F e G).

Uso: python3 fase1_verificacao.py <pasta_dos_dados>
Todos os números da Fase 1 no registro vêm da saída deste script.
"""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

D = sys.argv[1]
SNAPSHOT = pd.Timestamp("2017-12-31")  # último dia com registro na base

p = pd.read_csv(f"{D}/sales_pipeline.csv")
a = pd.read_csv(f"{D}/accounts.csv")
pr = pd.read_csv(f"{D}/products.csv")
t = pd.read_csv(f"{D}/sales_teams.csv")
p["product"] = p["product"].replace("GTXPro", "GTX Pro")
for c in ["engage_date", "close_date"]:
    p[c] = pd.to_datetime(p[c])
p = p.merge(pr, on="product", how="left").merge(t, on="sales_agent", how="left").merge(a, on="account", how="left")
p["ciclo"] = (p.close_date - p.engage_date).dt.days
p["idade_hoje"] = (SNAPSHOT - p.engage_date).dt.days

def titulo(x):
    print("\n" + "=" * 70 + f"\n{x}\n" + "=" * 70)

# ---------------------------------------------------------------- A
titulo("A) Chance de ganhar usando só a IDADE ATUAL do deal (sem futuro)")
# Safra iniciada em mar-jun/2017: todos os desfechos a partir de 01/03/2017 são
# observáveis e cada deal teve >= 183 dias de acompanhamento até 31/12/2017.
safra = p[(p.engage_date >= "2017-03-01") & (p.engage_date <= "2017-06-30")].copy()
safra["acomp"] = (SNAPSHOT - safra.engage_date).dt.days
print(f"Safra mar-jun/2017: {len(safra)} deals | acompanhamento mínimo {safra.acomp.min()} dias")
linhas = []
for idade in [0, 7, 14, 30, 60, 90, 120, 138]:
    # "vivo na idade X": não tinha fechado antes de X dias
    vivo = safra[(safra.ciclo.isna()) | (safra.ciclo >= idade)] if idade > 0 else safra
    ganho = (vivo.deal_stage == "Won").mean()
    perdido = (vivo.deal_stage == "Lost").mean()
    aberto = (vivo.deal_stage == "Engaging").mean()
    resolvidos = vivo[vivo.deal_stage.isin(["Won", "Lost"])]
    g_res = (resolvidos.deal_stage == "Won").mean() if len(resolvidos) else np.nan
    linhas.append((idade, len(vivo), ganho, perdido, aberto, g_res, len(resolvidos)))
tab = pd.DataFrame(linhas, columns=["vivo_na_idade", "n", "ganhou", "perdeu", "ainda_aberto", "ganho_entre_resolvidos", "n_resolvidos"])
print(tab.round(3).to_string(index=False))

# ---------------------------------------------------------------- B
titulo("B) O limite de 138 dias é real ou efeito da janela da base?")
fech = p[p.deal_stage.isin(["Won", "Lost"])]
for mes in pd.period_range("2016-10", "2017-09", freq="M"):
    m = p[p.engage_date.dt.to_period("M") == mes]
    f = m[m.deal_stage.isin(["Won", "Lost"])]
    ab = m[m.deal_stage == "Engaging"]
    acomp = (SNAPSHOT - mes.start_time).days
    print(f"{mes}: acompanhamento até ~{acomp:>3} dias | fechados {len(f):>4} | maior ciclo {f.ciclo.max():>5} | ainda abertos {len(ab):>3}")
print(f"Deals fechados com ciclo > 138: {(fech.ciclo > 138).sum()}")
print(f"Deals fechados por data de fechamento - primeiro: {fech.close_date.min().date()} | último: {fech.close_date.max().date()}")

# ---------------------------------------------------------------- D
titulo("D) Deals sem empresa cadastrada")
print("Fechados (ganhos/perdidos) sem empresa:", fech.account.isna().sum(), "de", len(fech))
eng = p[p.deal_stage == "Engaging"].copy()
eng["vivo"] = eng.idade_hoje <= 138
print("Em negociação, vivos (<=138 dias):", eng.vivo.sum(), "| sem empresa:", (eng.vivo & eng.account.isna()).sum())
print("Em negociação, zumbis (>138 dias):", (~eng.vivo).sum(), "| sem empresa:", ((~eng.vivo) & eng.account.isna()).sum())
print("% sem empresa por faixa de idade (negociação):")
print(eng.groupby(pd.cut(eng.idade_hoje, [-1, 30, 60, 90, 138, 200, 300, 500])).account.apply(lambda s: round(s.isna().mean(), 3)).to_string())
print("% sem empresa por vendedor (negociação) - mín/máx:",
      eng.groupby("sales_agent").account.apply(lambda s: s.isna().mean()).agg(["min", "max"]).round(3).to_dict())

# ---------------------------------------------------------------- E
titulo("E) Deals em prospecção")
pro = p[p.deal_stage == "Prospecting"]
print("Prospecção:", len(pro), "| com data de início:", pro.engage_date.notna().sum(), "| sem empresa:", pro.account.isna().sum())
print("Deals fechados SEM data de início (indicaria histórico de prospecção):", fech.engage_date.isna().sum())
print("Valor de tabela somado em prospecção (US$):", int(pro.sales_price.sum()))

# ---------------------------------------------------------------- F
titulo("F) Machine learning com separação no TEMPO (treina no passado, testa no futuro)")
c = fech.copy().sort_values("engage_date")
c["won"] = (c.deal_stage == "Won").astype(int)
c["vitorias_previas_conta"] = 0
for acc, g in c.groupby("account"):
    datas_vit = g.loc[g.won == 1, "close_date"].values
    c.loc[g.index, "vitorias_previas_conta"] = [int((datas_vit < d).sum()) for d in g.engage_date.values]
c["mes_inicio"] = c.engage_date.dt.month
cat = ["sales_agent", "product", "manager", "regional_office", "sector", "office_location"]
num = ["sales_price", "revenue", "employees", "year_established", "vitorias_previas_conta", "mes_inicio"]
X = pd.get_dummies(c[cat].astype(str)).join(c[num].fillna(-1)).astype(float)
y = c.won.values
corte = int(len(c) * 0.7)
data_corte = c.engage_date.iloc[corte]
Xtr, Xte, ytr, yte = X.iloc[:corte], X.iloc[corte:], y[:corte], y[corte:]
print(f"Treino: {corte} deals iniciados até {data_corte.date()} | Teste: {len(c) - corte} deals iniciados depois")
gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, random_state=42).fit(Xtr, ytr)
lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)).fit(Xtr, ytr)
print("AUC gradient boosting (teste no futuro):", round(roc_auc_score(yte, gb.predict_proba(Xte)[:, 1]), 3))
print("AUC regressão logística (teste no futuro):", round(roc_auc_score(yte, lr.predict_proba(Xte)[:, 1]), 3))

# ---------------------------------------------------------------- G
titulo("G) Padrão de fim de trimestre")
fech2 = fech.assign(mes_fech=fech.close_date.dt.month, ganho=(fech.deal_stage == "Won").astype(int))
g = fech2.groupby("mes_fech").agg(ganhos=("ganho", "sum"), perdidos=("ganho", lambda s: (1 - s).sum()), taxa=("ganho", "mean"))
print(g.round(3).to_string())
fim_tri = fech2.mes_fech.isin([3, 6, 9, 12])
print(f"Ganhos registrados em mês de fim de trimestre: {fech2[fim_tri].ganho.sum()} de {fech2.ganho.sum()} ({fech2[fim_tri].ganho.sum() / fech2.ganho.sum():.0%})")
print(f"Perdidos registrados em mês de fim de trimestre: {(1 - fech2[fim_tri].ganho).sum()} de {(1 - fech2.ganho).sum()} ({(1 - fech2[fim_tri].ganho).sum() / (1 - fech2.ganho).sum():.0%})")
print("Taxa de ganho pelo MÊS DE INÍCIO (informação conhecida no começo do deal):")
print(fech2.groupby(fech2.engage_date.dt.month).ganho.agg(["size", "mean"]).round(3).to_string())
