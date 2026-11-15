#!/usr/bin/env python3
# O cliente do deal pertence a regional do vendedor? Fechados x abertos.
import csv, os, sys
from collections import defaultdict, Counter
DD = sys.argv[1]
def load(n):
    with open(os.path.join(DD, n), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def pct(a, b): return 100.0*a/b if b else float("nan")
teams = {r["sales_agent"]: r["regional_office"] for r in load("sales_teams.csv")}
pipe = load("sales_pipeline.csv")
for r in pipe:
    r["acc"] = r["account"].strip(); r["reg"] = teams[r["sales_agent"]]
closed = [r for r in pipe if r["deal_stage"] in ("Won", "Lost")]
cr = defaultdict(Counter)
for r in closed: cr[r["acc"]][r["reg"]] += 1
home = {a: c.most_common(1)[0][0] for a, c in cr.items()}
pure = sum(1 for c in cr.values() if len(c) == 1)
print("clientes: %d | atendidos por uma unica regional nos fechados: %d | por regional principal: %s" % (len(cr), pure, dict(Counter(home.values()))))
print("clientes com fechados em mais de uma regional:", {a: dict(c) for a, c in cr.items() if len(c) > 1})
for st in ("Won", "Lost", "Engaging", "Prospecting"):
    g = [r for r in pipe if r["deal_stage"] == st and r["acc"]]
    m = sum(1 for r in g if home[r["acc"]] == r["reg"])
    print("%-11s com cliente %4d | cliente e da regional do vendedor: %4d (%.1f%%)" % (st, len(g), m, pct(m, len(g))))
# pares vendedor-cliente: nos fechados, quantos pares distintos; nos abertos, quantos pares nunca aparecem em fechados
pairs = {(r["sales_agent"], r["acc"]) for r in closed}
op = [r for r in pipe if r["deal_stage"] in ("Engaging", "Prospecting") and r["acc"]]
print("pares vendedor-cliente distintos nos fechados: %d (de %d possiveis)" % (len(pairs), 30*85))
print("abertos com cliente: %d | par vendedor-cliente que NUNCA aparece em deal fechado: %d (%.1f%%)" % (
    len(op), sum(1 for r in op if (r["sales_agent"], r["acc"]) not in pairs), pct(sum(1 for r in op if (r["sales_agent"], r["acc"]) not in pairs), len(op))))
# esperado ao acaso: cada vendedor tem ~30 clientes de 85
exp = sum(1 - len({a for (s, a) in pairs if s == r["sales_agent"]})/85.0 for r in op)
print("   esperado se o cliente do deal aberto fosse sorteado entre os 85: %.0f (%.1f%%)" % (exp, pct(exp, len(op))))
