#!/usr/bin/env python3
# Listas da maquina do tempo do Daniell em 4 dez 2017, com identificadores. So stdlib. Uso: python3 -I tm.py <dados>
import csv, os, sys
from datetime import datetime, date, timedelta
from collections import defaultdict
DD = sys.argv[1]; D = date(2017, 12, 4); WHO = "Daniell Hammack"; H = 30
MES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
def fd(d): return "%d %s" % (d.day, MES[d.month-1])
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip(); return datetime.strptime(s, "%Y-%m-%d").date() if s else None
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
P = [r for r in load("sales_pipeline.csv") if r["engage_date"].strip()]
for r in P:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["pn"] = r["product"].replace("GTXPro", "GTX Pro"); r["price"] = prod[r["pn"]]
    r["won"] = r["deal_stage"] == "Won"; r["val"] = float(r["close_value"]) if r["won"] else 0.0
AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)
def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim: return i
    return len(AGEB)
def wk(d): return (d - date(d.year, 3*((d.month-1)//3)+1, 1)).days // 7
def snap(d): return [r for r in P if r["e"] < d and (r["c"] is None or r["c"] >= d)]
cnt = defaultdict(lambda: [0, 0]); m = date(2017, 3, 6)
while m + timedelta(days=H) <= D:
    for r in snap(m):
        k = (ageb((m-r["e"]).days), wk(m)); cnt[k][1] += 1
        if r["won"] and r["c"] < m + timedelta(days=H): cnt[k][0] += 1
    m += timedelta(days=7)
mine = []
for r in snap(D):
    if r["sales_agent"] != WHO: continue
    age = (D-r["e"]).days; y, n = cnt[(ageb(age), wk(D))]; p = 0.0 if age > 138 else y/float(n)
    mine.append(dict(r=r, age=age, p=p, ev=p*r["price"], stale=age > 138))
def out(x):
    r = x["r"]
    if r["c"]: return ("Venda US$ %.0f em %s" % (r["val"], fd(r["c"]))) if r["won"] else ("Perda em %s" % fd(r["c"]))
    return "Segue aberto"
def show(title, lst):
    print(title); w = sum(1 for x in lst if x["r"]["won"]); v = sum(x["r"]["val"] for x in lst)
    for i, x in enumerate(lst, 1):
        print("  %2d #%s %-14s US$ %5.0f %3d dias %s | %s" % (i, x["r"]["opportunity_id"], x["r"]["pn"], x["r"]["price"], x["age"], "(sem desfecho)" if x["stale"] else "", out(x)))
    print("  => %d vendas, US$ %.0f" % (w, v))
show("PELO SCORE (empate: mais antigo primeiro)", sorted(mine, key=lambda x: (-round(x["ev"], 2), -x["age"]))[:10])
show("SO POR VALOR (empate: mais antigo primeiro)", sorted(mine, key=lambda x: (-x["r"]["price"], -x["age"]))[:10])
live = [x for x in mine if not x["stale"]]
show("POR VALOR SEM OS SEM DESFECHO (empate: mais antigo primeiro)", sorted(live, key=lambda x: (-x["r"]["price"], -x["age"]))[:10])
show("POR VALOR SEM OS SEM DESFECHO (empate: mais novo primeiro)", sorted(live, key=lambda x: (-x["r"]["price"], x["age"]))[:10])
print("vivos por produto:", {p: sum(1 for x in live if x["r"]["pn"] == p) for p in sorted({x["r"]["pn"] for x in live}, key=lambda p: -prod[p])})
