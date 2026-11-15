#!/usr/bin/env python3
# Dados reais para as telas novas (kanban, clientes, identificadores, comparacao justa). Data de referencia: 2017-12-04.
import csv, os, sys, random
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date
from statistics import median
DD = sys.argv[1]; DREF = date(2017, 12, 4); WHO = "Daniell Hammack"; H = 30
MES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
def fd(d): return "%d %s" % (d.day, MES[d.month-1])
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
accs = {r["account"]: r for r in load("accounts.csv")}
allp = load("sales_pipeline.csv")
for r in allp:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["pname"] = r["product"].replace("GTXPro", "GTX Pro")
    r["price"] = prod[r["pname"]]; r["won"] = r["deal_stage"] == "Won"; r["val"] = float(r["close_value"]) if r["won"] else 0.0
    r["acc"] = r["account"].strip(); r["reg"] = teams[r["sales_agent"]]["regional_office"]
pipe = [r for r in allp if r["e"]]
AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)
def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim: return i
    return len(AGEB)
def qpos(d):
    qs = date(d.year, 3*((d.month-1)//3)+1, 1); return (d-qs).days//7, (d.month-1) % 3
def snapshot(d):
    end = d + timedelta(days=H)
    return [(r, (d-r["e"]).days, 1 if (r["won"] and r["c"] < end) else 0) for r in pipe if r["e"] < d and (r["c"] is None or r["c"] >= d)]
mondays = []; d = date(2017, 3, 6)
while d <= date(2017, 12, 25): mondays.append(d); d += timedelta(days=7)
c_wk = defaultdict(lambda: [0, 0])
for m in mondays:
    if m + timedelta(days=H) > DREF: continue
    wk, mo = qpos(m)
    for r, age, y in snapshot(m): c_wk[(ageb(age), wk)][0] += y; c_wk[(ageb(age), wk)][1] += 1
def chance(age):
    y, n = c_wk[(ageb(age), qpos(DREF)[0])]; return y/float(n), n, y
mine = []
for r, age, y in snapshot(DREF):
    if r["sales_agent"] != WHO: continue
    stale = age > 138; p, n, yy = chance(age)
    mine.append(dict(r=r, age=age, stale=stale, p=0 if stale else p, ev=0 if stale else p*r["price"], n=n, y=yy))
print("== 1. TOP 12 DO DANIELL com identificador (empate: mais velho primeiro) ==")
live = [x for x in mine if not x["stale"]]
for x in sorted(live, key=lambda x: (-round(x["ev"], 2), -x["age"]))[:12]:
    r = x["r"]
    print("  #%s | %-14s | %-22s | US$ %5.0f | %3d dias | aberto em %s | chance %.0f%% (base %d, vendas %d) | esperado %.0f | depois: %s %s %s" % (
        r["opportunity_id"], r["pname"], r["acc"] or "-", r["price"], x["age"], fd(r["e"]), 100*x["p"], x["n"], x["y"], x["ev"],
        r["deal_stage"], fd(r["c"]) if r["c"] else "", ("US$ %.0f" % r["val"]) if r["val"] else ""))
print()
print("== 2. COMPARACAO JUSTA: top 10 por valor SO ENTRE OS VIVOS (Daniell) ==")
def outcome(sel): return sum(1 for x in sel if x["r"]["won"] and x["r"]["c"] <= date(2017, 12, 31)), sum(x["r"]["val"] for x in sel if x["r"]["won"])
for name, key in (("mais velho primeiro", lambda x: (-x["r"]["price"], -x["age"])), ("mais novo primeiro", lambda x: (-x["r"]["price"], x["age"]))):
    sel = sorted(live, key=key)[:10]
    print("  empate %-20s -> %d vendas, US$ %.0f | %s" % (name, outcome(sel)[0], outcome(sel)[1], [(x["r"]["pname"], x["age"], x["r"]["deal_stage"]) for x in sel]))
rng = random.Random(1); tw = tv = 0.0
for _ in range(20000):
    sel = sorted(live, key=lambda x: (-x["r"]["price"], rng.random()))[:10]; w, v = outcome(sel); tw += w; tv += v
print("  empate aleatorio (20000 sorteios) -> esperado %.2f vendas, US$ %.0f" % (tw/20000, tv/20000))
sel = sorted(live, key=lambda x: (-round(x["ev"], 2), -x["age"]))[:10]
print("  pelo score (empate mais velho)   -> %d vendas, US$ %.0f" % outcome(sel))
print()
print("== 3. KANBAN DO DANIELL em 4 dez ==")
stale = [x for x in mine if x["stale"]]
print("  em negociacao vivos: %d (US$ %.0f) | com cliente %d, sem cliente %d" % (len(live), sum(x["r"]["price"] for x in live), sum(1 for x in live if x["r"]["acc"]), sum(1 for x in live if not x["r"]["acc"])))
print("  sem desfecho: %d (US$ %.0f) | com cliente %d, sem cliente %d" % (len(stale), sum(x["r"]["price"] for x in stale), sum(1 for x in stale if x["r"]["acc"]), sum(1 for x in stale if not x["r"]["acc"])))
for x in sorted(stale, key=lambda x: (-x["r"]["price"], -x["age"]))[:5]:
    print("     sd  #%s %-14s %-18s US$ %5.0f %3d dias (aberto em %s %d)" % (x["r"]["opportunity_id"], x["r"]["pname"], x["r"]["acc"] or "-", x["r"]["price"], x["age"], fd(x["r"]["e"]), x["r"]["e"].year))
lo = DREF - timedelta(days=30)
rec = [r for r in allp if r["sales_agent"] == WHO and r["c"] and lo <= r["c"] < DREF]
w = [r for r in rec if r["won"]]; l = [r for r in rec if not r["won"]]
print("  ganhos nos 30 dias antes: %d (US$ %.0f) | perdidos: %d" % (len(w), sum(r["val"] for r in w), len(l)))
for r in sorted(w, key=lambda r: r["c"], reverse=True)[:4]: print("     won #%s %-14s %-18s US$ %5.0f fechado em %s (ciclo %d dias)" % (r["opportunity_id"], r["pname"], r["acc"], r["val"], fd(r["c"]), (r["c"]-r["e"]).days))
for r in sorted(l, key=lambda r: r["c"], reverse=True)[:4]: print("     lost #%s %-14s %-18s tabela US$ %5.0f perdido em %s (ciclo %d dias)" % (r["opportunity_id"], r["pname"], r["acc"], r["price"], fd(r["c"]), (r["c"]-r["e"]).days))
pros = [r for r in allp if r["sales_agent"] == WHO and r["deal_stage"] == "Prospecting"]
print("  prospeccao do Daniell: %d | prospeccao so existe na Central: %s" % (len(pros), dict(Counter(r["reg"] for r in allp if r["deal_stage"] == "Prospecting"))))
print()
print("== 4. CLIENTES (so historico fechado ate 3 dez; regional do cliente = regional dos fechados) ==")
closed = [r for r in allp if r["deal_stage"] in ("Won", "Lost") and r["c"] < DREF]
home = {}
cr = defaultdict(Counter)
for r in closed: cr[r["acc"]][r["reg"]] += 1
for a, c in cr.items(): home[a] = c.most_common(1)[0][0]
st = {}
for a in accs:
    cl = [r for r in closed if r["acc"] == a]; ww = [r for r in cl if r["won"]]
    op = [r for r in allp if r["acc"] == a and r["deal_stage"] in ("Engaging", "Prospecting")]
    st[a] = dict(n=len(cl), w=len(ww), val=sum(r["val"] for r in ww), last=max([r["c"] for r in ww] or [None]), op=len(op),
                 op_fora=sum(1 for r in op if r["reg"] != home.get(a)), prods=Counter(r["pname"] for r in ww).most_common(3), sellers=len({r["sales_agent"] for r in cl}))
east = sorted([a for a in accs if home.get(a) == "East"], key=lambda a: -st[a]["val"])
print("  clientes por regional principal:", dict(Counter(home.values())))
print("  %-28s %-18s %9s %6s | fech %4s taxa %5s | ganho US$ %8s | ult venda | abertos (fora da regional)" % ("cliente (Leste)", "setor", "fat US$mi", "func", "", "", ""))
for a in east[:12]:
    s = st[a]; A = accs[a]
    print("  %-28s %-18s %9.0f %6s | %4d %5.1f%% | %8.0f | %s | %d (%d)" % (a[:28], A["sector"], float(A["revenue"]), A["employees"], s["n"], 100.0*s["w"]/s["n"], s["val"], fd(s["last"]) if s["last"] else "-", s["op"], s["op_fora"]))
PICK = sys.argv[2] if len(sys.argv) > 2 else east[0]
s = st[PICK]; A = accs[PICK]
print()
print("  CLIENTE ESCOLHIDO:", PICK, dict(A))
print("  fechados %d | ganhos %d | taxa %.1f%% | valor ganho US$ %.0f | ticket medio US$ %.0f | ultima venda %s | vendedores %d | top produtos %s" % (
    s["n"], s["w"], 100.0*s["w"]/s["n"], s["val"], s["val"]/s["w"], s["last"], s["sellers"], s["prods"]))
cl = sorted([r for r in closed if r["acc"] == PICK], key=lambda r: r["c"], reverse=True)
print("  ultimos fechados:")
for r in cl[:8]: print("     #%s %s | %-14s | %-18s | %s | %s | ciclo %d dias" % (r["opportunity_id"], fd(r["c"]), r["pname"], r["sales_agent"], "Ganho US$ %.0f" % r["val"] if r["won"] else "Perdido", r["reg"], (r["c"]-r["e"]).days))
op = [r for r in allp if r["acc"] == PICK and r["deal_stage"] in ("Engaging", "Prospecting")]
print("  em aberto com este cliente no campo: %d | de vendedores de outra regional: %d" % (len(op), sum(1 for r in op if r["reg"] != home[PICK])))
for r in sorted(op, key=lambda r: (r["e"] or date(2099,1,1))):
    print("     #%s %-12s | %-14s | %-18s (%s) | %s" % (r["opportunity_id"], r["deal_stage"], r["pname"], r["sales_agent"], r["reg"], ("aberto em %s %d, %d dias" % (fd(r["e"]), r["e"].year, (DREF-r["e"]).days)) if r["e"] else "sem data"))
print("  por ano-mes de fechamento (ganhos):", dict(sorted(Counter("%d-%02d" % (r["c"].year, r["c"].month) for r in cl if r["won"]).items())))
