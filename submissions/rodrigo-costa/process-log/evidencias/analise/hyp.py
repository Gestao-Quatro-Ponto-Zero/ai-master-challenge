#!/usr/bin/env python3
# Testa as hipoteses levantadas pelo Rodrigo:
#  (A) o tempo de fechamento varia por produto;  (B) o faturamento do cliente preve ganho;
#  (C) o historico de compras preve ganho;       (D) estrutura de calendario (trimestre).
# So stdlib. Uso: python3 -I hyp.py <pasta com os CSV>
import csv
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from statistics import median

DD = sys.argv[1]


def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdate(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def chi2_sf(x, k):
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


def chi2_groups(rows):
    rows = [r for r in rows if sum(r) > 0]
    ta = sum(r[0] for r in rows)
    tb = sum(r[1] for r in rows)
    t = ta + tb
    if ta == 0 or tb == 0 or len(rows) < 2:
        return float("nan"), 0, float("nan")
    x = 0.0
    for a, b in rows:
        n = a + b
        x += (a - n * ta / t) ** 2 / (n * ta / t) + (b - n * tb / t) ** 2 / (n * tb / t)
    return x, len(rows) - 1, chi2_sf(x, len(rows) - 1)


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


def q(v, p):
    v = sorted(v)
    if not v:
        return float("nan")
    return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]


def kruskal(groups):
    groups = [g for g in groups if g]
    allv = [(v, gi) for gi, g in enumerate(groups) for v in g]
    n_all = len(allv)
    vals = [v for v, _ in allv]
    rk = ranks(vals)
    rs = defaultdict(float)
    ns = Counter()
    for (v, gi), r in zip(allv, rk):
        rs[gi] += r
        ns[gi] += 1
    h = 12.0 / (n_all * (n_all + 1)) * sum(rs[g] ** 2 / ns[g] for g in rs) - 3 * (n_all + 1)
    ties = sum(t ** 3 - t for t in Counter(vals).values())
    h /= (1 - ties / float(n_all ** 3 - n_all))
    return h, len(rs) - 1, chi2_sf(h, len(rs) - 1)


def cmh(strata):
    """strata: lista de (a,b,c,d) = (F1&won, F1&lost, F0&won, F0&lost). Devolve chi2, p, diferenca de risco MH em pp."""
    num = 0.0
    var = 0.0
    dn = 0.0
    dd = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        n1 = a + b
        n0 = c + d
        if n < 2 or n1 == 0 or n0 == 0:
            continue
        num += a - n1 * (a + c) / n
        var += n1 * n0 * (a + c) * (b + d) / (n * n * (n - 1.0))
        dn += (a * n0 - c * n1) / n
        dd += n1 * n0 / n
    if var == 0:
        return float("nan"), float("nan"), float("nan")
    x = (abs(num) - 0.5) ** 2 / var
    return x, chi2_sf(x, 1), 100.0 * dn / dd


acc = {r["account"]: r for r in load("accounts.csv")}
prod = {r["product"]: r for r in load("products.csv")}
teams = {r["sales_agent"]: r for r in load("sales_teams.csv")}
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["e"] = pdate(r["engage_date"])
    r["c"] = pdate(r["close_date"])
    r["prod"] = r["product"].replace("GTXPro", "GTX Pro")
    r["price"] = float(prod[r["prod"]]["sales_price"])
    r["series"] = prod[r["prod"]]["series"]
    r["acc"] = r["account"].strip()
    r["st"] = r["deal_stage"]
    r["won"] = 1 if r["st"] == "Won" else 0
    r["region"] = teams[r["sales_agent"]]["regional_office"]
closed = [r for r in pipe if r["st"] in ("Won", "Lost")]
for r in closed:
    r["cyc"] = (r["c"] - r["e"]).days
ref = max(x for r in pipe for x in (r["e"], r["c"]) if x)
maxcyc = max(r["cyc"] for r in closed)
cutoff = ref - timedelta(days=maxcyc)
first_close = min(r["c"] for r in closed)
eng = [r for r in pipe if r["st"] == "Engaging"]
opn = [r for r in pipe if r["st"] in ("Engaging", "Prospecting")]


