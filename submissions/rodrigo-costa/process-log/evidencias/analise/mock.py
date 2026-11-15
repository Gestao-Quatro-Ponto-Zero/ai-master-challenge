#!/usr/bin/env python3
# Dados reais para as telas do estudo de UX: retrato da base em uma segunda-feira (data de referencia).
# Mesmo modelo do prototipo: chance de virar venda em 30 dias por idade x ponto do trimestre, so com o que se sabia na data.
import csv, os, sys, json
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date
DD = sys.argv[1]; DREF = datetime.strptime(sys.argv[2], "%Y-%m-%d").date(); WHO = sys.argv[3] if len(sys.argv) > 3 else None
H = 30
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
allp = load("sales_pipeline.csv")
pipe = [r for r in allp if r["engage_date"].strip()]
for r in pipe:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["pname"] = r["product"].replace("GTXPro", "GTX Pro")
    r["price"] = prod[r["pname"]]; r["won"] = r["deal_stage"] == "Won"; r["val"] = float(r["close_value"]) if r["won"] else 0.0
AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)
def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim: return i
    return len(AGEB)
def qpos(d):
    qs = date(d.year, 3*((d.month-1)//3)+1, 1)
    return (d-qs).days//7, (d.month-1) % 3
def snapshot(d):
    end = d + timedelta(days=H); out = []
    for r in pipe:
        if r["e"] < d and (r["c"] is None or r["c"] >= d):
            out.append((r, (d-r["e"]).days, 1 if (r["won"] and r["c"] < end) else 0))
    return out
mondays = []; d = date(2017, 3, 6)
while d <= date(2017, 12, 25): mondays.append(d); d += timedelta(days=7)
c_wk = defaultdict(lambda: [0, 0]); c_mo = defaultdict(lambda: [0, 0]); c_age = defaultdict(lambda: [0, 0]); tot = [0, 0]
for m in mondays:
    if m + timedelta(days=H) > DREF: continue
    wk, mo = qpos(m)
    for r, age, y in snapshot(m):
        b = ageb(age)
        for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
            tab[key][0] += y; tab[key][1] += 1
        tot[0] += y; tot[1] += 1
maxc = max((r["c"]-r["e"]).days for r in pipe if r["c"] and r["c"] < DREF)
def chance(age):
    b = ageb(age); wk, mo = qpos(DREF)
    for lvl, tab, key in (("semana", c_wk, (b, wk)), ("mes", c_mo, (b, mo)), ("idade", c_age, b)):
        y, n = tab.get(key, (0, 0))
        if n >= 30: return y/float(n), n, y, lvl
    return tot[0]/float(tot[1]), tot[1], tot[0], "geral"
rows = []
for r, age, y in snapshot(DREF):
    p, n, yy, lvl = chance(age)
    stale = age > maxc
    rows.append(dict(id=r["opportunity_id"], s=r["sales_agent"], prod=r["pname"], acc=r["account"].strip(), price=r["price"], age=age, e=str(r["e"]),
                     p=0.0 if stale else p, n=n, y=yy, lvl=lvl, stale=stale, ev=0.0 if stale else p*r["price"],
                     won30=y, val30=r["val"] if y else 0.0, final=r["deal_stage"], c=str(r["c"]) if r["c"] else "", val=r["val"]))
live = sorted([x for x in rows if not x["stale"]], key=lambda x: x["ev"])
evs = [x["ev"] for x in live]
import bisect
for x in rows:
    x["score"] = None if x["stale"] else int(round(100.0*bisect.bisect_right(evs, x["ev"])/len(evs)))
def band(x):
    if x["stale"]: return "sem desfecho"
    return "quente" if x["score"] >= 80 else ("morno" if x["score"] >= 40 else "frio")
for x in rows: x["band"] = band(x)
wk, mo = qpos(DREF)
print("DATA %s (%s) | semana %d do trimestre, mes %d de 3 | maior ciclo conhecido %d | abertos %d | vivos %d | sem desfecho %d" % (
    DREF, ["seg","ter","qua","qui","sex","sab","dom"][DREF.weekday()], wk, mo+1, maxc, len(rows), len(live), len(rows)-len(live)))
print("empresa: declarado US$ %.0f | vivo US$ %.0f | sem desfecho US$ %.0f | esperado em 30d US$ %.0f | venderam de fato em %dd: %d deals, US$ %.0f" % (
    sum(x["price"] for x in rows), sum(x["price"] for x in live), sum(x["price"] for x in rows if x["stale"]), sum(x["ev"] for x in rows),
    min(H, (date(2017,12,31)-DREF).days+1), sum(x["won30"] for x in rows), sum(x["val30"] for x in rows)))
print("chance por faixa de idade nesta data:", {("%d-%d" % ((AGEB[i-1]+1 if i else 0), AGEB[i]) if i < len(AGEB) else "139+"): "%.0f%% (n=%d, %s)" % (100*chance(AGEB[i] if i < len(AGEB) else 999)[0], chance(AGEB[i] if i < len(AGEB) else 999)[1], chance(AGEB[i] if i < len(AGEB) else 999)[3]) for i in range(len(AGEB)+1)})
bys = defaultdict(list)
for x in rows: bys[x["s"]].append(x)
if not WHO:
    print("%-20s %-16s %-8s %4s %4s %4s %4s %4s %9s %9s %9s | top10 score: vendas/receita | top10 valor: vendas/receita" % ("vendedor", "gestor", "regiao", "ab", "que", "mor", "fri", "sd", "declarado", "vivo", "esperado"))
    for s in sorted(bys, key=lambda s: (teams[s]["regional_office"], teams[s]["manager"], s)):
        g = bys[s]; c = Counter(x["band"] for x in g)
        t1 = sorted(g, key=lambda x: (-(x["ev"]), x["id"]))[:10]; t2 = sorted(g, key=lambda x: (-x["price"], x["id"]))[:10]
        print("%-20s %-16s %-8s %4d %4d %4d %4d %4d %9.0f %9.0f %9.0f | %d / %6.0f | %d / %6.0f | GTK %d" % (
            s[:20], teams[s]["manager"], teams[s]["regional_office"], len(g), c["quente"], c["morno"], c["frio"], c["sem desfecho"],
            sum(x["price"] for x in g), sum(x["price"] for x in g if not x["stale"]), sum(x["ev"] for x in g),
            sum(x["won30"] for x in t1), sum(x["val30"] for x in t1), sum(x["won30"] for x in t2), sum(x["val30"] for x in t2),
            sum(1 for x in g if x["prod"] == "GTK 500")))
else:
    g = sorted(bys[WHO], key=lambda x: (-(x["score"] or -1), -x["ev"], x["id"]))
    c = Counter(x["band"] for x in g)
    print("VENDEDOR %s | gestor %s | regional %s" % (WHO, teams[WHO]["manager"], teams[WHO]["regional_office"]))
    print("abertos %d | quente %d morno %d frio %d sem desfecho %d | declarado US$ %.0f | vivo US$ %.0f | sem desfecho US$ %.0f | esperado 30d US$ %.0f" % (
        len(g), c["quente"], c["morno"], c["frio"], c["sem desfecho"], sum(x["price"] for x in g), sum(x["price"] for x in g if not x["stale"]),
        sum(x["price"] for x in g if x["stale"]), sum(x["ev"] for x in g)))
    cl = [r for r in pipe if r["sales_agent"] == WHO and r["c"] and r["c"] < DREF]
    w = sum(1 for r in cl if r["won"]); l = len(cl)-w; sd = c["sem desfecho"]
    print("historico ate a data: won %d lost %d | taxa oficial %.1f%% | contando sem desfecho %.1f%%" % (w, l, 100.0*w/(w+l), 100.0*w/(w+l+sd)))
    print("score band  produto          cliente(campo)        preco  idade chance  base(n,nivel)   esperado | desfecho real")
    for x in g[:40]:
        print("%5s %-12s %-16s %-20s %6.0f %5d %5.0f%%  %5d %-7s %8.0f | %s %s %s" % (
            "-" if x["score"] is None else x["score"], x["band"], x["prod"], (x["acc"] or "(vazio)")[:20], x["price"], x["age"], 100*x["p"], x["n"], x["lvl"], x["ev"],
            x["final"], x["c"], ("US$ %.0f" % x["val"]) if x["val"] else ""))
    print("... sem desfecho: %d deals; mais antigos:" % c["sem desfecho"])
    for x in sorted([x for x in g if x["stale"]], key=lambda x: -x["age"])[:6]:
        print("      %-16s %-20s %6.0f %4d dias (desde %s)" % (x["prod"], (x["acc"] or "(vazio)")[:20], x["price"], x["age"], x["e"]))
    t1 = sorted(g, key=lambda x: (-(x["ev"]), x["id"]))[:10]; t2 = sorted(g, key=lambda x: (-x["price"], x["id"]))[:10]
    print("PROVA top10 por score: %d vendas, US$ %.0f | top10 por valor: %d vendas, US$ %.0f | todas as vendas do vendedor no periodo: %d, US$ %.0f" % (
        sum(x["won30"] for x in t1), sum(x["val30"] for x in t1), sum(x["won30"] for x in t2), sum(x["val30"] for x in t2), sum(x["won30"] for x in g), sum(x["val30"] for x in g)))
    print("top10 por valor:", [(x["prod"], x["age"], "sd" if x["stale"] else x["score"], x["final"]) for x in t2])
    mgr = teams[WHO]["manager"]
    print("TIME de %s:" % mgr)
    for s in sorted(bys):
        if teams[s]["manager"] != mgr: continue
        gg = bys[s]; cc = Counter(x["band"] for x in gg)
        cl = [r for r in pipe if r["sales_agent"] == s and r["c"] and r["c"] < DREF]; w = sum(1 for r in cl if r["won"]); l = len(cl)-w
        print("  %-20s abertos %3d | vivos %3d (quente %2d) | sem desfecho %3d | declarado %7.0f | vivo %7.0f | esperado %6.0f | taxa oficial %.1f%% | real %.1f%% | vendeu em seguida %d (US$ %.0f)" % (
            s, len(gg), len(gg)-cc["sem desfecho"], cc["quente"], cc["sem desfecho"], sum(x["price"] for x in gg), sum(x["price"] for x in gg if not x["stale"]),
            sum(x["ev"] for x in gg), 100.0*w/(w+l), 100.0*w/(w+l+cc["sem desfecho"]), sum(x["won30"] for x in gg), sum(x["val30"] for x in gg)))
