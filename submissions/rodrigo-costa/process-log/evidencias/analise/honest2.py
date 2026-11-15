#!/usr/bin/env python3
# Segunda rodada: estrutura por time, maiores deals, zona de ultima chamada. So stdlib.
# Uso: python3 -I honest2.py <pasta com os CSV>
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

D = sys.argv[1]


def load(name):
    with open(os.path.join(D, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdate(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma = sum(a) / n
    mb = sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if sa == 0 or sb == 0:
        return float("nan")
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


def tstat(r, n):
    return r * math.sqrt(n - 2) / math.sqrt(1 - r * r) if abs(r) < 1 else float("inf")


def pct(a, b):
    return 100.0 * a / b if b else float("nan")


pipe = load("sales_pipeline.csv")
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
for r in pipe:
    r["e"] = pdate(r["engage_date"])
    r["c"] = pdate(r["close_date"])
    r["prod"] = r["product"].replace("GTXPro", "GTX Pro")
    r["price"] = prod[r["prod"]]
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
won = [r for r in pipe if r["deal_stage"] == "Won"]
lost = [r for r in pipe if r["deal_stage"] == "Lost"]
closed = won + lost
for r in closed:
    r["cyc"] = (r["c"] - r["e"]).days
maxcyc = max(r["cyc"] for r in closed)
cutoff = ref - timedelta(days=maxcyc)
eng = [r for r in pipe if r["deal_stage"] == "Engaging"]
for r in eng:
    r["age"] = (ref - r["e"]).days
    r["st"] = "stale" if r["age"] > maxcyc else "alive"
stale = [r for r in eng if r["st"] == "stale"]
alive = [r for r in eng if r["st"] == "alive"]
prosp = [r for r in pipe if r["deal_stage"] == "Prospecting"]

print("== A. VENDEDOR: time, datas, grupos ==")
A = defaultdict(lambda: dict(W=0, L=0, S=0, A=0, P=0, Wold=0, Lold=0, e=[], c=[]))
for r in pipe:
    a = A[r["sales_agent"]]
    if r["e"]:
        a["e"].append(r["e"])
    if r["c"]:
        a["c"].append(r["c"])
for r in won:
    A[r["sales_agent"]]["W"] += 1
    A[r["sales_agent"]]["Wold"] += r["e"] < cutoff
for r in lost:
    A[r["sales_agent"]]["L"] += 1
    A[r["sales_agent"]]["Lold"] += r["e"] < cutoff
for r in stale:
    A[r["sales_agent"]]["S"] += 1
for r in alive:
    A[r["sales_agent"]]["A"] += 1
for r in prosp:
    A[r["sales_agent"]]["P"] += 1
print("%-20s %-17s %-8s %4s %4s %4s %4s %4s | %-10s %-10s %-10s" % (
    "vendedor", "gestor", "regiao", "W", "L", "S", "A", "P", "1o engaj", "ult engaj", "ult fech"))
for s in sorted(A, key=lambda s: (teams[s]["regional_office"], teams[s]["manager"], s)):
    a = A[s]
    print("%-20s %-17s %-8s %4d %4d %4d %4d %4d | %-10s %-10s %-10s" % (
        s[:20], teams[s]["manager"], teams[s]["regional_office"], a["W"], a["L"], a["S"], a["A"], a["P"],
        min(a["e"]) if a["e"] else "-", max(a["e"]) if a["e"] else "-", max(a["c"]) if a["c"] else "-"))

print()
print("== B. CORRELACOES (taxa oficial x deixar aberto) ==")
sel_all = [s for s in A if A[s]["W"] + A[s]["L"] > 0]
groups = {
    "30 vendedores": sel_all,
    "27 com deals abertos": [s for s in sel_all if A[s]["S"] + A[s]["A"] + A[s]["P"] > 0],
    "17 sem prospeccao (P=0, com abertos)": [s for s in sel_all if A[s]["P"] == 0 and A[s]["S"] > 0],
    "10 com prospeccao (P>0)": [s for s in sel_all if A[s]["P"] > 0],
}
for name, sel in groups.items():
    off = [pct(A[s]["W"], A[s]["W"] + A[s]["L"]) for s in sel]
    ssh = [pct(A[s]["S"], A[s]["Wold"] + A[s]["Lold"] + A[s]["S"]) for s in sel]
    spw = [A[s]["S"] / A[s]["W"] for s in sel]
    n = len(sel)
    r1 = spearman(off, ssh)
    r2 = spearman(off, spw)
    print("%-38s n=%2d | oficial x S/antigos: %+.2f (t=%.2f) | oficial x S/W: %+.2f (t=%.2f) | S/antigos %.1f-%.1f" % (
        name, n, r1, tstat(r1, n), r2, tstat(r2, n), min(ssh), max(ssh)))


def chi2(rows):
    rows = [r for r in rows if sum(r) > 0]
    ta = sum(r[0] for r in rows)
    tb = sum(r[1] for r in rows)
    t = ta + tb
    x = 0.0
    for a, b in rows:
        n = a + b
        x += (a - n * ta / t) ** 2 / (n * ta / t) + (b - n * tb / t) ** 2 / (n * tb / t)
    return x, len(rows) - 1


for name, sel in groups.items():
    x, df = chi2([(A[s]["S"], A[s]["Wold"] + A[s]["Lold"]) for s in sel])
    y, df2 = chi2([(A[s]["W"], A[s]["L"]) for s in sel])
    print("%-38s chi2 parado/antigos %.1f (df %d) | chi2 taxa oficial %.1f (df %d)" % (name, x, df, y, df2))

print()
print("== C. MAIORES DEALS EM NEGOCIACAO (ordenar por valor) ==")
byval = sorted(eng, key=lambda r: (-r["price"], r["opportunity_id"]))
for n in (10, 15, 25, 50, 100, 200):
    top = byval[:n]
    print("top %3d por preco: %3d parados (%.0f%%) | menor preco no corte %.0f" % (
        n, sum(1 for r in top if r["st"] == "stale"), pct(sum(1 for r in top if r["st"] == "stale"), n), top[-1]["price"]))
print("GTK 500 abertos: parados %d vivos %d prospeccao %d | valor parado US$ %.0f" % (
    sum(1 for r in stale if r["prod"] == "GTK 500"), sum(1 for r in alive if r["prod"] == "GTK 500"),
    sum(1 for r in prosp if r["prod"] == "GTK 500"), sum(r["price"] for r in stale if r["prod"] == "GTK 500")))
print("valor total parado US$ %.0f | vivo US$ %.0f" % (sum(r["price"] for r in stale), sum(r["price"] for r in alive)))
# por vendedor: top 10 em negociacao por preco -> quantos parados
perseller = defaultdict(list)
for r in eng:
    perseller[r["sales_agent"]].append(r)
frac = []
for s, lst in perseller.items():
    top = sorted(lst, key=lambda r: (-r["price"], r["opportunity_id"]))[:10]
    frac.append(sum(1 for r in top if r["st"] == "stale"))
frac.sort()
print("top 10 por preco de cada vendedor (%d vendedores): parados min %d mediana %.1f max %d | dist %s" % (
    len(frac), frac[0], median(frac), frac[-1], frac))

print()
print("== D. VIVOS POR FAIXA DE IDADE ==")
for lo, hi in ((0, 30), (31, 60), (61, 90), (91, 110), (111, 138)):
    g = [r for r in alive if lo <= r["age"] <= hi]
    print("%3d-%3d dias: %3d deals | US$ %8.0f" % (lo, hi, len(g), sum(r["price"] for r in g)))
print("vivos ate 90 dias: %d | acima de 90: %d" % (
    sum(1 for r in alive if r["age"] <= 90), sum(1 for r in alive if r["age"] > 90)))

print()
print("== E. REGIAO x MES DE ENGAJAMENTO (W/L/aberto) ==")
M = defaultdict(lambda: defaultdict(lambda: dict(W=0, L=0, O=0)))
for r in pipe:
    if not r["e"]:
        continue
    reg = teams[r["sales_agent"]]["regional_office"]
    k = "%d-%02d" % (r["e"].year, r["e"].month)
    key = {"Won": "W", "Lost": "L", "Engaging": "O"}[r["deal_stage"]]
    M[reg][k][key] += 1
months = sorted({k for reg in M for k in M[reg]})
print("%-8s" % "mes" + "".join("  %-22s" % reg for reg in sorted(M)))
for k in months:
    line = "%-8s" % k
    for reg in sorted(M):
        a = M[reg][k]
        n = a["W"] + a["L"] + a["O"]
        line += "  n%4d ab %3d (%4.1f%%)   " % (n, a["O"], pct(a["O"], n))
    print(line)
print("prospeccao por regiao:", {reg: sum(1 for r in prosp if teams[r["sales_agent"]]["regional_office"] == reg)
                                 for reg in sorted(M)})
print("prospeccao por gestor:", dict(sorted(defaultdict(int, {
    m: sum(1 for r in prosp if teams[r["sales_agent"]]["manager"] == m)
    for m in {t["manager"] for t in teams.values()}}).items())))

print()
print("== F. FECHAMENTOS RECENTES POR REGIAO (ultimos 60 dias) ==")
for reg in sorted(M):
    g = [r for r in closed if teams[r["sales_agent"]]["regional_office"] == reg and (ref - r["c"]).days <= 60]
    print("%-8s fechados nos ultimos 60 dias: %4d (won %d)" % (reg, len(g), sum(1 for r in g if r["deal_stage"] == "Won")))
