#!/usr/bin/env python3
# Relacao vendedor-cliente: e sinal de verdade ou efeito de como o campo "cliente" foi preenchido nos deals abertos?
import csv, os, sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date
from statistics import median, mean
DD = sys.argv[1]
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
def pct(a, b): return 100.0*a/b if b else float("nan")
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["acc"] = r["account"].strip(); r["st"] = r["deal_stage"]
    r["s"] = r["sales_agent"]; r["region"] = teams[r["s"]]["regional_office"]
closed = [r for r in pipe if r["st"] in ("Won", "Lost")]
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
maxcyc = max((r["c"]-r["e"]).days for r in closed); cutoff = ref - timedelta(days=maxcyc)
NACC = len({r["acc"] for r in pipe if r["acc"]})
print("== 1. carteira: cada vendedor atende quantos clientes (deals fechados)? ==")
terr = defaultdict(Counter)
for r in closed: terr[r["s"]][r["acc"]] += 1
sizes = sorted(len(v) for v in terr.values())
exp = []
for s, c in terr.items():
    n = sum(c.values()); exp.append(NACC*(1-(1-1.0/NACC)**n))
print("  clientes distintos por vendedor: min %d mediana %g max %d (de %d) | esperado se fosse ao acaso: mediana %.0f" % (sizes[0], median(sizes), sizes[-1], NACC, median(exp)))
top3 = [pct(sum(x for _, x in c.most_common(3)), sum(c.values())) for c in terr.values()]
print("  parcela dos fechados do vendedor nos seus 3 maiores clientes: mediana %.1f%% (ao acaso seria ~%.1f%%)" % (median(top3), 100*3.0/NACC))
acc_reg = defaultdict(Counter)
for r in closed: acc_reg[r["acc"]][r["region"]] += 1
dom = sorted(pct(max(c.values()), sum(c.values())) for c in acc_reg.values())
print("  parcela dos fechados de cada cliente na sua regional principal: min %.0f%% mediana %.0f%% max %.0f%%" % (dom[0], median(dom), dom[-1]))
print()
print("== 2. 'o vendedor ja tinha ganho neste cliente antes de o deal entrar?' por desfecho ==")
wins = defaultdict(list)   # (vendedor, cliente) -> datas de fechamento dos ganhos
swins = defaultdict(list)  # vendedor -> [(data, cliente)]
for r in closed:
    if r["st"] == "Won":
        wins[(r["s"], r["acc"])].append(r["c"]); swins[r["s"]].append((r["c"], r["acc"]))
def had(r, asof):
    return any(c < asof for c in wins.get((r["s"], r["acc"]), ()))
def book(s, asof):
    return len({a for c, a in swins.get(s, ()) if c < asof})
groups = (("fechados (ganho ou perdido)", [r for r in closed if date(2017, 4, 1) <= r["e"] < cutoff]),
          ("  so ganhos", [r for r in closed if r["st"] == "Won" and date(2017, 4, 1) <= r["e"] < cutoff]),
          ("  so perdidos", [r for r in closed if r["st"] == "Lost" and date(2017, 4, 1) <= r["e"] < cutoff]),
          ("sem desfecho com cliente", [r for r in pipe if r["st"] == "Engaging" and r["acc"] and date(2017, 4, 1) <= r["e"] < cutoff]),
          ("vivos com cliente", [r for r in pipe if r["st"] == "Engaging" and r["acc"] and r["e"] >= cutoff]),
          ("fechados engajados depois de %s" % cutoff, [r for r in closed if r["e"] >= cutoff]))
for name, g in groups:
    obs = pct(sum(1 for r in g if had(r, r["e"])), len(g))
    rnd = mean(100.0*book(r["s"], r["e"])/NACC for r in g)
    print("  %-40s n %4d | vendedor ja tinha ganho ali: %5.1f%% | se o cliente fosse sorteado: %5.1f%%" % (name, len(g), obs, rnd))
pr = [r for r in pipe if r["st"] == "Prospecting" and r["acc"]]
print("  %-40s n %4d | vendedor ja ganhou ali (ate a data de referencia): %5.1f%% | se sorteado: %5.1f%%" % (
    "prospeccao com cliente", len(pr), pct(sum(1 for r in pr if had(r, ref + timedelta(days=1))), len(pr)),
    mean(100.0*book(r["s"], ref + timedelta(days=1))/NACC for r in pr)))
print()
print("== 3. por regional: sem desfecho com x sem relacao previa (deals com cliente, abr a meados de ago) ==")
ev = [r for r in pipe if r["acc"] and r["e"] and date(2017, 4, 1) <= r["e"] < cutoff and r["st"] in ("Won", "Lost", "Engaging")]
for reg in ("Central", "East", "West"):
    g = [r for r in ev if r["region"] == reg]
    a = [r for r in g if had(r, r["e"])]; b = [r for r in g if not had(r, r["e"])]
    print("  %-8s com relacao: %4.1f%% sem desfecho (n=%d) | sem relacao: %4.1f%% (n=%d)" % (
        reg, pct(sum(1 for r in a if r["st"] == "Engaging"), len(a)), len(a), pct(sum(1 for r in b if r["st"] == "Engaging"), len(b)), len(b)))
print("  e ganho x perda (so fechados): com relacao %.1f%% de ganho (n=%d) | sem relacao %.1f%% (n=%d)" % (
    pct(sum(1 for r in ev if r["st"] == "Won" and had(r, r["e"])), sum(1 for r in ev if r["st"] != "Engaging" and had(r, r["e"]))),
    sum(1 for r in ev if r["st"] != "Engaging" and had(r, r["e"])),
    pct(sum(1 for r in ev if r["st"] == "Won" and not had(r, r["e"])), sum(1 for r in ev if r["st"] != "Engaging" and not had(r, r["e"]))),
    sum(1 for r in ev if r["st"] != "Engaging" and not had(r, r["e"]))))
