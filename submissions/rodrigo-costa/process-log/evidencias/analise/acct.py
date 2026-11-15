#!/usr/bin/env python3
# Porte do cliente x deals SEM DESFECHO (nao so ganho x perda). So stdlib.
import csv, math, os, random, sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from statistics import median, mean, pvariance
DD = sys.argv[1]
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pd(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None
def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(idx):
        j = i
        while j+1 < len(idx) and v[idx[j+1]] == v[idx[i]]: j += 1
        for k in range(i, j+1): r[idx[k]] = (i+j)/2+1
        i = j+1
    return r
def pearson(a, b):
    n = len(a); ma = sum(a)/n; mb = sum(b)/n
    sa = math.sqrt(sum((x-ma)**2 for x in a)); sb = math.sqrt(sum((y-mb)**2 for y in b))
    return sum((x-ma)*(y-mb) for x, y in zip(a, b))/(sa*sb) if sa and sb else float("nan")
def spearman(a, b): return pearson(ranks(a), ranks(b))
def pct(a, b): return 100.0*a/b if b else float("nan")
acc = {r["account"]: r for r in load("accounts.csv")}
prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["e"] = pd(r["engage_date"]); r["c"] = pd(r["close_date"]); r["acc"] = r["account"].strip()
    r["st"] = r["deal_stage"]; r["won"] = r["st"] == "Won"
    r["price"] = prod[r["product"].replace("GTXPro", "GTX Pro")]
    r["region"] = teams[r["sales_agent"]]["regional_office"]
closed = [r for r in pipe if r["st"] in ("Won", "Lost")]
for r in closed: r["cyc"] = (r["c"]-r["e"]).days
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
maxcyc = max(r["cyc"] for r in closed); cutoff = ref - timedelta(days=maxcyc); first_close = min(r["c"] for r in closed)
names = sorted(acc)
rev = {a: float(acc[a]["revenue"]) for a in names}
order = sorted(names, key=lambda a: rev[a])
quart = {a: min(3, i*4//len(order)) for i, a in enumerate(order)}
QL = ["Q1 menor", "Q2", "Q3", "Q4 maior"]
mat = [r for r in pipe if r["e"] and r["e"] < cutoff and r["acc"]]
def table(rows, key, labels):
    g = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        g[key(r)][0 if r["won"] else (1 if r["st"] == "Lost" else 2)] += 1
    out = []
    for k in sorted(g):
        w, l, s = g[k]; n = w+l+s
        out.append("%s: sem desfecho %.1f%% | venda %.1f%% | n=%d" % (labels[k], pct(s, n), pct(w, n), n))
    return g, out
print("== 1. coorte madura COM cliente identificado (n=%d): sem desfecho por quartil de faturamento ==" % len(mat))
g, out = table(mat, lambda r: quart[r["acc"]], QL)
for o in out: print("  ", o)
obs = pct(g[0][2], sum(g[0])) - pct(g[3][2], sum(g[3]))
# permutacao: embaralha o faturamento entre as contas
per = defaultdict(lambda: [0, 0])
for r in mat:
    per[r["acc"]][0] += r["st"] == "Engaging"; per[r["acc"]][1] += 1
rng = random.Random(7)
cnt = 0; N = 20000
labs = [quart[a] for a in names]
for _ in range(N):
    rng.shuffle(labs)
    s = [[0, 0] for _ in range(4)]
    for a, q in zip(names, labs):
        s[q][0] += per[a][0]; s[q][1] += per[a][1]
    d = pct(s[0][0], s[0][1]) - pct(s[3][0], s[3][1])
    if abs(d) >= abs(obs): cnt += 1
print("   diferenca Q1 - Q4 = %.1f pp | permutacao por conta (%d sorteios): p = %.4f" % (obs, N, cnt/float(N)))
print("   por regional do vendedor (o efeito continua dentro de cada uma?):")
for reg in ("Central", "East", "West"):
    g2, out2 = table([r for r in mat if r["region"] == reg], lambda r: quart[r["acc"]], QL)
    print("    %-8s" % reg, " | ".join("%s %.1f%% (n=%d)" % (QL[k], pct(g2[k][2], sum(g2[k])), sum(g2[k])) for k in sorted(g2)))
print("   janela sem truncamento (engajados desde %s):" % first_close)
g3, out3 = table([r for r in mat if r["e"] >= first_close], lambda r: quart[r["acc"]], QL)
for o in out3: print("     ", o)
print()
print("== 2. por conta: os deals sem desfecho se espalham por igual ou acompanham o tamanho? ==")
st = {a: 0 for a in names}; cl = {a: 0 for a in names}; wonn = {a: 0 for a in names}; allst = {a: 0 for a in names}
for r in pipe:
    if not r["acc"]: continue
    if r["st"] == "Engaging" and r["e"] < cutoff: st[r["acc"]] += 1
    if r["st"] in ("Won", "Lost") and r["e"] < cutoff: cl[r["acc"]] += 1
    if r["won"]: wonn[r["acc"]] += 1
sv = [st[a] for a in names]
print("   sem desfecho por conta: min %d mediana %g max %d | media %.2f variancia %.2f (Poisson: variancia ~ media)" % (min(sv), median(sv), max(sv), mean(sv), pvariance(sv)))
print("   Spearman(faturamento, n de sem desfecho da conta) = %+.3f | Spearman(faturamento, n de fechados da conta) = %+.3f" % (
    spearman([rev[a] for a in names], sv), spearman([rev[a] for a in names], [cl[a] for a in names])))
print("   Spearman(n de vendas da conta, %% sem desfecho da conta) = %+.3f" % spearman([wonn[a] for a in names], [st[a]/float(st[a]+cl[a]) for a in names]))
print("   por quartil: sem desfecho por conta (media) e fechados por conta (media)")
for k in range(4):
    gq = [a for a in names if quart[a] == k]
    print("     %-9s contas %2d | sem desfecho/conta %.1f | fechados/conta %.1f" % (QL[k], len(gq), mean(st[a] for a in gq), mean(cl[a] for a in gq)))
print("   por tercil de VOLUME de compras da conta (n de vendas):")
ordv = sorted(names, key=lambda a: wonn[a]); ter = {a: min(2, i*3//len(ordv)) for i, a in enumerate(ordv)}
g4, out4 = table(mat, lambda r: ter[r["acc"]], ["compra pouco", "medio", "compra muito"])
for o in out4: print("     ", o)
print()
print("== 3. chance de venda se ainda aberto aos t dias, so deals COM cliente, por porte (janela limpa) ==")
cleanm = [r for r in mat if r["e"] >= first_close]
for name, sel in (("Q1 menor", (0,)), ("Q2+Q3", (1, 2)), ("Q4 maior", (3,))):
    rows = [r for r in cleanm if quart[r["acc"]] in sel]
    parts = []
    for t in (0, 30, 60, 90, 110):
        w = sum(1 for r in rows if r["won"] and r["cyc"] > t); l = sum(1 for r in rows if r["st"] == "Lost" and r["cyc"] > t)
        s = sum(1 for r in rows if r["st"] == "Engaging")
        parts.append("t=%d: %.1f%% (%d)" % (t, pct(w, w+l+s), w+l+s))
    print("   %-9s %s" % (name, " | ".join(parts)))
print()
print("== 4. quantos deals abertos hoje seriam afetados ==")
alive = [r for r in pipe if r["st"] == "Engaging" and r["e"] >= cutoff]
stale = [r for r in pipe if r["st"] == "Engaging" and r["e"] < cutoff]
pros = [r for r in pipe if r["st"] == "Prospecting"]
for nm, grp in (("vivos", alive), ("sem desfecho", stale), ("prospeccao", pros)):
    wa = [r for r in grp if r["acc"]]
    print("   %-13s %4d | com cliente %3d (%.0f%%) | por quartil: %s" % (nm, len(grp), len(wa), pct(len(wa), len(grp)),
          ", ".join("%s %d" % (QL[k], sum(1 for r in wa if quart[r["acc"]] == k)) for k in range(4))))