def clean(r):
    return r["e"] is not None and first_close <= r["e"] < cutoff


PRODS = sorted(prod, key=lambda p: float(prod[p]["sales_price"]))
print("ref %s | maior ciclo %d | janela limpa: engajados de %s ate antes de %s" % (ref, maxcyc, first_close, cutoff))

print()
print("== A. TEMPO DE FECHAMENTO POR PRODUTO (janela limpa) ==")
print("%-15s %6s | %5s %5s %5s %5s | ganhos: %4s %4s %4s %4s %4s | <=14d 15-60 >60 | perdidos: med p75 max" % (
    "produto", "preco", "n", "won%", "lost%", "ab%", "p25", "med", "p75", "p90", "max"))
gw = []
gl = []
for p in PRODS:
    w = [r["cyc"] for r in closed if r["prod"] == p and r["won"] and clean(r)]
    l = [r["cyc"] for r in closed if r["prod"] == p and not r["won"] and clean(r)]
    s = sum(1 for r in eng if r["prod"] == p and clean(r))
    n = len(w) + len(l) + s
    gw.append(w)
    gl.append(l)
    print("%-15s %6.0f | %5d %5.1f %5.1f %5.1f | %12d %4d %4d %4d %4d | %4.0f%% %4.0f%% %3.0f%% | %12d %3d %3d" % (
        p, float(prod[p]["sales_price"]), n, pct(len(w), n), pct(len(l), n), pct(s, n),
        q(w, .25), median(w), q(w, .75), q(w, .9), max(w),
        pct(sum(1 for x in w if x <= 14), len(w)), pct(sum(1 for x in w if 15 <= x <= 60), len(w)),
        pct(sum(1 for x in w if x > 60), len(w)), median(l), q(l, .75), max(l)))
print("Kruskal-Wallis do ciclo dos ganhos entre produtos: H=%.2f gl=%d p=%.3f" % kruskal(gw))
print("Kruskal-Wallis do ciclo dos perdidos entre produtos: H=%.2f gl=%d p=%.3f" % kruskal(gl))
ww = [r for r in closed if r["won"] and clean(r)]
print("Spearman(preco de tabela, ciclo) nos ganhos: %.3f (n=%d) | nos perdidos: %.3f" % (
    spearman([r["price"] for r in ww], [r["cyc"] for r in ww]), len(ww),
    spearman([r["price"] for r in closed if not r["won"] and clean(r)], [r["cyc"] for r in closed if not r["won"] and clean(r)])))
print("maior ciclo por produto (todos os fechados):", {p: max(r["cyc"] for r in closed if r["prod"] == p) for p in PRODS})
print("ganhos na janela limpa: <=14d %.1f%% | 15-60d %.1f%% | 61+d %.1f%% | mediana %d" % (
    pct(sum(1 for r in ww if r["cyc"] <= 14), len(ww)), pct(sum(1 for r in ww if 15 <= r["cyc"] <= 60), len(ww)),
    pct(sum(1 for r in ww if r["cyc"] > 60), len(ww)), median([r["cyc"] for r in ww])))
print()
print("chance de venda dado que segue aberto aos t dias (contando os sem desfecho), por produto e por faixa:")
TS = (0, 30, 60, 90, 110)


def surv(rows_closed, n_open):
    out = []
    for t in TS:
        w = sum(1 for r in rows_closed if r["won"] and r["cyc"] > t)
        l = sum(1 for r in rows_closed if not r["won"] and r["cyc"] > t)
        tot = w + l + n_open
        out.append("%5.1f%% (%4d)" % (pct(w, tot), tot))
    return "  ".join(out)


print("%-22s %s" % ("", "  ".join("t=%-10d" % t for t in TS)))
for p in PRODS:
    print("%-22s %s" % (p, surv([r for r in closed if r["prod"] == p and clean(r)], sum(1 for r in eng if r["prod"] == p and clean(r)))))
