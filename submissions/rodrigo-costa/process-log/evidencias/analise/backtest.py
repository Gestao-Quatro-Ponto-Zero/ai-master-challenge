#!/usr/bin/env python3
# Prototipo da "maquina do tempo": em cada segunda-feira do 2o semestre de 2017, usando so o que se sabia
# naquele dia, ordena os deals abertos de cada vendedor e ve o que fechou como venda nos 30 dias seguintes.
# Compara: valor (preco de tabela), aleatorio, valor sem os parados, idade, idade + posicao no trimestre.
# So stdlib. Uso: python3 -I backtest.py <pasta com os CSV>
import csv
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date

DD = sys.argv[1]
H = 30
TOPN = 10


def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdate(s):
    s = (s or "").strip()
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


prod = {r["product"]: float(r["sales_price"]) for r in load("products.csv")}
pipe = [r for r in load("sales_pipeline.csv") if r["engage_date"].strip()]
for r in pipe:
    r["e"] = pdate(r["engage_date"])
    r["c"] = pdate(r["close_date"])
    r["price"] = prod[r["product"].replace("GTXPro", "GTX Pro")]
    r["won"] = r["deal_stage"] == "Won"
    r["val"] = float(r["close_value"]) if r["won"] else 0.0

AGEB = (14, 30, 45, 60, 75, 90, 105, 120, 138)


def ageb(a):
    for i, lim in enumerate(AGEB):
        if a <= lim:
            return i
    return len(AGEB)


def qpos(d):
    qs = date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
    return (d - qs).days // 7, (d.month - 1) % 3


def snapshot(d):
    out = []
    end = d + timedelta(days=H)
    for r in pipe:
        if r["e"] < d and (r["c"] is None or r["c"] >= d):
            y = 1 if (r["won"] and r["c"] < end) else 0
            out.append((r, (d - r["e"]).days, y, r["val"] if y else 0.0))
    return out


mondays = []
d = date(2017, 3, 6)
while d <= date(2017, 12, 25):
    mondays.append(d)
    d += timedelta(days=7)
SNAP = {m: snapshot(m) for m in mondays}
EVAL = [m for m in mondays if date(2017, 7, 3) <= m <= date(2017, 12, 1)]


def train(dref):
    """Tabelas de frequencia com snapshots cujo resultado de 30 dias ja era conhecido em dref."""
    c_wk = defaultdict(lambda: [0, 0])
    c_mo = defaultdict(lambda: [0, 0])
    c_age = defaultdict(lambda: [0, 0])
    tot = [0, 0]
    for m in mondays:
        if m + timedelta(days=H) > dref:
            continue
        wk, mo = qpos(m)
        for r, age, y, v in SNAP[m]:
            b = ageb(age)
            for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
                tab[key][0] += y
                tab[key][1] += 1
            tot[0] += y
            tot[1] += 1
    # maior ciclo conhecido em dref
    mc = max([(r["c"] - r["e"]).days for r in pipe if r["c"] and r["c"] < dref] or [0])
    return c_wk, c_mo, c_age, tot, mc


MINN = 30


def p_cal(model, age, dref):
    c_wk, c_mo, c_age, tot, mc = model
    b = ageb(age)
    wk, mo = qpos(dref)
    for tab, key in ((c_wk, (b, wk)), (c_mo, (b, mo)), (c_age, b)):
        y, n = tab.get(key, (0, 0))
        if n >= MINN:
            return y / float(n)
    return tot[0] / float(tot[1]) if tot[1] else 0.0


def p_age(model, age):
    c_wk, c_mo, c_age, tot, mc = model
    y, n = c_age.get(ageb(age), (0, 0))
    if n >= MINN:
        return y / float(n)
    return tot[0] / float(tot[1]) if tot[1] else 0.0


def auc(pairs):
    """pairs: lista de (score, y). Probabilidade de um positivo ficar acima de um negativo (empates = 0,5)."""
    pairs = sorted(pairs, key=lambda t: t[0])
    n1 = sum(y for _, y in pairs)
    n0 = len(pairs) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    rsum = 0.0
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        rsum += avg * sum(y for _, y in pairs[i:j + 1])
        i = j + 1
    return (rsum - n1 * (n1 + 1) / 2.0) / (n1 * n0)


