#!/usr/bin/env python3
# Historico de compras x ficar SEM DESFECHO (deals com cliente, coorte madura, comparando dentro do mes de engajamento).
import csv, math, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from statistics import median
DD = sys.argv[1]
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
def chi2_sf1(x):
    return math.erfc(math.sqrt(x / 2.0)) if x == x else float("nan")
def cmh(strata):
    num = var = dn = dd = 0.0
    for a, b, c, d in strata:
        n = a+b+c+d; n1 = a+b; n0 = c+d
        if n < 2 or n1 == 0 or n0 == 0: continue
        num += a - n1*(a+c)/n; var += n1*n0*(a+c)*(b+d)/(n*n*(n-1.0)); dn += (a*n0 - c*n1)/n; dd += n1*n0/n
    if var == 0: return float("nan"), float("nan"), float("nan")
    x = (abs(num)-0.5)**2/var
    return x, chi2_sf1(x), 100.0*dn/dd
def pct(a, b): return 100.0*a/b if b else float("nan")
prodt = {r["product"]: r for r in load("products.csv")}
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["acc"] = r["account"].strip(); r["st"] = r["deal_stage"]
    r["prod"] = r["product"].replace("GTXPro", "GTX Pro"); r["series"] = prodt[r["prod"]]["series"]
closed = [r for r in pipe if r["st"] in ("Won", "Lost")]
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
maxcyc = max((r["c"]-r["e"]).days for r in closed); cutoff = ref - timedelta(days=maxcyc)
byacc = defaultdict(list)
for r in pipe:
    if r["acc"]: byacc[r["acc"]].append(r)
ev = [r for r in pipe if r["acc"] and r["e"] and date(2017, 4, 1) <= r["e"] < cutoff and r["st"] in ("Won", "Lost", "Engaging")]
for r in ev:
    pr = [x for x in byacc[r["acc"]] if x is not r]
    pw = [x for x in pr if x["st"] == "Won" and x["c"] < r["e"]]
    pl = [x for x in pr if x["st"] == "Lost" and x["c"] < r["e"]]
    r["stall"] = r["st"] == "Engaging"
    r["h_won"] = len(pw); r["h_val"] = sum(float(x["close_value"]) for x in pw)
    r["h_same"] = any(x["prod"] == r["prod"] for x in pw)
    r["h_rel"] = sum(1 for x in pw if x["sales_agent"] == r["sales_agent"])
    r["h_rec"] = min((r["e"]-x["c"]).days for x in pw) if pw else None
    r["h_wr"] = len(pw)/float(len(pw)+len(pl)) if len(pw)+len(pl) >= 5 else None
    r["mk"] = "%d-%02d" % (r["e"].year, r["e"].month)
print("deals com cliente, engajados de 2017-04-01 ate antes de %s: %d | sem desfecho %d (%.1f%%)" % (
    cutoff, len(ev), sum(r["stall"] for r in ev), pct(sum(r["stall"] for r in ev), len(ev))))
def med(g, k):
    v = [r[k] for r in g if r[k] is not None]
    return median(v) if v else None
TESTS = (
    ("este vendedor ja ganhou nesta conta", lambda r, g: r["h_rel"] > 0),
    ("vendedor ja ganhou 2+ vezes nesta conta", lambda r, g: r["h_rel"] >= 2),
    ("conta ja comprou ESTE produto", lambda r, g: r["h_same"]),
    ("mais compras anteriores que a mediana do mes", lambda r, g: r["h_won"] > med(g, "h_won")),
    ("mais valor comprado que a mediana do mes", lambda r, g: r["h_val"] > med(g, "h_val")),
    ("comprou ha menos tempo que a mediana do mes", lambda r, g: None if r["h_rec"] is None else r["h_rec"] < med(g, "h_rec")),
    ("taxa de ganho anterior acima da mediana", lambda r, g: None if r["h_wr"] is None else r["h_wr"] > med(g, "h_wr")),
)
for name, flag in TESTS:
    strata = []; t1 = [0, 0]; t0 = [0, 0]
    for mk in sorted({r["mk"] for r in ev}):
        g = [r for r in ev if r["mk"] == mk]; a = b = c = d = 0
        for r in g:
            f = flag(r, g)
            if f is None: continue
            if f:
                if r["stall"]: a += 1
                else: b += 1
            else:
                if r["stall"]: c += 1
                else: d += 1
        strata.append((a, b, c, d)); t1[0] += a; t1[1] += b; t0[0] += c; t0[1] += d
    x, p, diff = cmh(strata)
    print("  %-44s sem desfecho: sim %.1f%% (n=%d) x nao %.1f%% (n=%d) | dif. dentro do mes %+.1f pp | CMH qui2=%.2f p=%.4f" % (
        name, pct(t1[0], sum(t1)), sum(t1), pct(t0[0], sum(t0)), sum(t0), diff, x, p))
print("  por numero de compras anteriores da conta (sem estratificar):")
for lo, hi in ((0, 5), (6, 15), (16, 30), (31, 999)):
    g = [r for r in ev if lo <= r["h_won"] <= hi]
    if g: print("     %3d-%-3d: sem desfecho %.1f%% (n=%d)" % (lo, hi, pct(sum(r["stall"] for r in g), len(g)), len(g)))
