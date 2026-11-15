#!/usr/bin/env python3
# O campo cliente (account) dos deals abertos denuncia o futuro quando simulamos uma data passada?
# E dados do painel do cliente escolhido na data de referencia. So stdlib. Uso: python3 -I leak.py <dados> [cliente]
import bisect, csv, os, sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date
DD = sys.argv[1]; DREF = date(2017, 12, 4); H = 30; END = date(2017, 12, 31)
PICK = sys.argv[2] if len(sys.argv) > 2 else "Mathtouch"
MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
def fd(d): return "%d %s" % (d.day, MES[d.month-1])
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
allp = load("sales_pipeline.csv")
for r in allp:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["pname"] = r["product"].replace("GTXPro", "GTX Pro")
    r["price"] = prod[r["pname"]]; r["won"] = r["deal_stage"] == "Won"; r["val"] = float(r["close_value"]) if r["won"] else 0.0
    r["acc"] = r["account"].strip(); r["reg"] = teams[r["sales_agent"]]["regional_office"]
pipe = [r for r in allp if r["e"]]

print("== A. todo deal fechado tem cliente? ==")
for st in ("Won", "Lost", "Engaging", "Prospecting"):
    g = [r for r in allp if r["deal_stage"] == st]
    print("  %-11s n %4d | com cliente %4d (%.1f%%)" % (st, len(g), sum(1 for r in g if r["acc"]), 100.0*sum(1 for r in g if r["acc"])/len(g)))

def snap(d):
    return [r for r in pipe if r["e"] < d and (r["c"] is None or r["c"] >= d)]
def fate(r, d, horizon=None):
    lim = END if horizon is None else d + timedelta(days=horizon-1)
    if r["c"] and r["c"] <= lim:
        return "venda" if r["won"] else "perda"
    return "aberto"

print()
print("== B. abertos em 4 dez 2017: ter cliente x o que aconteceu ate 31 dez ==")
S = snap(DREF)
for lab, sel in (("todos", S), ("vivos (<=138 dias)", [r for r in S if (DREF-r["e"]).days <= 138]), ("sem desfecho (>138)", [r for r in S if (DREF-r["e"]).days > 138])):
    print("  %s: n %d" % (lab, len(sel)))
    for has in (True, False):
        g = [r for r in sel if bool(r["acc"]) == has]
        c = Counter(fate(r, DREF) for r in g)
        if g:
            print("     %-11s n %4d | venda %4d (%.1f%%) | perda %4d (%.1f%%) | segue aberto %4d (%.1f%%)" % (
                "com cliente" if has else "sem cliente", len(g), c["venda"], 100.0*c["venda"]/len(g), c["perda"], 100.0*c["perda"]/len(g), c["aberto"], 100.0*c["aberto"]/len(g)))

print()
print("== C. o mesmo nas 22 segundas da prova (3 jul a 27 nov), desfecho em 30 dias, so vivos ==")
tot = {True: Counter(), False: Counter()}
d = date(2017, 7, 3)
while d <= date(2017, 11, 27):
    mc = max((r["c"]-r["e"]).days for r in pipe if r["c"] and r["c"] < d)
    for r in snap(d):
        if (d-r["e"]).days > mc: continue
        tot[bool(r["acc"])][fate(r, d, 30)] += 1
    d += timedelta(days=7)
for has in (True, False):
    c = tot[has]; n = sum(c.values())
    print("  %-11s pares deal-data %6d | venda em 30d %5d (%.1f%%) | perda %5d (%.1f%%) | segue aberto %6d (%.1f%%)" % (
        "com cliente" if has else "sem cliente", n, c["venda"], 100.0*c["venda"]/n, c["perda"], 100.0*c["perda"]/n, c["aberto"], 100.0*c["aberto"]/n))
print("  nota: 'sem cliente' numa data simulada = deal que nunca fechou ate o fim da base (aberto ainda em 31 dez).")
never = [r for r in pipe if r["c"] is None]
print("  deals com data de entrada que nunca fecharam: %d | com cliente %d (%.1f%%)" % (len(never), sum(1 for r in never if r["acc"]), 100.0*sum(1 for r in never if r["acc"])/len(never)))

# modelo da data de referencia (igual a mock.py)
AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)
def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim: return i
    return len(AGEB)
