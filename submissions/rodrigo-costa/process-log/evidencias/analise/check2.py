#!/usr/bin/env python3
# Conferencia cruzada dos achados do revisor independente, com o MEU codigo (mesma logica de backtest.py):
# serie por data (A valor, B valor sem parados, B2 = B com o mais novo primeiro, C score), por trimestre, top 5/10/20.
# So stdlib. Uso: python3 -I check2.py <pasta com os CSV>
import csv, os, random, sys
from collections import defaultdict
from datetime import datetime, timedelta, date
DD = sys.argv[1]; H = 30; MINN = 30; REP = 20
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pdate(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
pipe = [r for r in load("sales_pipeline.csv") if r["engage_date"].strip()]
for r in pipe:
    r["e"] = pdate(r["engage_date"]); r["c"] = pdate(r["close_date"])
    r["price"] = prod[r["product"].replace("GTXPro", "GTX Pro")]
    r["won"] = r["deal_stage"] == "Won"; r["val"] = float(r["close_value"]) if r["won"] else 0.0
AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)
def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim: return i
    return len(AGEB)
def qpos(d):
    qs = date(d.year, 3*((d.month-1)//3)+1, 1); return (d-qs).days//7, (d.month-1) % 3
def snapshot(d):
    end = d + timedelta(days=H); out = []
    for r in pipe:
        if r["e"] < d and (r["c"] is None or r["c"] >= d):
            y = 1 if (r["won"] and r["c"] < end) else 0
            out.append((r, (d-r["e"]).days, y, r["val"] if y else 0.0))
    return out
mondays = []; d = date(2017, 3, 6)
while d <= date(2017, 12, 25): mondays.append(d); d += timedelta(days=7)
SNAP = {m: snapshot(m) for m in mondays}
EVAL = [m for m in mondays if date(2017, 7, 3) <= m <= date(2017, 12, 1)]
def train(dref):
    c_wk = defaultdict(lambda: [0, 0]); c_mo = defaultdict(lambda: [0, 0]); c_age = defaultdict(lambda: [0, 0]); tot = [0, 0]
    for m in mondays:
        if m + timedelta(days=H) > dref: continue
        wk, mo = qpos(m)
        for r, age, y, v in SNAP[m]:
            b = ageb(age)
            for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
                tab[key][0] += y; tab[key][1] += 1
            tot[0] += y; tot[1] += 1
    mc = max([(r["c"]-r["e"]).days for r in pipe if r["c"] and r["c"] < dref] or [0])
    return c_wk, c_mo, c_age, tot, mc
def p_cal(model, age, dref):
    c_wk, c_mo, c_age, tot, mc = model; b = ageb(age); wk, mo = qpos(dref)
    for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
        y, n = tab.get(key, (0, 0))
        if n >= MINN: return y/float(n)
    return tot[0]/float(tot[1]) if tot[1] else 0.0
KEYS = {
    "A": lambda x, j: (x["price"], j),
    "B": lambda x, j: (0 if x["stale"] else 1, x["price"], j),
    "B2": lambda x, j: (0 if x["stale"] else 1, x["price"], -x["age"], j),
    "C": lambda x, j: (x["pc"]*x["price"], j),
}
MODELS = {dref: train(dref) for dref in EVAL}
ROWS = {}
for dref in EVAL:
    model = MODELS[dref]; mc = model[4]; bys = defaultdict(list)
    for r, age, y, v in SNAP[dref]:
        bys[r["sales_agent"]].append(dict(age=age, y=y, v=v, pc=p_cal(model, age, dref), price=r["price"], stale=age > mc))
    ROWS[dref] = bys
print("maior ciclo conhecido por data:", sorted({MODELS[d][4] for d in EVAL}))
for TOPN in (5, 10, 20):
    rng = random.Random(7)
    tot = {m: [0.0, 0.0] for m in KEYS}; perd = []; nl = 0
    byq = defaultdict(lambda: {m: 0.0 for m in KEYS})
    for dref in EVAL:
        ds = {m: 0.0 for m in KEYS}
        for s, lst in ROWS[dref].items():
            if len(lst) < TOPN: continue
            nl += 1
            for m, kf in KEYS.items():
                w = v = 0.0
                for _ in range(REP):
                    jit = [rng.random() for _ in lst]
                    order = sorted(range(len(lst)), key=lambda i: kf(lst[i], jit[i]), reverse=True)[:TOPN]
                    w += sum(lst[i]["y"] for i in order); v += sum(lst[i]["v"] for i in order)
                tot[m][0] += w/REP; tot[m][1] += v/REP; ds[m] += v/REP
                byq["jul-set" if dref.month <= 9 else "out-nov"][m] += v/REP
        perd.append((dref, ds))
    print()
    print("TOP %d | listas %d" % (TOPN, nl))
    for m in KEYS:
        print("   %-2s vendas por lista %.4f | receita US$ %.0f" % (m, tot[m][0]/nl, tot[m][1]))
    print("   C/A %.3f | C/B %.3f | C/B2 %.3f" % (tot["C"][1]/tot["A"][1], tot["C"][1]/tot["B"][1], tot["C"][1]/tot["B2"][1]))
    for q in ("jul-set", "out-nov"):
        b = byq[q]; print("   %s: C/A %.3f | C/B %.3f | C/B2 %.3f" % (q, b["C"]/b["A"], b["C"]/b["B"], b["C"]/b["B2"]))
    print("   datas em que C > A: %d de %d | C > B: %d | C > B2: %d" % (
        sum(1 for _, ds in perd if ds["C"] > ds["A"]), len(perd), sum(1 for _, ds in perd if ds["C"] > ds["B"]), sum(1 for _, ds in perd if ds["C"] > ds["B2"])))
    if TOPN == 10:
        for dref, ds in perd:
            print("      %s  A %7.0f | B %7.0f | B2 %7.0f | C %7.0f%s" % (dref, ds["A"], ds["B"], ds["B2"], ds["C"], "   <- C perde de B" if ds["C"] <= ds["B"] else ""))
