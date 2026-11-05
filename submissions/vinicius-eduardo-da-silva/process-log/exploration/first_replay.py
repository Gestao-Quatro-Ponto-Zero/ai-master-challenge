"""Replay past Monday mornings: rank each rep's open deals using only what was known that day."""
import sys
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
d = sys.argv[1]
pr = pd.read_csv(f"{d}/products.csv")
p = pd.read_csv(f"{d}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
p = p.merge(pr, on="product", how="left")
e = p[p.engage_date.notna()].copy()  # Prospecting has no dates, so it cannot be replayed
e["won"] = (e.deal_stage == "Won").astype(int)
e["cycle"] = (e.close_date - e.engage_date).dt.days

print("== Quarter effect: month position x outcome")
c = e[e.close_date.notna()].copy()
c["mpos"] = (c.close_date.dt.month - 1) % 3 + 1
c["cb"] = pd.cut(c.cycle, [0, 14, 30, 60, 90, 138])
print(c.pivot_table(index="cb", columns="mpos", values="won", aggfunc=["size", "mean"], observed=True).round(3))
print(c.groupby("mpos").deal_stage.value_counts().unstack())
print("week of month in month 3:", c[c.mpos == 3].groupby(c.close_date.dt.day // 8).won.mean().round(3).to_dict())

H = 30
BIN = 15


def age_table(known_closed, known_all, s):
    """P(won within H days | alive at age bin), estimated only from information available at s."""
    rows = {}
    for b in range(0, 150, BIN):
        # eligible: reached age b early enough that the H-day outcome is already observable at s
        start = known_all.engage_date + pd.to_timedelta(b, "D")
        alive = known_all[(start + pd.to_timedelta(H, "D") <= s) & (known_all.end >= b)]
        wins = ((alive.won_known == 1) & (alive.end < b + H)).sum()
        rows[b] = (wins + 2) / (len(alive) + 10)  # light smoothing
    return rows


snaps = pd.date_range("2017-07-03", "2017-11-27", freq="7D")
rng = np.random.default_rng(0)
out = []
for s in snaps:
    known = e[e.engage_date < s].copy()
    closed_before = known.close_date < s
    known["won_known"] = np.where(closed_before, known.won, 0)
    known["end"] = np.where(closed_before, known.cycle, (s - known.engage_date).dt.days)
    max_seen = known.loc[closed_before, "cycle"].max()
    table = age_table(known[closed_before], known, s)
    o = known[~closed_before].copy()
    o["age"] = (s - o.engage_date).dt.days
    o["realized"] = np.where((o.close_date >= s) & (o.close_date < s + pd.Timedelta(days=H)) & (o.won == 1), o.close_value, 0.0)
    o["won_h"] = (o.realized > 0).astype(int)
    closed_hist = known[closed_before]
    prod_wr = closed_hist.groupby("product").won.agg(["sum", "size"])
    base = closed_hist.won.mean()
    o["p_static"] = o["product"].map(lambda x: (prod_wr["sum"].get(x, 0) + 20 * base) / (prod_wr["size"].get(x, 0) + 20))
    o["p_time"] = [table.get(min(a // BIN * BIN, 135), 0) if a <= max_seen else 0.0 for a in o.age]
    strategies = {
        "random": rng.random(len(o)),
        "maior_valor": o.sales_price.values,
        "mais_novo": -o.age.values,
        "mais_antigo": o.age.values,
        "EV_estatico": (o.p_static * o.sales_price).values,
        "EV_tempo": (o.p_time * o.sales_price).values,
        "so_tempo": o.p_time.values,
    }
    for name, score in strategies.items():
        o["_s"] = score
        for k in (5, 10, 20):
            top = o.sort_values("_s", ascending=False).groupby("sales_agent").head(k)
            out.append(dict(s=s, strat=name, k=k, rev=top.realized.sum(), wins=top.won_h.sum(), n=len(top), zombies=(top.age > max_seen).sum(), pool_rev=o.realized.sum(), pool=len(o), zombies_pool=(o.age > max_seen).sum()))

r = pd.DataFrame(out)
g = r.groupby(["k", "strat"]).agg(rev_mes=("rev", "mean"), wins=("wins", "mean"), n=("n", "mean"), zumbi=("zombies", "mean"), cap=("rev", "sum"), pool=("pool_rev", "sum"))
g["win_por_deal"] = g.wins / g.n
g["captura"] = g.cap / g.pool
print("\n== Replay:", len(snaps), "Mondays, H =", H, "days")
print(g.drop(columns=["cap", "pool"]).round(3).to_string())
print("\npool size / zombies at first and last snapshot")
print(r[r.strat == "random"].drop_duplicates("s")[["s", "pool", "zombies_pool", "pool_rev"]].iloc[[0, 5, 10, 15, -1]].to_string(index=False))

print("\n== Paired: EV_tempo vs maior_valor, k=10, per snapshot")
w = r[r.k == 10].pivot(index="s", columns="strat", values="rev")
diff = w.EV_tempo - w.maior_valor
print("mean diff", round(diff.mean()), "wins", (diff > 0).sum(), "of", len(diff))
boot = [diff.sample(len(diff), replace=True, random_state=i).mean() for i in range(2000)]
print("95% CI (snapshot bootstrap, overlapping horizons so optimistic)", np.percentile(boot, [2.5, 97.5]).round())
