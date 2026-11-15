#!/usr/bin/env python3
# Testa a hipotese "deal parado = perda escondida" direto no CSV bruto. So stdlib.
# Uso: python3 -I honest.py <pasta com os CSV>
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


def chi2_sf(x, k):
    """P(chi2_k > x) pela gama incompleta regularizada (serie / fracao continuada)."""
    a = k / 2.0
    x2 = x / 2.0
    if x2 <= 0:
        return 1.0
    lg = -x2 + a * math.log(x2) - math.lgamma(a)
    if x2 < a + 1:
        term = 1.0 / a
        s = term
        n = 1
        while abs(term) > 1e-15 * abs(s) and n < 100000:
            term *= x2 / (a + n)
            s += term
            n += 1
        return max(0.0, 1.0 - s * math.exp(lg))
    tiny = 1e-300
    b = x2 + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 100000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return h * math.exp(lg)


def chi2_table(rows):
    rows = [r for r in rows if sum(r) > 0]
    ta = sum(r[0] for r in rows)
    tb = sum(r[1] for r in rows)
    t = ta + tb
    x = 0.0
    for a, b in rows:
        n = a + b
        ea = n * ta / t
        eb = n * tb / t
        x += (a - ea) ** 2 / ea + (b - eb) ** 2 / eb
    df = len(rows) - 1
    return x, df, chi2_sf(x, df)


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


def pct(a, b):
    return 100.0 * a / b if b else float("nan")


def quant(v, q):
    v = sorted(v)
    if not v:
        return float("nan")
    i = min(len(v) - 1, max(0, int(round(q * (len(v) - 1)))))
    return v[i]


pipe = load("sales_pipeline.csv")
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}

for r in pipe:
    r["e"] = pdate(r["engage_date"])
    r["c"] = pdate(r["close_date"])
    p = r["product"]
    r["price"] = prod.get(p, prod.get(p.replace("GTXPro", "GTX Pro")))

ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
won = [r for r in pipe if r["deal_stage"] == "Won"]
lost = [r for r in pipe if r["deal_stage"] == "Lost"]
closed = won + lost
for r in closed:
    r["cyc"] = (r["c"] - r["e"]).days
maxcyc = max(r["cyc"] for r in closed)
cutoff = ref - timedelta(days=maxcyc)  # engajado antes disso => idade > maxcyc
eng_all = [r for r in pipe if r["deal_stage"] == "Engaging"]
eng = [r for r in eng_all if r["e"] is not None]
for r in eng:
    r["age"] = (ref - r["e"]).days
stale = [r for r in eng if r["age"] > maxcyc]
alive = [r for r in eng if r["age"] <= maxcyc]
prosp = [r for r in pipe if r["deal_stage"] == "Prospecting"]

print("== 1. GERAL ==")
print("ref", ref, "| maxcyc", maxcyc, "| cutoff", cutoff)
print("won", len(won), "lost", len(lost), "engaging", len(eng_all), "(sem data:", len(eng_all) - len(eng), ")",
      "stale", len(stale), "alive", len(alive), "prosp", len(prosp))
W, L, S = len(won), len(lost), len(stale)
print("taxa oficial  W/(W+L)      = %.1f%%" % pct(W, W + L))
print("taxa honesta  W/(W+L+S)    = %.1f%%" % pct(W, W + L + S))
print("mortos nunca encerrados S/(L+S) = %.1f%%" % pct(S, L + S))
ages = [r["age"] for r in stale]
print("idade dos parados: min %d p10 %d mediana %d p90 %d max %d" % (
    min(ages), quant(ages, .1), median(ages), quant(ages, .9), max(ages)))
aa = [r["age"] for r in alive]
print("idade dos vivos:   min %d p10 %d mediana %d p90 %d max %d" % (
    min(aa), quant(aa, .1), median(aa), quant(aa, .9), max(aa)))

print()
print("== 2. POR VENDEDOR ==")
A = defaultdict(lambda: dict(W=0, L=0, S=0, A=0, P=0, Wold=0, Lold=0))
for r in won:
    A[r["sales_agent"]]["W"] += 1
    if r["e"] < cutoff:
        A[r["sales_agent"]]["Wold"] += 1
for r in lost:
    A[r["sales_agent"]]["L"] += 1
    if r["e"] < cutoff:
        A[r["sales_agent"]]["Lold"] += 1
for r in stale:
    A[r["sales_agent"]]["S"] += 1
for r in alive:
    A[r["sales_agent"]]["A"] += 1
for r in prosp:
    A[r["sales_agent"]]["P"] += 1

