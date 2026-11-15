#!/usr/bin/env python3
# Confere se a ausencia de fechamentos antes de 2017-03-01 distorce a coorte madura e a curva por idade.
import csv, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from statistics import median
D = sys.argv[1]
def load(n):
    with open(os.path.join(D, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"])
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
closed = [r for r in pipe if r["deal_stage"] in ("Won", "Lost")]
for r in closed: r["cyc"] = (r["c"] - r["e"]).days
maxcyc = max(r["cyc"] for r in closed)
cutoff = ref - timedelta(days=maxcyc)
first_close = min(r["c"] for r in closed)
print("primeiro fechamento", first_close, "| primeiro engajamento", min(r["e"] for r in pipe if r["e"]), "| ref", ref, "| cutoff", cutoff)
print("fechamentos por mes:", dict(sorted(Counter("%d-%02d" % (r["c"].year, r["c"].month) for r in closed).items())))
print()
print("menor ciclo observado por mes de engajamento (se > 0 nos primeiros meses, ha truncamento a esquerda):")
by = defaultdict(list)
for r in closed: by["%d-%02d" % (r["e"].year, r["e"].month)].append(r["cyc"])
for k in sorted(by):
    v = sorted(by[k]); print("  %s n %4d | ciclo min %3d p10 %3d mediana %3d max %3d | <=14d: %4.1f%%" % (
        k, len(v), v[0], v[len(v)//10], median(v), v[-1], 100.0*sum(1 for x in v if x <= 14)/len(v)))
def cohort(lo, hi, name):
    W = [r for r in closed if r["deal_stage"] == "Won" and lo <= r["e"] < hi]
    L = [r for r in closed if r["deal_stage"] == "Lost" and lo <= r["e"] < hi]
    S = [r for r in pipe if r["deal_stage"] == "Engaging" and lo <= r["e"] < hi]
    n = len(W) + len(L) + len(S)
    print()
    print("COORTE %s: n %d | won %d (%.1f%%) lost %d (%.1f%%) ainda aberto %d (%.1f%%) | taxa oficial %.1f%%" % (
        name, n, len(W), 100.0*len(W)/n, len(L), 100.0*len(L)/n, len(S), 100.0*len(S)/n, 100.0*len(W)/(len(W)+len(L))))
    print("   t | so fechados (n) | contando abertos (n) | fecha como won em 30d (contando abertos)")
    for t in (0, 7, 14, 30, 45, 60, 75, 90, 100, 110, 120, 130):
        w = sum(1 for r in W if r["cyc"] > t); l = sum(1 for r in L if r["cyc"] > t)
        w30 = sum(1 for r in W if t < r["cyc"] <= t + 30)
        tot = w + l + len(S)
        print(" %3d | %5.1f%% (%4d) | %5.1f%% (%4d) | %5.1f%%" % (t, 100.0*w/(w+l) if w+l else float('nan'), w+l, 100.0*w/tot, tot, 100.0*w30/tot))
    print("   histograma do ciclo (won/lost):")
    for a, b in ((0,7),(8,14),(15,30),(31,45),(46,60),(61,75),(76,90),(91,105),(106,120),(121,138)):
        w = sum(1 for r in W if a <= r["cyc"] <= b); l = sum(1 for r in L if a <= r["cyc"] <= b)
        print("     %3d-%3d: won %4d lost %4d | taxa %5.1f%%" % (a, b, w, l, 100.0*w/(w+l) if w+l else float('nan')))
cohort(date(2000,1,1), cutoff, "madura inteira (antes de %s)" % cutoff)
cohort(first_close, cutoff, "sem truncamento (%s a %s)" % (first_close, cutoff))
cohort(date(2000,1,1), first_close, "truncada (antes de %s)" % first_close)
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
print()
print("% ainda aberto por regional, so meses sem truncamento (2017-03 a 2017-07):")
M = defaultdict(lambda: defaultdict(lambda: [0, 0]))
for r in pipe:
    if not r["e"]: continue
    k = "%d-%02d" % (r["e"].year, r["e"].month)
    if not ("2017-03" <= k <= "2017-07"): continue
    reg = teams[r["sales_agent"]]["regional_office"]
    M[reg][k][0] += 1; M[reg][k][1] += r["deal_stage"] == "Engaging"
for reg in sorted(M):
    print("  %-8s" % reg, " ".join("%s %.1f%%" % (k, 100.0*M[reg][k][1]/M[reg][k][0]) for k in sorted(M[reg])))
