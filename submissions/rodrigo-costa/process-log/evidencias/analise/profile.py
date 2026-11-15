#!/usr/bin/env python3
# Inventario dos 5 arquivos: colunas, vazios, distintos, faixas, cobertura por estagio, integridade.
# Uso: python3 -I profile.py <pasta com os CSV>
import csv
import os
import sys
from collections import Counter, defaultdict
from statistics import median

D = sys.argv[1]


def load(name):
    with open(os.path.join(D, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def isnum(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def isdate(s):
    return len(s) == 10 and s[4] == "-" and s[7] == "-"


def prof(name, rows, topn=12):
    print("=====", name, "|", len(rows), "linhas")
    for c in rows[0].keys():
        vals = [(r[c] or "").strip() for r in rows]
        ne = [v for v in vals if v != ""]
        dist = Counter(ne)
        line = "  %-18s vazios %5d | distintos %5d" % (c, len(vals) - len(ne), len(dist))
        if ne and all(isnum(v) for v in ne):
            nums = sorted(float(v) for v in ne)
            line += " | min %g mediana %g max %g" % (nums[0], median(nums), nums[-1])
        elif ne and all(isdate(v) for v in ne):
            line += " | %s .. %s" % (min(ne), max(ne))
        print(line)
        if len(dist) <= topn:
            print("       ", dict(dist.most_common()))
        else:
            print("        mais comuns:", dist.most_common(5))


acc = load("accounts.csv")
prod = load("products.csv")
teams = load("sales_teams.csv")
pipe = load("sales_pipeline.csv")

print("===== metadata.csv")
with open(os.path.join(D, "metadata.csv"), newline="", encoding="utf-8") as f:
    for row in csv.reader(f):
        print("  ", " | ".join(row))
print()
prof("accounts.csv", acc)
print()
prof("products.csv", prod)
for r in prod:
    print("    ", r)
print()
prof("sales_teams.csv", teams)
print()
prof("sales_pipeline.csv", pipe)

print()
print("== COBERTURA DO PIPELINE POR ESTAGIO ==")
for st in ("Won", "Lost", "Engaging", "Prospecting"):
    g = [r for r in pipe if r["deal_stage"] == st]
    cv = [float(r["close_value"]) for r in g if (r["close_value"] or "").strip() != ""]
    print("%-11s n %4d | sem account %4d (%.1f%%) | sem engage_date %4d | sem close_date %4d | sem close_value %4d | close_value=0: %d" % (
        st, len(g), sum(1 for r in g if not r["account"].strip()),
        100.0 * sum(1 for r in g if not r["account"].strip()) / len(g),
        sum(1 for r in g if not r["engage_date"].strip()), sum(1 for r in g if not r["close_date"].strip()),
        sum(1 for r in g if not (r["close_value"] or "").strip()), sum(1 for v in cv if v == 0)))
    if cv:
        cv.sort()
        print("            close_value: min %g mediana %g max %g soma %g" % (cv[0], median(cv), cv[-1], sum(cv)))

print()
print("== INTEGRIDADE ==")
accn = {r["account"] for r in acc}
pacc = {r["account"].strip() for r in pipe if r["account"].strip()}
print("contas no pipeline fora de accounts:", sorted(pacc - accn))
print("contas de accounts sem deal:", sorted(accn - pacc))
pn = {r["product"] for r in prod}
pp = {r["product"] for r in pipe}
print("produtos no pipeline fora de products:", sorted(pp - pn), "| em products sem deal:", sorted(pn - pp))
tn = {r["sales_agent"] for r in teams}
pa = {r["sales_agent"] for r in pipe}
print("vendedores no pipeline fora de teams:", sorted(pa - tn), "| em teams sem deal:", sorted(tn - pa))
ids = Counter(r["opportunity_id"] for r in pipe)
print("opportunity_id duplicados:", sum(1 for v in ids.values() if v > 1), "| contas duplicadas:", len(acc) - len(accn))
subs = {r["subsidiary_of"].strip() for r in acc if r["subsidiary_of"].strip()}
print("subsidiary_of preenchido em", sum(1 for r in acc if r["subsidiary_of"].strip()), "contas | controladoras:", sorted(subs),
      "| fora de accounts:", sorted(subs - accn))
bad = [r for r in pipe if r["engage_date"] and r["close_date"] and r["close_date"] < r["engage_date"]]
print("close_date antes de engage_date:", len(bad))
print("Won com close_value <= 0:", sum(1 for r in pipe if r["deal_stage"] == "Won" and float(r["close_value"] or 0) <= 0),
      "| Lost com close_value != 0:", sum(1 for r in pipe if r["deal_stage"] == "Lost" and float(r["close_value"] or 0) != 0))

print()
print("== CONTAS: setores, paises, faixas ==")
print("setores:", dict(Counter(r["sector"] for r in acc).most_common()))
print("paises:", dict(Counter(r["office_location"] for r in acc).most_common()))
for c in ("year_established", "revenue", "employees"):
    v = sorted(float(r[c]) for r in acc)
    print("%-16s min %g p25 %g mediana %g p75 %g max %g" % (c, v[0], v[len(v) // 4], median(v), v[3 * len(v) // 4], v[-1]))

print()
print("== DEALS POR CONTA ==")
per = defaultdict(lambda: Counter())
for r in pipe:
    if r["account"].strip():
        per[r["account"].strip()][r["deal_stage"]] += 1
tot = sorted(sum(c.values()) for c in per.values())
print("deals por conta (com conta): min %d mediana %g max %d | contas %d" % (tot[0], median(tot), tot[-1], len(tot)))
won_val = defaultdict(float)
for r in pipe:
    if r["deal_stage"] == "Won":
        won_val[r["account"].strip()] += float(r["close_value"])
tv = sum(won_val.values())
top = sorted(won_val.items(), key=lambda kv: -kv[1])
print("valor ganho total %.0f | top 5 contas: %s" % (tv, [(k, round(v), "%.1f%%" % (100 * v / tv)) for k, v in top[:5]]))
print("top 10 contas = %.1f%% do valor ganho | top 20 = %.1f%%" % (
    100 * sum(v for _, v in top[:10]) / tv, 100 * sum(v for _, v in top[:20]) / tv))
opn = [sum(c[s] for s in ("Engaging", "Prospecting")) for c in per.values()]
print("deals abertos COM conta: %d, em %d contas (min %d mediana %g max %d por conta)" % (
    sum(opn), sum(1 for x in opn if x > 0), min(opn), median(opn), max(opn)))
agents_per_acc = defaultdict(set)
for r in pipe:
    if r["account"].strip():
        agents_per_acc[r["account"].strip()].add(r["sales_agent"])
apa = sorted(len(v) for v in agents_per_acc.values())
print("vendedores distintos por conta: min %d mediana %g max %d" % (apa[0], median(apa), apa[-1]))

print()
print("== EXEMPLOS (3 linhas de cada) ==")
for name, rows in (("accounts", acc), ("pipeline Won", [r for r in pipe if r["deal_stage"] == "Won"]),
                   ("pipeline Lost", [r for r in pipe if r["deal_stage"] == "Lost"]),
                   ("pipeline Engaging", [r for r in pipe if r["deal_stage"] == "Engaging"]),
                   ("pipeline Prospecting", [r for r in pipe if r["deal_stage"] == "Prospecting"])):
    print(name)
    for r in rows[:3]:
        print("    ", dict(r))
