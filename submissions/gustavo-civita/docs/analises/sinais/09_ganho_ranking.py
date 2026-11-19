"""Ganho de ranking: quanto do valor ganho depois de T fica no topo da lista de cada vendedor (top 10) e no top 10% da empresa,
ordenando por variantes do score. Baseline = preco x chance por idade (solucao atual). Tudo calculado so com dados ate T."""
from common import *
from bt import *
import os, subprocess, sys
if not os.path.exists("snapshots.pkl"):  # gerado pelo bt.py
    subprocess.run([sys.executable, "bt.py"], check=True, stdout=subprocess.DEVNULL)
d = load(); S = pd.read_pickle("snapshots.pkl")
glob = 0.63
zr_all = {}
for T in sorted(S["T"].unique()):
    old = d[d.engage_date <= T - pd.Timedelta(days=140)]
    zr_all[T] = (old.close_date.isna() | (old.close_date > T)).groupby(old.sales_agent).mean()
S["zr"] = [zr_all[T].get(a, np.nan) for T, a in zip(S["T"], S.sales_agent)]; S["zr"] = S.zr.fillna(S.groupby("T").zr.transform("mean"))
base = S.sales_price * S.p0
V = {"baseline preco x chance(idade)": base,
     "so preco (entre chance>0)": S.sales_price * (S.p0 > 0),
     "so chance": S.p0 + S.sales_price * 1e-9,
     "x taxa de ganho hist. do vendedor": base * S.wr_agent,
     "x taxa hist. vendedor x produto": base * S.wr_agent_x_product,
     "x (1 - taxa de zumbis hist. do vendedor)": base * (1 - S.zr),
     "x carga: / deals abertos do vendedor": base / S.agent_open_n,
     "x taxa hist. da conta (sem conta = media)": base * S.wr_account,
     "x recompra conta x produto (+20%)": base * (1 + .2 * S.prior_won_account_x_product),
     "[ARTEFATO] x tem conta preenchida": base * (0.2 + S.has_account),
     "aleatorio entre chance>0": (S.p0 > 0) * np.random.default_rng(0).random(len(S))}
def capture(S, score, ycol, per_agent_k=10, top_frac=.10):
    out = []
    for T, s in S.assign(score=score).groupby("T"):
        tot = s[ycol].sum()
        topa = s.sort_values("score", ascending=False).groupby("sales_agent").head(per_agent_k)[ycol].sum()
        topc = s.nlargest(int(len(s) * top_frac), "score")[ycol].sum()
        out.append((T, topa / tot, topc / tot))
    return pd.DataFrame(out, columns=["T", "top10_vendedor", "top10pct_empresa"]).set_index("T")
per = {"A (jun-jul, ganho ate o fim)": (CUT_A, "val_future"), "B (ago-set, ganho ate o fim)": (CUT_B, "val_future"), "C (out-nov, ganho em 30d)": (CUT_C, "val30"),
       "todos, ganho em 30d": (CUT_A + CUT_B + CUT_C, "val30")}
rows = []
for name, sc in V.items():
    r = {"score": name}
    for lab, (cuts, y) in per.items():
        m = S["T"].isin(pd.to_datetime(cuts)); c = capture(S[m], sc[m], y)
        r[lab + " | top10/vend"] = 100 * c.top10_vendedor.mean(); r[lab + " | top10% emp"] = 100 * c.top10pct_empresa.mean()
    rows.append(r)
R = pd.DataFrame(rows).set_index("score"); R.to_csv("09_ganho_ranking.csv")
print("% do valor ganho capturado (media dos cortes)"); print(R.round(1).T.to_string())
print("\ndiferenca vs baseline (pontos percentuais)"); print((R - R.iloc[0]).round(1).T.to_string())
# por corte, variante zumbis vs baseline
m = pd.Series(True, index=S.index)
a = capture(S, V["baseline preco x chance(idade)"], "val_future"); b = capture(S, V["x (1 - taxa de zumbis hist. do vendedor)"], "val_future"); c = capture(S, V["x taxa de ganho hist. do vendedor"], "val_future")
print("\npor corte (top10 por vendedor; ganho ate 31/12): baseline | x(1-zumbis) | x wr vendedor"); print(pd.concat([a.top10_vendedor, b.top10_vendedor, c.top10_vendedor], axis=1).round(3).to_string())