def qpos(d):
    qs = date(d.year, 3*((d.month-1)//3)+1, 1); return (d-qs).days//7, (d.month-1) % 3
def snapy(d):
    end = d + timedelta(days=H)
    return [(r, (d-r["e"]).days, 1 if (r["won"] and r["c"] < end) else 0) for r in pipe if r["e"] < d and (r["c"] is None or r["c"] >= d)]
mondays = []; d = date(2017, 3, 6)
while d <= date(2017, 12, 25): mondays.append(d); d += timedelta(days=7)
c_wk = defaultdict(lambda: [0, 0]); c_mo = defaultdict(lambda: [0, 0]); c_age = defaultdict(lambda: [0, 0]); tt = [0, 0]
for m in mondays:
    if m + timedelta(days=H) > DREF: continue
    wk, mo = qpos(m)
    for r, age, y in snapy(m):
        b = ageb(age)
        for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
            tab[key][0] += y; tab[key][1] += 1
        tt[0] += y; tt[1] += 1
maxc = max((r["c"]-r["e"]).days for r in pipe if r["c"] and r["c"] < DREF)
def chance(age):
    b = ageb(age); wk, mo = qpos(DREF)
    for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
        y, n = tab.get(key, (0, 0))
        if n >= 30: return y/float(n), n, y
    return tt[0]/float(tt[1]), tt[1], tt[0]
rows = []
for r, age, y in snapy(DREF):
    p, n, yy = chance(age); stale = age > maxc
    rows.append(dict(r=r, age=age, stale=stale, p=0.0 if stale else p, n=n, y=yy, ev=0.0 if stale else p*r["price"]))
evs = sorted(x["ev"] for x in rows if not x["stale"])
for x in rows:
    x["score"] = None if x["stale"] else int(round(100.0*bisect.bisect_right(evs, x["ev"])/len(evs)))

print()
print("== D. Daniell Hammack em 4 dez: vivos com e sem cliente x desfecho ate 31 dez ==")
mine = [x for x in rows if x["r"]["sales_agent"] == "Daniell Hammack" and not x["stale"]]
for has in (True, False):
    g = [x for x in mine if bool(x["r"]["acc"]) == has]; c = Counter(fate(x["r"], DREF) for x in g)
    print("  %-11s n %2d | venda %2d | perda %2d | segue aberto %2d | quentes (score>=80): %d" % ("com cliente" if has else "sem cliente", len(g), c["venda"], c["perda"], c["aberto"], sum(1 for x in g if x["score"] >= 80)))

print()
print("== E. painel do cliente %s na data de referencia ==" % PICK)
closed = [r for r in allp if r["deal_stage"] in ("Won", "Lost") and r["c"] < DREF and r["acc"] == PICK]
won = [r for r in closed if r["won"]]
print("  fechados ate 3 dez: %d | ganhos %d | perdidos %d | valor ganho US$ %.0f | primeira venda %s | ultima venda %s" % (
    len(closed), len(won), len(closed)-len(won), sum(r["val"] for r in won), min(r["c"] for r in won), max(r["c"] for r in won)))
print("  regional dos vendedores nos fechados:", dict(Counter(r["reg"] for r in closed)))
print("  ganhos por produto:", Counter(r["pname"] for r in won).most_common())
print("  valor ganho por produto:", sorted(((p, round(sum(r["val"] for r in won if r["pname"] == p))) for p in {r["pname"] for r in won}), key=lambda t: -t[1]))
op = [x for x in rows if x["r"]["acc"] == PICK]
print("  abertos em 4 dez com este cliente no campo: %d | vivos %d | sem desfecho %d | de outra regional %d" % (
    len(op), sum(1 for x in op if not x["stale"]), sum(1 for x in op if x["stale"]), sum(1 for x in op if x["r"]["reg"] != "East")))
for x in sorted(op, key=lambda x: (x["stale"], -(x["score"] or 0), -x["age"])):
    r = x["r"]
    print("     #%s | %-14s US$ %5.0f | %-18s (%s) | aberto em %s %d, %3d dias | %s | chance %2.0f%% (base %d) | score %s | depois: %s %s %s" % (
        r["opportunity_id"], r["pname"], r["price"], r["sales_agent"], r["reg"], fd(r["e"]), r["e"].year, x["age"], "SEM DESFECHO" if x["stale"] else "vivo",
        100*x["p"], x["n"], x["score"], fate(r, DREF), fd(r["c"]) if r["c"] else "", ("US$ %.0f" % r["val"]) if r["val"] else ""))
pros = [r for r in allp if r["acc"] == PICK and r["deal_stage"] == "Prospecting"]
print("  em prospeccao (sem data de entrada) com este cliente: %d" % len(pros), [(r["opportunity_id"], r["pname"], r["sales_agent"], r["reg"]) for r in pros])
print("  fechados entre 4 e 31 dez com este cliente:", [(r["opportunity_id"], r["pname"], r["sales_agent"], r["deal_stage"], str(r["c"]), r["val"]) for r in allp if r["acc"] == PICK and r["c"] and r["c"] >= DREF])