sellers = [s for s in A if A[s]["W"] + A[s]["L"] > 0]
rows = []
for s in sellers:
    a = A[s]
    off = pct(a["W"], a["W"] + a["L"])
    hon = pct(a["W"], a["W"] + a["L"] + a["S"])
    unb = pct(a["S"], a["L"] + a["S"])
    old = a["Wold"] + a["Lold"] + a["S"]
    ssh = pct(a["S"], old)
    rows.append(dict(s=s, off=off, hon=hon, unb=unb, ssh=ssh, **a))
ro = ranks([-r["off"] for r in rows])
rh = ranks([-r["hon"] for r in rows])
for r, x, y in zip(rows, ro, rh):
    r["ro"] = x
    r["rh"] = y
rows.sort(key=lambda r: r["rh"])
print("%-22s %5s %5s %5s %5s %5s | %6s %6s | %4s %4s %4s | %6s %6s" % (
    "vendedor", "W", "L", "S", "A", "P", "ofic%", "hon%", "rO", "rH", "d", "S/(L+S)", "S/antigos"))
for r in rows:
    print("%-22s %5d %5d %5d %5d %5d | %6.1f %6.1f | %4.0f %4.0f %+4.0f | %6.1f %6.1f" % (
        r["s"][:22], r["W"], r["L"], r["S"], r["A"], r["P"], r["off"], r["hon"],
        r["ro"], r["rh"], r["ro"] - r["rh"], r["unb"], r["ssh"]))
off = [r["off"] for r in rows]
hon = [r["hon"] for r in rows]
ssh = [r["ssh"] for r in rows]
unb = [r["unb"] for r in rows]
print("faixa oficial %.1f-%.1f | honesta %.1f-%.1f | S/antigos %.1f-%.1f | S/(L+S) %.1f-%.1f" % (
    min(off), max(off), min(hon), max(hon), min(ssh), max(ssh), min(unb), max(unb)))
print("spearman(oficial, honesta) = %.2f" % spearman(off, hon))
print("spearman(oficial, S/antigos) = %.2f  (positivo = quem esconde mais parece melhor)" % spearman(off, ssh))
print("spearman(oficial, S/(L+S)) = %.2f" % spearman(off, unb))
print("mudam >=5 posicoes: %d de %d | >=10: %d" % (
    sum(1 for r in rows if abs(r["ro"] - r["rh"]) >= 5), len(rows),
    sum(1 for r in rows if abs(r["ro"] - r["rh"]) >= 10)))
print("chi2 oficial (W vs L):        %.1f df %d p=%.4f" % chi2_table([(r["W"], r["L"]) for r in rows]))
print("chi2 honesta (W vs L+S):      %.1f df %d p=%.2g" % chi2_table([(r["W"], r["L"] + r["S"]) for r in rows]))
print("chi2 parado/antigos (S vs resolvidos antigos): %.1f df %d p=%.2g" % chi2_table(
    [(r["S"], r["Wold"] + r["Lold"]) for r in rows]))
print("chi2 nao-encerrado (S vs L):  %.1f df %d p=%.2g" % chi2_table([(r["S"], r["L"]) for r in rows]))
allreg = set(teams)
print("cadastrados %d | com fechados %d | sem nenhum deal: %s" % (
    len(allreg), len(sellers), sorted(allreg - set(A))))
print("com fechados mas sem abertos:", sorted(s for s in sellers if A[s]["S"] + A[s]["A"] + A[s]["P"] == 0))
print("com S == 0:", sorted(s for s in sellers if A[s]["S"] == 0))

print()
print("== 3. POR GESTOR / REGIONAL ==")
for key in ("manager", "regional_office"):
    G = defaultdict(lambda: dict(W=0, L=0, S=0, A=0, old=0))
    for r in rows:
        g = teams[r["s"]][key]
        G[g]["W"] += r["W"]
        G[g]["L"] += r["L"]
        G[g]["S"] += r["S"]
        G[g]["A"] += r["A"]
        G[g]["old"] += r["Wold"] + r["Lold"] + r["S"]
    for g, a in sorted(G.items()):
        print("%-18s W %4d L %4d S %4d A %4d | ofic %.1f hon %.1f | S/antigos %.1f | S/(L+S) %.1f" % (
            g, a["W"], a["L"], a["S"], a["A"], pct(a["W"], a["W"] + a["L"]),
            pct(a["W"], a["W"] + a["L"] + a["S"]), pct(a["S"], a["old"]), pct(a["S"], a["L"] + a["S"])))
    print("  chi2 parado/antigos: %.1f df %d p=%.2g" % chi2_table(
        [(a["S"], a["old"] - a["S"]) for a in G.values()]))

print()
print("== 4. POR PRODUTO ==")
P = defaultdict(lambda: dict(W=0, L=0, S=0, A=0, old=0, price=0))
for r in pipe:
    k = r["product"].replace("GTXPro", "GTX Pro")
    P[k]["price"] = r["price"]
