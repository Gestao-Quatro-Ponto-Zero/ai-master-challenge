#!/usr/bin/env python3
# Numeros exatos para as telas de Transparencia e Qualidade dos dados. So stdlib. Uso: python3 -I cal.py <dados>
import csv, os, sys
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
DD = sys.argv[1]
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip(); return datetime.strptime(s, "%Y-%m-%d").date() if s else None
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
accs = {r["account"]: r for r in load("accounts.csv")}
P = load("sales_pipeline.csv")
for r in P:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["won"] = r["deal_stage"] == "Won"; r["acc"] = r["account"].strip()
    r["reg"] = teams[r["sales_agent"]]["regional_office"]
closed = [r for r in P if r["c"]]
print("== fechamentos por mes do trimestre (1o, 2o, 3o) ==")
for mo in (0, 1, 2):
    g = [r for r in closed if (r["c"].month-1) % 3 == mo]
    w = sum(1 for r in g if r["won"]); cyc = [(r["c"]-r["e"]).days for r in g]
    print("  mes %d do trimestre: fechamentos %4d | vendas %4d (%.1f%%) | ciclo max %3d | com ciclo > 30 dias: %d | meses: %s" % (
        mo+1, len(g), w, 100.0*w/len(g), max(cyc), sum(1 for c in cyc if c > 30), sorted({r["c"].strftime("%Y-%m") for r in g})))
g = [r for r in closed if (r["c"].month-1) % 3 != 2]; print("  meses 1 e 2 juntos: fechamentos %d | vendas %.1f%%" % (len(g), 100.0*sum(1 for r in g if r["won"])/len(g)))
print("== deals com mais de 30 dias abertos no 1o dia do 1o mes de cada trimestre, e quantos fecharam naquele mes ==")
tot = totc = 0
for (y, m) in ((2017, 4), (2017, 7), (2017, 10)):
    d0 = date(y, m, 1); d1 = date(y, m+1, 1)
    op = [r for r in P if r["e"] and r["e"] < d0 and (r["c"] is None or r["c"] >= d0) and (d0-r["e"]).days > 30]
    cl = [r for r in op if r["c"] and r["c"] < d1]
    tot += len(op); totc += len(cl)
    print("  %d-%02d: abertos com >30 dias %4d | fecharam no mes %d" % (y, m, len(op), len(cl)))
print("  total: %d | fecharam %d" % (tot, totc))
print("== vendas com ciclo curto ==")
won = [r for r in closed if r["won"]]; cyc = sorted((r["c"]-r["e"]).days for r in won)
print("  vendas %d | ciclo <=14: %.1f%% | >60: %.1f%% | mediana %d | max %d" % (len(won), 100.0*sum(1 for c in cyc if c <= 14)/len(cyc), 100.0*sum(1 for c in cyc if c > 60)/len(cyc), cyc[len(cyc)//2], cyc[-1]))
print("  maior ciclo entre TODOS os fechados (venda ou perda):", max((r["c"]-r["e"]).days for r in closed), "| primeiro fechamento:", min(r["c"] for r in closed), "| ultimo:", max(r["c"] for r in closed))
print("  primeira e ultima data de entrada:", min(r["e"] for r in P if r["e"]), max(r["e"] for r in P if r["e"]))
print("  deals com entrada antes de 2017-03-01: %d | destes, fechados: %d | abertos: %d" % (
    sum(1 for r in P if r["e"] and r["e"] < date(2017,3,1)), sum(1 for r in P if r["e"] and r["e"] < date(2017,3,1) and r["c"]), sum(1 for r in P if r["e"] and r["e"] < date(2017,3,1) and not r["c"])))
print("== cliente do deal x regional do vendedor ==")
home = defaultdict(Counter)
for r in closed: home[r["acc"]][r["reg"]] += 1
hm = {a: c.most_common(1)[0][0] for a, c in home.items()}
one = sum(1 for a, c in home.items() if len(c) == 1)
print("  clientes com fechados: %d | atendidos por uma so regional: %d" % (len(home), one))
ok = sum(1 for r in closed if hm[r["acc"]] == r["reg"]); print("  fechados cuja regional do vendedor = regional principal do cliente: %d de %d (%.1f%%)" % (ok, len(closed), 100.0*ok/len(closed)))
op = [r for r in P if not r["c"]]; opa = [r for r in op if r["acc"]]
ok2 = sum(1 for r in opa if hm.get(r["acc"]) == r["reg"])
print("  abertos %d | sem cliente %d (%.1f%%) | com cliente %d | destes, regional bate: %d (%.1f%%)" % (len(op), len(op)-len(opa), 100.0*(len(op)-len(opa))/len(op), len(opa), ok2, 100.0*ok2/len(opa)))
print("== campos vazios ==")
for f in ("account", "engage_date", "close_date", "close_value"):
    print("  %-12s vazio em %d de %d" % (f, sum(1 for r in P if not r[f].strip()), len(P)))
print("  estagios:", dict(Counter(r["deal_stage"] for r in P)))
print("  close_value dos Lost:", dict(Counter(r["close_value"] for r in P if r["deal_stage"] == "Lost")))
print("  produtos no pipeline que nao batem com products.csv:", sorted({r["product"] for r in P} - {x["product"] for x in load("products.csv")}))
print("  setores:", sorted({a["sector"] for a in accs.values()}))
print("  sedes fora do padrao:", sorted({a["office_location"] for a in accs.values() if "Phil" in a["office_location"]}))
print("  vendedores sem nenhum deal:", sorted(set(teams) - {r["sales_agent"] for r in P}))
D = date(2017, 12, 4)
S = [r for r in P if r["e"] and r["e"] < D and (r["c"] is None or r["c"] >= D)]
st = [r for r in S if (D-r["e"]).days > 138]
print("== 4 dez 2017: abertos %d | sem desfecho %d (%.1f%%) | vivos %d ==" % (len(S), len(st), 100.0*len(st)/len(S), len(S)-len(st)))
print("  por regional (abertos / sem desfecho):", {reg: (sum(1 for r in S if r["reg"] == reg), sum(1 for r in st if r["reg"] == reg)) for reg in ("Central", "East", "West")})
print("  prospeccao (sem data de entrada) por regional:", dict(Counter(r["reg"] for r in P if r["deal_stage"] == "Prospecting")))