TIERS = (("ate US$ 1.096", lambda x: x <= 1096), ("US$ 3.393 a 5.482", lambda x: 3000 < x < 6000), ("GTK 500 (26.768)", lambda x: x > 6000))
for name, f in TIERS:
    print("%-22s %s" % (name, surv([r for r in closed if f(r["price"]) and clean(r)], sum(1 for r in eng if f(r["price"]) and clean(r)))))
for sname in ("GTX", "MG", "GTK"):
    print("%-22s %s" % ("serie " + sname, surv([r for r in closed if r["series"] == sname and clean(r)], sum(1 for r in eng if r["series"] == sname and clean(r)))))

print()
print("== D. CALENDARIO ==")
print("por mes de engajamento (fechados): n, taxa oficial, mediana do ciclo dos ganhos e dos perdidos, %% dos fechamentos em ate 14 dias")
bym = defaultdict(list)
for r in closed:
    bym["%d-%02d" % (r["e"].year, r["e"].month)].append(r)
for k in sorted(bym):
    g = bym[k]
    w = [r["cyc"] for r in g if r["won"]]
    l = [r["cyc"] for r in g if not r["won"]]
    print("  %s n %4d | taxa %5.1f%% | ciclo ganho med %3d | perdido med %3d | <=14d %5.1f%%" % (
        k, len(g), pct(len(w), len(g)), median(w) if w else -1, median(l) if l else -1,
        pct(sum(1 for r in g if r["cyc"] <= 14), len(g))))
print("matriz mes de engajamento (linha) x mes de fechamento (coluna): ganhos/perdidos")
cm = sorted({"%d-%02d" % (r["c"].year, r["c"].month) for r in closed})
print("         " + " ".join("%9s" % c[2:] for c in cm))
for k in sorted(bym):
    row = []
    for c in cm:
        w = sum(1 for r in bym[k] if r["won"] and "%d-%02d" % (r["c"].year, r["c"].month) == c)
        l = sum(1 for r in bym[k] if not r["won"] and "%d-%02d" % (r["c"].year, r["c"].month) == c)
        row.append("%4d/%-4d" % (w, l) if w + l else "    .    ")
    print("  %s " % k[2:] + " ".join(row))
print("por dia do mes de fechamento (ganhos e perdidos), meses de fim de trimestre x demais:")
for name, months in (("fim de trimestre", (3, 6, 9, 12)), ("demais", (4, 5, 7, 8, 10, 11))):
    g = [r for r in closed if r["c"].month in months]
    parts = []
    for lo, hi in ((1, 10), (11, 20), (21, 31)):
        w = sum(1 for r in g if r["won"] and lo <= r["c"].day <= hi)
        l = sum(1 for r in g if not r["won"] and lo <= r["c"].day <= hi)
        parts.append("dias %d-%d: %d/%d (%.0f%%)" % (lo, hi, w, l, pct(w, w + l)))
    print("  %-16s %s" % (name, " | ".join(parts)))
print()
print("teste sem vazamento: no dia 1 de cada mes, deals abertos naquele dia -> % que fecha como GANHO nos 30 dias seguintes, por idade")
BUCK = ((0, 30), (31, 60), (61, 90), (91, 138), (139, 9999))
print("  data       tipo      " + "  ".join("%3d-%-4s" % (a, str(b) if b < 9999 else "+") + "      " for a, b in BUCK) + " total")
for m in range(4, 13):
    d0 = date(2017, m, 1)
    d1 = d0 + timedelta(days=30)
    op = [r for r in pipe if r["e"] and r["e"] < d0 and (r["c"] is None or r["c"] >= d0)]
    parts = []
    for a, b in BUCK:
        g = [r for r in op if a <= (d0 - r["e"]).days <= b]
        w = sum(1 for r in g if r["won"] and r["c"] < d1)
        l = sum(1 for r in g if r["st"] == "Lost" and r["c"] < d1)
        parts.append("%4.0f%%/%2.0f%% (%4d)" % (pct(w, len(g)), pct(l, len(g)), len(g)) if g else "      .        ")
    w = sum(1 for r in op if r["won"] and r["c"] < d1)
    print("  %s %-9s %s  %4.0f%% (%d)" % (d0, "FIM-TRI" if m in (6, 9, 12) else "", "  ".join(parts), pct(w, len(op)), len(op)))