for r in won:
    k = r["product"].replace("GTXPro", "GTX Pro")
    P[k]["W"] += 1
    P[k]["old"] += r["e"] < cutoff
for r in lost:
    k = r["product"].replace("GTXPro", "GTX Pro")
    P[k]["L"] += 1
    P[k]["old"] += r["e"] < cutoff
for r in stale:
    k = r["product"].replace("GTXPro", "GTX Pro")
    P[k]["S"] += 1
    P[k]["old"] += 1
for r in alive:
    k = r["product"].replace("GTXPro", "GTX Pro")
    P[k]["A"] += 1
for k, a in sorted(P.items(), key=lambda kv: kv[1]["price"]):
    print("%-16s preco %7.0f | W %4d L %4d S %4d A %4d | ofic %.1f hon %.1f | S/antigos %.1f" % (
        k, a["price"], a["W"], a["L"], a["S"], a["A"], pct(a["W"], a["W"] + a["L"]),
        pct(a["W"], a["W"] + a["L"] + a["S"]), pct(a["S"], a["old"])))
print("  chi2 parado/antigos: %.1f df %d p=%.2g" % chi2_table([(a["S"], a["old"] - a["S"]) for a in P.values()]))

print()
print("== 5. SEM CONTA VINCULADA ==")
for name, grp in (("won", won), ("lost", lost), ("alive", alive), ("stale", stale), ("prosp", prosp)):
    n = sum(1 for r in grp if not (r["account"] or "").strip())
    print("%-6s %4d de %4d = %.1f%%" % (name, n, len(grp), pct(n, len(grp))))

print()
print("== 6. CADASTRO TARDIO (ciclos curtissimos) ==")
for t in (0, 1, 3, 7):
    w = sum(1 for r in won if r["cyc"] <= t)
    l = sum(1 for r in lost if r["cyc"] <= t)
    print("ciclo <= %d dias: won %4d (%.1f%% dos won) lost %4d (%.1f%% dos lost) | taxa %.1f%%" % (
        t, w, pct(w, len(won)), l, pct(l, len(lost)), pct(w, w + l)))

print()
print("== 7. SOBREVIVENCIA: ingenuo x honesto ==")
print("taxa por faixa de ciclo (so fechados):")
for lo, hi in ((0, 7), (8, 14), (15, 30), (31, 60), (61, 90), (91, 200)):
    w = sum(1 for r in won if lo <= r["cyc"] <= hi)
    l = sum(1 for r in lost if lo <= r["cyc"] <= hi)
    print("  %3d-%3d dias: n %4d taxa %.1f%%" % (lo, hi, w + l, pct(w, w + l)))
coh_w = [r for r in won if r["e"] < cutoff]
coh_l = [r for r in lost if r["e"] < cutoff]
print("coorte madura (engajados antes de %s): won %d lost %d parados %d | nunca fecharam %.1f%%" % (
    cutoff, len(coh_w), len(coh_l), len(stale), pct(len(stale), len(coh_w) + len(coh_l) + len(stale))))
print("dado que o deal ainda esta aberto aos t dias, chance de virar venda:")
print("  %4s | %8s %6s | %8s %6s | %s" % ("t", "ingenuo", "n", "honesto", "n", "nunca fecha"))
for t in (0, 7, 14, 30, 45, 60, 90, 110, 120, 130):
    w = sum(1 for r in won if r["cyc"] > t)
    l = sum(1 for r in lost if r["cyc"] > t)
    cw = sum(1 for r in coh_w if r["cyc"] > t)
    cl = sum(1 for r in coh_l if r["cyc"] > t)
    n = cw + cl + len(stale)
    print("  %4d | %7.1f%% %6d | %7.1f%% %6d | %.1f%%" % (
        t, pct(w, w + l), w + l, pct(cw, n), n, pct(len(stale), n)))

print()
print("== 8. COORTES POR MES DE ENGAJAMENTO ==")
M = defaultdict(lambda: dict(W=0, L=0, O=0))
for r in won:
    M[(r["e"].year, r["e"].month)]["W"] += 1
for r in lost:
    M[(r["e"].year, r["e"].month)]["L"] += 1
for r in eng:
    M[(r["e"].year, r["e"].month)]["O"] += 1
for k in sorted(M):
    a = M[k]
    n = a["W"] + a["L"] + a["O"]
    print("  %d-%02d n %4d | won %5.1f%% lost %5.1f%% aberto %5.1f%% (%d)" % (
        k[0], k[1], n, pct(a["W"], n), pct(a["L"], n), pct(a["O"], n), a["O"]))