METHODS = ("aleatorio", "valor", "valor_sem_parados", "idade_x_valor", "idade+trimestre_x_valor", "idade+trimestre_so_chance", "oraculo")
agg = {m: dict(wins=0.0, rev=0.0, lists=0) for m in METHODS}
byq = defaultdict(lambda: {m: dict(wins=0.0, rev=0.0, lists=0) for m in METHODS})
auc_cal = []
auc_age = []
auc_val = []
rng = random.Random(20171231)
REP = 20
per_date = []
for dref in EVAL:
    model = train(dref)
    mc = model[4]
    snap = SNAP[dref]
    rows = []
    for r, age, y, v in snap:
        pc = p_cal(model, age, dref)
        pa = p_age(model, age)
        rows.append(dict(r=r, age=age, y=y, v=v, pc=pc, pa=pa, price=r["price"], stale=age > mc))
        auc_cal.append((pc, y))
        auc_age.append((pa, y))
        auc_val.append((r["price"], y))
    bys = defaultdict(list)
    for x in rows:
        bys[x["r"]["sales_agent"]].append(x)
    qk = "T%d" % ((dref.month - 1) // 3 + 1)
    dsum = {m: [0.0, 0.0] for m in METHODS}
    nl = 0
    for s, lst in bys.items():
        if len(lst) < TOPN:
            continue
        nl += 1
        keys = {
            "valor": lambda x: x["price"],
            "valor_sem_parados": lambda x: (0 if x["stale"] else 1, x["price"]),
            "idade_x_valor": lambda x: x["pa"] * x["price"],
            "idade+trimestre_x_valor": lambda x: x["pc"] * x["price"],
            "idade+trimestre_so_chance": lambda x: x["pc"],
            "oraculo": lambda x: x["v"],
        }
        res = {m: [0.0, 0.0] for m in METHODS}
        for _ in range(REP):
            jit = {id(x): rng.random() for x in lst}
            order = sorted(lst, key=lambda x: jit[id(x)])
            top = order[:TOPN]
            res["aleatorio"][0] += sum(x["y"] for x in top)
            res["aleatorio"][1] += sum(x["v"] for x in top)
            for m, kf in keys.items():
                top = sorted(lst, key=lambda x: (kf(x), jit[id(x)]), reverse=True)[:TOPN]
                res[m][0] += sum(x["y"] for x in top)
                res[m][1] += sum(x["v"] for x in top)
        for m in METHODS:
            w = res[m][0] / REP
            v = res[m][1] / REP
            for bucket in (agg, byq[qk]):
                bucket[m]["wins"] += w
                bucket[m]["rev"] += v
                bucket[m]["lists"] += 1
            dsum[m][0] += w
            dsum[m][1] += v
    per_date.append((dref, nl, len(rows), sum(x["y"] for x in rows), dsum))


def report(title, bucket):
    print(title)
    base = bucket["valor"]["rev"]
    orc = bucket["oraculo"]["rev"]
    for m in METHODS:
        b = bucket[m]
        print("  %-28s vendas no top %d: %.2f | receita em 30 dias: US$ %10.0f | %5.1f%% do oraculo | x%.2f do 'valor'" % (
            m, TOPN, b["wins"] / b["lists"], b["rev"], 100 * b["rev"] / orc if orc else 0, b["rev"] / base if base else 0))


print("datas avaliadas: %d segundas-feiras de %s a %s | horizonte %d dias | top %d por vendedor (com 10+ deals abertos)" % (
    len(EVAL), EVAL[0], EVAL[-1], H, TOPN))
report("GERAL (%d listas vendedor-data)" % agg["valor"]["lists"], agg)
for qk in sorted(byq):
    report("%s (%d listas)" % (qk, byq[qk]["valor"]["lists"]), byq[qk])
print("AUC (todos os pares deal-data, n=%d, positivos=%d): idade+trimestre %.3f | so idade %.3f | preco %.3f" % (
    len(auc_cal), sum(y for _, y in auc_cal), auc(auc_cal), auc(auc_age), auc(auc_val)))
print()
print("por data: abertos, vendas reais em 30d, e vendas no top 10 somadas (valor x idade+trimestre x oraculo)")
for dref, nl, nopen, npos, dsum in per_date:
    print("  %s (sem %2d do tri) listas %2d | abertos %4d | vendas em 30d %3d (%.1f%%) | top10: valor %5.1f | idade %5.1f | idade+tri %5.1f | oraculo %5.1f" % (
        dref, qpos(dref)[0], nl, nopen, npos, 100.0 * npos / nopen, dsum["valor"][0], dsum["idade_x_valor"][0],
        dsum["idade+trimestre_x_valor"][0], dsum["oraculo"][0]))

print()
print("calibracao do modelo idade+trimestre (todas as datas avaliadas): previsto x real, por faixa de chance prevista")
cal = defaultdict(lambda: [0.0, 0, 0])
for p, y in auc_cal:
    k = min(9, int(p * 10))
    cal[k][0] += p
    cal[k][1] += y
    cal[k][2] += 1
for k in sorted(cal):
    s, y, n = cal[k]
    print("  %3d-%3d%%: previsto %5.1f%% | real %5.1f%% | n %5d" % (k * 10, k * 10 + 10, 100 * s / n, 100.0 * y / n, n))