print()
print("== B. FATURAMENTO E OUTROS ATRIBUTOS DO CLIENTE (fechados; todos tem conta) ==")
for r in closed:
    a = acc[r["acc"]]
    r["rev"] = float(a["revenue"])
    r["emp"] = float(a["employees"])
    r["year"] = int(a["year_established"])
    r["us"] = a["office_location"] == "United States"
    r["sub"] = bool(a["subsidiary_of"].strip())
    r["sector"] = a["sector"]
revs = sorted(float(a["revenue"]) for a in acc.values())
cuts = [revs[len(revs) // 4], revs[len(revs) // 2], revs[3 * len(revs) // 4]]
print("cortes de faturamento por quartil de contas (US$ milhoes):", cuts)


def quart(v, cuts_):
    return sum(1 for c in cuts_ if v >= c)


def show(name, keyf, rows=closed, labels=None):
    g = defaultdict(lambda: [0, 0])
    for r in rows:
        g[keyf(r)][0 if r["won"] else 1] += 1
    parts = []
    for k in sorted(g):
        w, l = g[k]
        parts.append("%s: %.1f%% (n=%d)" % (labels[k] if labels else k, pct(w, w + l), w + l))
    x, df, p = chi2_groups([tuple(v) for v in g.values()])
    print("  %-34s %s | qui2=%.2f gl=%d p=%.3f" % (name, " | ".join(parts), x, df, p))


QL = {0: "Q1 menor", 1: "Q2", 2: "Q3", 3: "Q4 maior"}
show("faturamento (quartil de contas)", lambda r: quart(r["rev"], cuts), labels=QL)
half = sorted(r["c"] for r in closed)[len(closed) // 2]
show("  idem, 1a metade dos fechamentos", lambda r: quart(r["rev"], cuts), [r for r in closed if r["c"] < half], QL)
show("  idem, 2a metade", lambda r: quart(r["rev"], cuts), [r for r in closed if r["c"] >= half], QL)
low10 = set(sorted(acc, key=lambda a: float(acc[a]["revenue"]))[:10])
top10 = set(sorted(acc, key=lambda a: -float(acc[a]["revenue"]))[:10])
show("10 menores x 10 maiores x resto", lambda r: 0 if r["acc"] in low10 else (2 if r["acc"] in top10 else 1),
     labels={0: "10 menores", 1: "resto", 2: "10 maiores"})
lr = [math.log10(r["rev"]) for r in closed]
wv = [r["won"] for r in closed]
rr = pearson(lr, wv)
print("  correlacao log10(faturamento) x ganho: r=%.4f (t=%.2f, n=%d)" % (rr, rr * math.sqrt(len(lr) - 2) / math.sqrt(1 - rr * rr), len(lr)))
print("  produtos caros (preco >= 3.393), por quartil de faturamento:")
show("    caros", lambda r: quart(r["rev"], cuts), [r for r in closed if r["price"] >= 3393], QL)
show("    GTK 500", lambda r: 0 if r["rev"] < cuts[1] else 1, [r for r in closed if r["prod"] == "GTK 500"], {0: "metade menor", 1: "metade maior"})
print("  peso do deal no faturamento do cliente (preco / faturamento anual):")
ratio = sorted(r["price"] / (r["rev"] * 1e6) for r in closed)
print("    mediana %.5f%% | p90 %.4f%% | maximo %.3f%%" % (100 * median(ratio), 100 * q(ratio, .9), 100 * ratio[-1]))
rc = [q(ratio, .25), q(ratio, .5), q(ratio, .75)]
show("    por quartil do peso", lambda r: quart(r["price"] / (r["rev"] * 1e6), rc), labels={0: "Q1 leve", 1: "Q2", 2: "Q3", 3: "Q4 pesado"})
top1 = q(ratio, .99)
show("    1% mais pesados x resto", lambda r: 1 if r["price"] / (r["rev"] * 1e6) >= top1 else 0, labels={0: "resto", 1: "1% mais pesados"})
emps = sorted(float(a["employees"]) for a in acc.values())
ec = [emps[len(emps) // 4], emps[len(emps) // 2], emps[3 * len(emps) // 4]]
show("funcionarios (quartil de contas)", lambda r: quart(r["emp"], ec), labels=QL)
yrs = sorted(int(a["year_established"]) for a in acc.values())
yc = [yrs[len(yrs) // 4], yrs[len(yrs) // 2], yrs[3 * len(yrs) // 4]]
show("ano de fundacao (quartil)", lambda r: quart(r["year"], yc), labels={0: "mais antigas", 1: "Q2", 2: "Q3", 3: "mais novas"})
show("sede nos EUA", lambda r: 1 if r["us"] else 0, labels={0: "fora", 1: "EUA"})
show("e subsidiaria", lambda r: 1 if r["sub"] else 0, labels={0: "nao", 1: "sim"})
show("setor", lambda r: r["sector"])
print("  por CONTA (85): o faturamento se relaciona com volume e valor?")
A = defaultdict(lambda: dict(n=0, w=0, l=0, val=0.0, price=0.0))
for r in pipe:
    if r["acc"]:
        a = A[r["acc"]]
        a["n"] += 1
        a["price"] += r["price"]
        if r["st"] == "Won":
            a["w"] += 1
            a["val"] += float(r["close_value"])
        elif r["st"] == "Lost":
            a["l"] += 1
names = sorted(A)
rv = [float(acc[n]["revenue"]) for n in names]
for lab, vec in (("n de deals", [A[n]["n"] for n in names]), ("valor ganho", [A[n]["val"] for n in names]),
                 ("preco medio de tabela dos deals", [A[n]["price"] / A[n]["n"] for n in names]),
                 ("taxa de ganho", [A[n]["w"] / float(A[n]["w"] + A[n]["l"]) for n in names])):
    rho = spearman(rv, vec)
    print("    Spearman(faturamento, %s) = %+.3f (t=%.2f, n=85)" % (lab, rho, rho * math.sqrt(83) / math.sqrt(1 - rho * rho)))
print("    por quartil de faturamento: deals por conta e valor ganho por conta (medianas):")
for k in range(4):
    g = [n for n in names if quart(float(acc[n]["revenue"]), cuts) == k]
    print("      %-9s contas %2d | deals/conta %5.0f | valor ganho/conta US$ %8.0f | taxa %.1f%%" % (
        QL[k], len(g), median([A[n]["n"] for n in g]), median([A[n]["val"] for n in g]),
        pct(sum(A[n]["w"] for n in g), sum(A[n]["w"] + A[n]["l"] for n in g))))
print("  disponibilidade: conta preenchida em %d de %d deals abertos (%.1f%%)" % (
    sum(1 for r in opn if r["acc"]), len(opn), pct(sum(1 for r in opn if r["acc"]), len(opn))))

print()
print("== C. HISTORICO DE COMPRAS (sem vazamento: so o que estava FECHADO antes do engajamento do deal) ==")
byacc = defaultdict(list)
for r in pipe:
    if r["acc"]:
        byacc[r["acc"]].append(r)
START = date(2017, 4, 1)
ev = [r for r in closed if r["e"] >= START]
for r in ev:
    pr = [x for x in byacc[r["acc"]] if x is not r]
    pw = [x for x in pr if x["st"] == "Won" and x["c"] < r["e"]]
    pl = [x for x in pr if x["st"] == "Lost" and x["c"] < r["e"]]
    r["h_won"] = len(pw)
    r["h_lost"] = len(pl)
    r["h_val"] = sum(float(x["close_value"]) for x in pw)
    r["h_same"] = any(x["prod"] == r["prod"] for x in pw)
    r["h_series"] = any(x["series"] == r["series"] for x in pw)
    r["h_rel"] = sum(1 for x in pw if x["sales_agent"] == r["sales_agent"])
    r["h_rec"] = min((r["e"] - x["c"]).days for x in pw) if pw else None
    r["h_wr"] = len(pw) / float(len(pw) + len(pl)) if len(pw) + len(pl) >= 5 else None
    r["h_open"] = sum(1 for x in pr if x["e"] and x["e"] < r["e"] and (x["c"] is None or x["c"] >= r["e"]))
    r["h_lostsame"] = any(x["prod"] == r["prod"] for x in pl)
    r["mk"] = "%d-%02d" % (r["e"].year, r["e"].month)
print("deals avaliados (engajados desde %s): %d | com alguma compra anterior da conta: %.1f%% | mediana de compras anteriores %d" % (
    START, len(ev), pct(sum(1 for r in ev if r["h_won"] > 0), len(ev)), median([r["h_won"] for r in ev])))


def strat_test(name, flag, rows):
    """flag(r, mediana_do_mes) -> True/False/None. Compara dentro do mes de engajamento (CMH)."""
    strata = []
    tot1 = [0, 0]
    tot0 = [0, 0]
    for mk in sorted({r["mk"] for r in rows}):
        g = [r for r in rows if r["mk"] == mk]
        a = b = c = d = 0
        for r in g:
            f = flag(r, g)
            if f is None:
                continue
            if f:
                if r["won"]:
                    a += 1
                else:
                    b += 1
            else:
                if r["won"]:
                    c += 1
                else:
                    d += 1
        strata.append((a, b, c, d))
        tot1[0] += a
        tot1[1] += b
        tot0[0] += c
        tot0[1] += d
    x, p, diff = cmh(strata)
    return "%-44s sim %.1f%% (n=%d) x nao %.1f%% (n=%d) | dif. dentro do mes %+.1f pp | CMH qui2=%.2f p=%.3f" % (
        name, pct(tot1[0], sum(tot1)), sum(tot1), pct(tot0[0], sum(tot0)), sum(tot0), diff, x, p)


def med_of(g, key):
    v = [r[key] for r in g if r[key] is not None]
    return median(v) if v else None


TESTS = (
    ("conta ja comprou ESTE produto", lambda r, g: r["h_same"]),
    ("conta ja comprou a mesma serie", lambda r, g: r["h_series"]),
    ("este vendedor ja ganhou nesta conta", lambda r, g: r["h_rel"] > 0),
    ("conta ja PERDEU este produto antes", lambda r, g: r["h_lostsame"]),
    ("mais compras anteriores que a mediana do mes", lambda r, g: r["h_won"] > med_of(g, "h_won")),
    ("mais valor comprado que a mediana do mes", lambda r, g: r["h_val"] > med_of(g, "h_val")),
    ("taxa de ganho anterior da conta acima da mediana", lambda r, g: None if r["h_wr"] is None else r["h_wr"] > med_of(g, "h_wr")),
    ("comprou ha menos tempo que a mediana do mes", lambda r, g: None if r["h_rec"] is None else r["h_rec"] < med_of(g, "h_rec")),
    ("mais deals abertos na conta que a mediana", lambda r, g: r["h_open"] > med_of(g, "h_open")),
)
for label, rows in (("todos", ev), ("engajados abr-jul", [r for r in ev if r["mk"] <= "2017-07"]), ("engajados ago-dez", [r for r in ev if r["mk"] >= "2017-08"])):
    print("  -- %s (n=%d)" % (label, len(rows)))
    for name, flag in TESTS:
        print("     " + strat_test(name, flag, rows))
print("  taxa de ganho por numero de compras anteriores da conta (sem estratificar):")
for lo, hi in ((0, 0), (1, 5), (6, 15), (16, 30), (31, 999)):
    g = [r for r in ev if lo <= r["h_won"] <= hi]
    if g:
        print("     %3d-%-3d compras: %.1f%% (n=%d)" % (lo, hi, pct(sum(r["won"] for r in g), len(g)), len(g)))
print("  disponibilidade nos abertos: so %.1f%% tem conta; desses, a conta ja comprou o mesmo produto em %.1f%%" % (
    pct(sum(1 for r in opn if r["acc"]), len(opn)),
    pct(sum(1 for r in opn if r["acc"] and any(x["st"] == "Won" and x["prod"] == r["prod"] for x in byacc[r["acc"]])),
        sum(1 for r in opn if r["acc"]))))
