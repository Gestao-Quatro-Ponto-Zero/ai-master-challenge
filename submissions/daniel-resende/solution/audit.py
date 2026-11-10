"""Data audit for the G4 Lead Scorer (challenge 003).

Standard library only. Data is located from __file__. No system clock is read:
the reference date ("today" for an open deal) is the last date present in the data.
Every number the decision report cites is printed here.
"""
import csv
import math
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------- helpers
def load(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d(s):
    return date.fromisoformat(s) if s else None


def pct(x, nd=1):
    return "   -  " if x is None else f"{100 * x:5.{nd}f}%"


def quant(v, p):
    if not v:
        return None
    s = sorted(v)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def fmt(x, nd=1):
    return "-" if x is None else f"{x:.{nd}f}"


def dist(v, nd=1):
    if not v:
        return "n=0"
    return (f"n={len(v)} min={fmt(min(v), nd)} p25={fmt(quant(v, .25), nd)} "
            f"mediana={fmt(quant(v, .5), nd)} p75={fmt(quant(v, .75), nd)} "
            f"p90={fmt(quant(v, .9), nd)} max={fmt(max(v), nd)}")


def wilson(w, n, z=1.96):
    if n == 0:
        return (None, None)
    p = w / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def gamma_q(a, x):
    """Regularised upper incomplete gamma Q(a, x) (series / continued fraction)."""
    if x <= 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1:
        ap, s, dl = a, 1 / a, 1 / a
        for _ in range(500):
            ap += 1
            dl *= x / ap
            s += dl
            if abs(dl) < abs(s) * 1e-12:
                break
        return 1 - s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1 - a
    c = 1e300
    dd = 1 / b
    h = dd
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        dd = an * dd + b
        dd = 1e-300 if abs(dd) < 1e-300 else dd
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        dd = 1 / dd
        dl = dd * c
        h *= dl
        if abs(dl - 1) < 1e-12:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_won_lost(groups, min_n=20):
    """groups: {label: (won, lost)}. Chi-square of independence, Won/Lost x group.
    Groups with n < min_n are left out (reported). Returns dict."""
    use = {k: v for k, v in groups.items() if sum(v) >= min_n}
    dropped = len(groups) - len(use)
    W = sum(v[0] for v in use.values())
    L = sum(v[1] for v in use.values())
    N = W + L
    if len(use) < 2 or W == 0 or L == 0:
        return None
    chi = 0.0
    for w, l in use.values():
        n = w + l
        ew, el = n * W / N, n * L / N
        chi += (w - ew) ** 2 / ew + (l - el) ** 2 / el
    df = len(use) - 1
    p = gamma_q(df / 2, chi / 2)
    v = math.sqrt(chi / N)
    return dict(chi=chi, df=df, p=p, v=v, kept=len(use), dropped=dropped, n=N)


def verdict_noise(r):
    if r is None:
        return "sem teste possivel"
    if r["p"] < 0.001 and r["v"] >= 0.05:
        return "ACIMA do ruido"
    if r["p"] < 0.05:
        return "marginal (p<0,05 mas efeito pequeno ou p>=0,001)"
    return "dentro do ruido"


def auc(scores, labels):
    """AUC for labels 1/0 with average ranks for ties."""
    idx = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and scores[idx[j + 1]] == scores[idx[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[idx[k]] = r
        i = j + 1
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return None
    sr = sum(r for r, y in zip(ranks, labels) if y == 1)
    return (sr - pos * (pos + 1) / 2) / (pos * neg)


def title(n, text):
    print()
    print(f"== {n}. {text} ==")


def band(x, edges, labels):
    for e, lab in zip(edges, labels):
        if x < e:
            return lab
    return labels[-1]


# ---------------------------------------------------------------- load
accounts = load("accounts.csv")
products = load("products.csv")
teams = load("sales_teams.csv")
pipe = load("sales_pipeline.csv")

print("AUDITORIA DOS DADOS - Lead Scorer (desafio 003)")
print("Fonte: submissions/daniel-resende/solution/data/*.csv. Nenhuma data de relogio do sistema e usada.")

# ---------------------------------------------------------------- 1
title(1, "Linhas e chaves por tabela")
for name, rows, key in [("accounts", accounts, "account"), ("products", products, "product"),
                        ("sales_teams", teams, "sales_agent"), ("sales_pipeline", pipe, "opportunity_id")]:
    vals = [r[key] for r in rows]
    blank = sum(1 for v in vals if v == "")
    print(f"{name:15s} linhas={len(rows):5d} colunas={list(rows[0].keys())}")
    print(f"{'':15s} chave={key}: distintas={len(set(vals))} vazias={blank} "
          f"duplicadas={len(vals) - len(set(vals))} -> {'UNICA' if len(set(vals)) == len(vals) and blank == 0 else 'NAO unica'}")
print("Chave composta a conferir: sales_teams.sales_agent distintos por manager:",
      dict(Counter(r["manager"] for r in teams)))

# ---------------------------------------------------------------- 2
title(2, "Chaves que nao casam (pipeline x accounts, products, sales_teams)")
acc_names = {r["account"] for r in accounts}
prod_names = {r["product"] for r in products}
team_names = {r["sales_agent"] for r in teams}

print("-- pipeline.product x products.product (valores exatos)")
pc = Counter(r["product"] for r in pipe)
for k, v in sorted(pc.items(), key=lambda kv: -kv[1]):
    print(f"   {k!r:20s} linhas={v:5d} {'casa' if k in prod_names else 'NAO CASA'}")
print("   produtos do catalogo sem nenhuma linha no pipeline:",
      sorted(prod_names - set(pc)) or "nenhum (antes da normalizacao)")
norm = lambda s: "".join(s.lower().split())
cat_norm = {norm(p): p for p in prod_names}
prod_map = {}
for k in pc:
    if k not in prod_names:
        if norm(k) in cat_norm:
            prod_map[k] = cat_norm[norm(k)]
print("   NORMALIZACAO aplicada (ignorar espacos e caixa, so se casar de forma unica com o catalogo):",
      prod_map or "nenhuma")
for r in pipe:
    r["product_raw"] = r["product"]
    r["product"] = prod_map.get(r["product"], r["product"])
still = Counter(r["product"] for r in pipe if r["product"] not in prod_names)
print("   apos normalizar, produtos sem casamento:", dict(still) or "nenhum")
print("   produtos do catalogo sem linha no pipeline apos normalizar:",
      sorted(prod_names - {r['product'] for r in pipe}) or "nenhum")

print("-- pipeline.account x accounts.account")
ac = Counter(r["account"] for r in pipe)
um = {k: v for k, v in ac.items() if k not in acc_names}
print(f"   valores distintos de conta no pipeline={len(ac)}; sem casamento={len(um)}; "
      f"linhas sem casamento={sum(um.values())} de {len(pipe)}")
for k, v in sorted(um.items(), key=lambda kv: -kv[1]):
    print(f"   {k!r}: {v} linhas; por estagio {dict(Counter(r['deal_stage'] for r in pipe if r['account'] == k))}")
print("   (conta vazia = sem conta; nao e corrigida, fica como 'sem conta')")
print(f"   contas de accounts.csv sem nenhuma linha no pipeline: "
      f"{sorted(acc_names - set(ac)) or 'nenhuma'}")
low = Counter(a.lower().strip() for a in acc_names)
print("   contas de accounts.csv que colidem ao ignorar caixa/espacos:",
      [k for k, v in low.items() if v > 1] or "nenhuma")

print("-- pipeline.sales_agent x sales_teams.sales_agent")
sc = Counter(r["sales_agent"] for r in pipe)
um = {k: v for k, v in sc.items() if k not in team_names}
print(f"   vendedores distintos no pipeline={len(sc)}; sem casamento em sales_teams={len(um)} {um or ''}")
nodeal = sorted(team_names - set(sc))
print(f"   vendedores de sales_teams SEM nenhum deal no pipeline: {len(nodeal)} -> {nodeal}")
for n in nodeal:
    t = next(r for r in teams if r["sales_agent"] == n)
    print(f"      {n}: manager={t['manager']} regiao={t['regional_office']}")
low = Counter(a.lower().strip() for a in team_names)
print("   nomes de vendedores que colidem ao ignorar caixa/espacos:", [k for k, v in low.items() if v > 1] or "nenhum")
print("   managers x regioes em sales_teams:",
      dict(Counter((r["manager"], r["regional_office"]) for r in teams)))

# ---------------------------------------------------------------- derive
prod = {r["product"]: r for r in products}
acc = {r["account"]: r for r in accounts}
team = {r["sales_agent"]: r for r in teams}
for r in pipe:
    r["eng"] = d(r["engage_date"])
    r["clo"] = d(r["close_date"])
    r["cv"] = float(r["close_value"]) if r["close_value"] != "" else None
    r["price"] = float(prod[r["product"]]["sales_price"]) if r["product"] in prod else None
    r["series"] = prod[r["product"]]["series"] if r["product"] in prod else None
    a = acc.get(r["account"])
    r["acc"] = a
    r["sector"] = a["sector"] if a else None
    r["manager"] = team[r["sales_agent"]]["manager"] if r["sales_agent"] in team else None
    r["region"] = team[r["sales_agent"]]["regional_office"] if r["sales_agent"] in team else None
    r["dur"] = (r["clo"] - r["eng"]).days if r["clo"] and r["eng"] else None
    r["is_open"] = r["deal_stage"] in ("Prospecting", "Engaging")
STAGES = ["Prospecting", "Engaging", "Won", "Lost"]
closed = [r for r in pipe if r["deal_stage"] in ("Won", "Lost")]
won = [r for r in closed if r["deal_stage"] == "Won"]
lost = [r for r in closed if r["deal_stage"] == "Lost"]
open_ = [r for r in pipe if r["is_open"]]
eng_open = [r for r in pipe if r["deal_stage"] == "Engaging"]
pros = [r for r in pipe if r["deal_stage"] == "Prospecting"]

# ---------------------------------------------------------------- 3
title(3, "Valores ausentes por coluna, e por coluna x deal_stage")
print(f"deal_stage (linhas): { {s: sum(1 for r in pipe if r['deal_stage'] == s) for s in STAGES} }")
for tname, rows in [("accounts", accounts), ("products", products), ("sales_teams", teams)]:
    for c in rows[0].keys():
        m = sum(1 for r in rows if r[c] == "")
        if m:
            print(f"{tname}.{c}: vazios={m} de {len(rows)}")
print("(colunas de accounts/products/sales_teams nao listadas acima nao tem vazios, exceto o que consta acima)")
print()
cols = ["opportunity_id", "sales_agent", "product", "account", "deal_stage", "engage_date", "close_date", "close_value"]
print(f"{'coluna':16s} {'total':>12s} " + " ".join(f"{s:>16s}" for s in STAGES))
for c in cols:
    tot = sum(1 for r in pipe if r[c] == "")
    cells = []
    for s in STAGES:
        rs = [r for r in pipe if r["deal_stage"] == s]
        m = sum(1 for r in rs if r[c] == "")
        cells.append(f"{m:5d}/{len(rs):5d}({100 * m / len(rs):3.0f}%)")
    print(f"{c:16s} {tot:5d}/{len(pipe):5d}  " + " ".join(f"{x:>16s}" for x in cells))
print("(celula = vazios/linhas do estagio)")

# ---------------------------------------------------------------- 4
title(4, "O que cada estagio significa nos dados")
print("Campos preenchidos por estagio (n preenchidos / n do estagio):")
for s in STAGES:
    rs = [r for r in pipe if r["deal_stage"] == s]
    fill = {c: sum(1 for r in rs if r[c] != "") for c in ["account", "engage_date", "close_date", "close_value"]}
    print(f"   {s:12s} n={len(rs):5d} " + " ".join(f"{c}={v}" for c, v in fill.items()))
print()
print("close_value em linha ABERTA (Prospecting e Engaging):")
for s in ("Prospecting", "Engaging"):
    rs = [r for r in pipe if r["deal_stage"] == s]
    print(f"   {s}: valores distintos de close_value (bruto) = {dict(Counter(r['close_value'] for r in rs))}")
print()
print("close_value em Lost:")
print(f"   valores distintos = {dict(Counter(r['close_value'] for r in lost))}")
print()
print("close_value em Won: distribuicao de close_value / sales_price do produto")
ratios = [r["cv"] / r["price"] for r in won if r["price"]]
print(f"   Won n={len(won)}; close_value: {dist([r['cv'] for r in won], 0)}")
print(f"   razao: {dist(ratios, 3)}")
print(f"   razao == 1: {sum(1 for x in ratios if abs(x - 1) < 1e-9)} ({pct(sum(1 for x in ratios if abs(x - 1) < 1e-9) / len(ratios))}); "
      f"< 1: {sum(1 for x in ratios if x < 1 - 1e-9)}; > 1: {sum(1 for x in ratios if x > 1 + 1e-9)}")
print("   por produto (n, mediana da razao, min, max):")
for p in sorted(prod, key=lambda k: float(prod[k]["sales_price"])):
    rr = [r["cv"] / r["price"] for r in won if r["product"] == p]
    print(f"      {p:15s} preco={prod[p]['sales_price']:>6s} n={len(rr):4d} "
          f"mediana={fmt(quant(rr, .5), 3)} min={fmt(min(rr) if rr else None, 3)} max={fmt(max(rr) if rr else None, 3)}")
print()
bad = sum(1 for r in closed if r["dur"] is not None and r["dur"] < 0)
print(f"Consistencia: fechados com close_date < engage_date = {bad}; "
      f"abertos com close_date preenchida = {sum(1 for r in open_ if r['close_date'])}; "
      f"fechados sem engage_date = {sum(1 for r in closed if not r['engage_date'])}")

# ---------------------------------------------------------------- 5
title(5, "Datas")
alld = [x for r in pipe for x in (r["eng"], r["clo"]) if x]
REF = max(alld)
print(f"engage_date: min={min(r['eng'] for r in pipe if r['eng'])} max={max(r['eng'] for r in pipe if r['eng'])} "
      f"(n={sum(1 for r in pipe if r['eng'])})")
print(f"close_date : min={min(r['clo'] for r in pipe if r['clo'])} max={max(r['clo'] for r in pipe if r['clo'])} "
      f"(n={sum(1 for r in pipe if r['clo'])})")
print(f"DATA DE REFERENCIA (ultima data presente nos dados) = {REF}")
last_eng_open = max(r["eng"] for r in eng_open)
print(f"Maior engage_date entre abertos Engaging = {last_eng_open}; maior close_date = {max(r['clo'] for r in closed)}")
print()
em = Counter(r["eng"].strftime("%Y-%m") for r in pipe if r["eng"])
cm = Counter(r["clo"].strftime("%Y-%m") for r in pipe if r["clo"])
cmw = Counter(r["clo"].strftime("%Y-%m") for r in won)
months = sorted(set(em) | set(cm))
print(f"{'mes':8s} {'engajados':>10s} {'fechados':>9s} {'Won':>6s} {'Lost':>6s}")
for m in months:
    print(f"{m:8s} {em.get(m, 0):10d} {cm.get(m, 0):9d} {cmw.get(m, 0):6d} {cm.get(m, 0) - cmw.get(m, 0):6d}")
print()
print("Taxa de vitoria por mes de FECHAMENTO (so descreve; o mes de fechamento nao e conhecido com o deal aberto):")
print("   " + "; ".join(f"{m}: {pct(cmw.get(m, 0) / cm[m], 0)} (n={cm[m]})" for m in sorted(cm)))
pre = [r for r in closed if r["eng"] < date(2017, 3, 1)]
print(f"TRUNCAMENTO A ESQUERDA: nenhum fechamento antes de {min(r['clo'] for r in closed)}. Fechados engajados antes dessa data: n={len(pre)}, "
      f"duracao {dist([r['dur'] for r in pre], 0)}; vit={pct(sum(1 for r in pre if r['deal_stage'] == 'Won') / len(pre))}.")
print("   Esses negocios so aparecem se ficaram abertos ate marco/2017 (duracao longa): a janela seleciona quem demorou. O inicio da serie nao e comparavel com o resto.")
for r in open_:
    r["age"] = (REF - r["eng"]).days if r["eng"] else None
ages = [r["age"] for r in eng_open]
print(f"Idade dos Engaging abertos na data de referencia (dias): {dist(ages, 0)}")
print(f"Tempo ate fechar (dias, close - engage):")
print(f"   Won : {dist([r['dur'] for r in won], 0)}")
print(f"   Lost: {dist([r['dur'] for r in lost], 0)}")
wd = [r["dur"] for r in won]
ld = [r["dur"] for r in lost]
for lab, v in (("Won", wd), ("Lost", ld)):
    print(f"   {lab}: {pct(sum(1 for x in v if x > 0) / len(v))} levaram mais de 0 dias; duracao 0 dias: {sum(1 for x in v if x == 0)}")
print("Engaging abertos por faixa de idade vs. maior duracao de Won/Lost:")
mx = max(max(wd), max(ld))
print(f"   maior duracao entre fechados = {mx} dias; Engaging com idade > {mx}: {sum(1 for a in ages if a > mx)}; "
      f"> p90 de Won ({fmt(quant(wd, .9), 0)}): {sum(1 for a in ages if a > quant(wd, .9))}; "
      f"> p90 de Lost ({fmt(quant(ld, .9), 0)}): {sum(1 for a in ages if a > quant(ld, .9))}")
for lo, hi in [(0, 30), (31, 60), (61, 90), (91, 120), (121, 180), (181, 365), (366, 10 ** 6)]:
    print(f"   idade {lo}-{hi if hi < 10 ** 6 else '+'}: {sum(1 for a in ages if lo <= a <= hi)}")

# ---------------------------------------------------------------- 6
title(6, "Conhecido com o deal aberto versus so depois de fechar (vazamento)")
print("Coluna por coluna: onde esta preenchida (n preenchidos por estagio) e veredito de uso no score de um deal ABERTO.")
leak = [
    ("opportunity_id", "identificador; nao informa; fora do score"),
    ("sales_agent", "CONHECIDO aberto (vendedor atribuido)"),
    ("product", "CONHECIDO aberto"),
    ("account", "CONHECIDO aberto SE preenchida (ver vazios por estagio)"),
    ("deal_stage", "CONHECIDO aberto, mas Prospecting/Engaging so diz 'aberto'; Won/Lost e o alvo (vazamento se usado)"),
    ("engage_date", "CONHECIDO aberto SO em Engaging (Prospecting nao tem)"),
    ("close_date", "SO APOS fechar (vazamento: vazia em aberto)"),
    ("close_value", "SO APOS fechar (vazamento: vazia em aberto; 0 em Lost denuncia o alvo)"),
]
for c, v in leak:
    fills = {s: sum(1 for r in pipe if r["deal_stage"] == s and r[c] != "") for s in STAGES}
    print(f"   {c:15s} preenchidos {fills} -> {v}")
na_open = sum(1 for r in open_ if not r["account"])
print(f"   ATENCAO: conta vazia em {na_open} de {len(open_)} abertos ({pct(na_open / len(open_))}) e em 0 de {len(closed)} fechados: conta vazia e propriedade do estagio aberto, "
      f"nao do desfecho. Nenhum modelo treinado nos fechados viu um deal sem conta; atributos de conta nao existem para esses abertos.")
print("   Derivados dos dados da conta/produto/time (setor, receita, funcionarios, local, subsidiaria, serie, preco, manager, regiao):")
print("      CONHECIDOS aberto, desde que o deal tenha conta/produto/vendedor casados (secao 2). Sao atributos atuais, nao do dia do engage;")
print("      accounts.csv nao tem data de snapshot, entao nao da para provar que valem 'no momento' (limite honesto).")
print("   Derivados de historico (negocios fechados ANTES do engage da conta ou do vendedor, secao 7): conhecidos aberto se contados so com close_date < engage_date.")
print("   Duracao (close - engage) e idade em aberto: duracao so existe apos fechar; a idade em aberto e conhecida (REF - engage).")

# ---------------------------------------------------------------- history features
def build_history(key):
    byk = defaultdict(list)
    for r in closed:
        k = r[key]
        if k and r["clo"]:
            byk[k].append(r)
    idx = {}
    for k, rs in byk.items():
        rs.sort(key=lambda r: r["clo"])
        dates = [r["clo"] for r in rs]
        cum = [0]
        for r in rs:
            cum.append(cum[-1] + (1 if r["deal_stage"] == "Won" else 0))
        idx[k] = (dates, cum)
    return idx


def hist(r, key, idx):
    k = r[key]
    if not k or k not in idx or not r["eng"]:
        return (0, None) if k and r["eng"] else (None, None)
    dates, cum = idx[k]
    n = bisect_left(dates, r["eng"])  # deals closed strictly before this engage date
    return (n, cum[n] / n if n else None)


acc_idx = build_history("account")
sel_idx = build_history("sales_agent")
for r in pipe:
    r["acc_n"], r["acc_wr"] = hist(r, "account", acc_idx)
    r["sel_n"], r["sel_wr"] = hist(r, "sales_agent", sel_idx)

# ---------------------------------------------------------------- 7
title(7, "Taxa de vitoria e tempo ate fechar por segmento (Won / (Won + Lost), com n)")
print("Cada linha: n = Won+Lost; vit = Won/n; IC95 = Wilson; dias = mediana (q1-q3) de close-engage dos fechados do grupo;")
print("dias W / dias L = mediana so de Won / so de Lost. Teste: qui-quadrado Won/Lost x grupo (grupos com n<20 fora);")
print("'ACIMA do ruido' = p<0,001 e V de Cramer>=0,05; V mede a forca (0 = nada, 1 = tudo).")
print(f"Taxa geral: Won={len(won)} Lost={len(lost)} n={len(closed)} vit={pct(len(won) / len(closed))} "
      f"IC95={tuple(round(x * 100, 1) for x in wilson(len(won), len(closed)))}")

# band edges derived from account distribution (printed)
revs = sorted(float(a["revenue"]) for a in accounts)
emps = sorted(float(a["employees"]) for a in accounts)
rq = [quant(revs, .25), quant(revs, .5), quant(revs, .75)]
eq = [quant(emps, .25), quant(emps, .5), quant(emps, .75)]
print(f"Faixas de receita (US$ mi, quartis das {len(accounts)} contas): <{rq[0]:.0f} | <{rq[1]:.0f} | <{rq[2]:.0f} | >={rq[2]:.0f}")
print(f"Faixas de funcionarios (quartis das contas): <{eq[0]:.0f} | <{eq[1]:.0f} | <{eq[2]:.0f} | >={eq[2]:.0f}")
RL = ["Q1 menor receita", "Q2", "Q3", "Q4 maior receita"]
EL = ["Q1 menos func.", "Q2", "Q3", "Q4 mais func."]
for r in pipe:
    a = r["acc"]
    r["rev_band"] = band(float(a["revenue"]), rq, RL) if a else "(sem conta)"
    r["emp_band"] = band(float(a["employees"]), eq, EL) if a else "(sem conta)"
    r["office"] = a["office_location"] if a else "(sem conta)"
    r["subs"] = ("subsidiaria" if a["subsidiary_of"] else "independente") if a else "(sem conta)"
    r["sector_l"] = r["sector"] or "(sem conta)"
    r["quarter"] = f"{r['eng'].year}-T{(r['eng'].month - 1) // 3 + 1}" if r["eng"] else "(sem engage)"
    r["prod_sector"] = f"{r['product']} x {r['sector']}" if r["sector"] else None
    r["acc_n_band"] = ("(sem conta)" if r["acc_n"] is None else "0" if r["acc_n"] == 0 else
                       "1-2" if r["acc_n"] <= 2 else "3-5" if r["acc_n"] <= 5 else "6-10" if r["acc_n"] <= 10 else "11+")
    r["acc_wr_band"] = ("sem historico" if r["acc_wr"] is None else "<50%" if r["acc_wr"] < .5 else
                        "50-60%" if r["acc_wr"] < .6 else "60-70%" if r["acc_wr"] < .7 else ">=70%")
    r["sel_n_band"] = ("(sem vendedor)" if r["sel_n"] is None else "0" if r["sel_n"] == 0 else
                       "1-9" if r["sel_n"] <= 9 else "10-29" if r["sel_n"] <= 29 else "30-99" if r["sel_n"] <= 99 else "100+")
    r["sel_wr_band"] = ("sem historico" if r["sel_wr"] is None else "<50%" if r["sel_wr"] < .5 else
                        "50-60%" if r["sel_wr"] < .6 else "60-70%" if r["sel_wr"] < .7 else ">=70%")

segments = [
    ("product", "Produto"), ("series", "Serie"), ("sector_l", "Setor da conta"),
    ("rev_band", "Receita da conta (faixa)"), ("emp_band", "Funcionarios da conta (faixa)"),
    ("office", "Sede da conta (office_location)"), ("subs", "Subsidiaria ou nao"),
    ("sales_agent", "Vendedor"), ("manager", "Manager"), ("region", "Escritorio regional"),
    ("quarter", "Trimestre do engage"),
    ("acc_n_band", "Historico: n de negocios fechados ANTES da conta"),
    ("acc_wr_band", "Historico: taxa de vitoria ANTERIOR da conta"),
    ("sel_n_band", "Historico: n de negocios fechados ANTES do vendedor"),
    ("sel_wr_band", "Historico: taxa de vitoria ANTERIOR do vendedor"),
]
seg_result = {}


def seg_table(key, label, rows=closed, show=True):
    g = defaultdict(list)
    for r in rows:
        g[str(r[key])].append(r)
    groups = {k: (sum(1 for r in v if r["deal_stage"] == "Won"), sum(1 for r in v if r["deal_stage"] == "Lost"))
              for k, v in g.items()}
    res = chi2_won_lost(groups)
    seg_result[key] = res
    if show:
        print()
        print(f"-- 7.{[s[0] for s in segments].index(key) + 1} {label}")
        print(f"   {'grupo':34s} {'n':>5s} {'vit':>7s} {'IC95':>13s} {'dias(q1-q3)':>16s} {'dW':>5s} {'dL':>5s}")
        items = sorted(g.items(), key=lambda kv: (-len(kv[1]) if key in ("sales_agent", "office", "sector_l") else 0, kv[0]))
        for k, v in items:
            w = sum(1 for r in v if r["deal_stage"] == "Won")
            n = len(v)
            lo, hi = wilson(w, n)
            du = [r["dur"] for r in v if r["dur"] is not None]
            dw = [r["dur"] for r in v if r["deal_stage"] == "Won" and r["dur"] is not None]
            dl = [r["dur"] for r in v if r["deal_stage"] == "Lost" and r["dur"] is not None]
            print(f"   {k[:34]:34s} {n:5d} {pct(w / n)} [{pct(lo, 0)},{pct(hi, 0)}] "
                  f"{fmt(quant(du, .5), 0):>5s} ({fmt(quant(du, .25), 0)}-{fmt(quant(du, .75), 0)})".ljust(78)
                  + f" {fmt(quant(dw, .5), 0):>5s} {fmt(quant(dl, .5), 0):>5s}")
        wrs = [w / (w + l) for w, l in groups.values() if w + l >= 20]
        if res:
            print(f"   spread (grupos n>=20): vit min={pct(min(wrs))} max={pct(max(wrs))} amplitude={pct(max(wrs) - min(wrs))}")
            print(f"   qui2={res['chi']:.1f} gl={res['df']} p={res['p']:.2g} V={res['v']:.3f} "
                  f"(grupos usados={res['kept']}, fora por n<20={res['dropped']}, n={res['n']}) -> {verdict_noise(res)}")
        else:
            print("   sem teste possivel")


for key, label in segments:
    seg_table(key, label)

print()
print("-- 7.x Duracao: o tempo ate fechar separa Won de Lost?")
print(f"   Won : {dist(wd, 0)}")
print(f"   Lost: {dist(ld, 0)}")
print(f"   AUC (duracao como escore de Lost; so existe apos fechar, usado aqui apenas para descrever): "
      f"{fmt(auc([r['dur'] for r in closed], [1 if r['deal_stage'] == 'Lost' else 0 for r in closed]), 3)}")

print()
print("-- 7.y Historico: cobertura (deals cujo historico anterior existe)")
for lab, key, nk in (("conta", "account", "acc_n"), ("vendedor", "sales_agent", "sel_n")):
    z = sum(1 for r in closed if r[nk] == 0)
    nn = sum(1 for r in closed if r[nk] is None)
    print(f"   {lab}: fechados com 0 negocios anteriores = {z}; sem {lab} = {nn}; "
          f"com >=1 anterior = {len(closed) - z - nn} de {len(closed)}")
print("   Historico = so negocios com close_date ESTRITAMENTE antes do engage_date do negocio.")
print("   CUIDADO: o historico so conta fechamentos a partir da primeira close_date (truncamento a esquerda, secao 5). Quem tem 'zero anteriores' e")
print("   o deal engajado no inicio da janela, que so aparece se demorou muito (duracao ~90 dias). O 'efeito' de 7.11 e 7.12 a 7.15 (vit ~72% sem historico)")
print("   e artefato da janela, nao sinal: fora da amostra a AUC desses atributos e ~0,50 (secao 10.4). Nao usar como fator.")

# ---------------------------------------------------------------- 8
title(8, "A pergunta do esfriamento, sem vazamento")
print("Entre negocios COM desfecho: dos que ainda estavam abertos com idade a (dias depois do engage; duracao > a),")
print("que parcela foi ganha e quantos dias ainda restavam (duracao - a). Prospecting nao entra (sem engage_date).")
AGES = [0, 15, 30, 45, 60, 90, 120, 150, 180, 210]
print(f"{'a':>4s} {'ainda abertos n':>16s} {'Won':>6s} {'Lost':>6s} {'vit':>7s} {'IC95':>13s} "
      f"{'resta med':>10s} {'q1':>5s} {'q3':>5s} {'rW':>5s} {'rL':>5s} | Engaging abertos c/ idade>a")
for a in AGES:
    s = [r for r in closed if r["dur"] is not None and r["dur"] > a]
    w = sum(1 for r in s if r["deal_stage"] == "Won")
    n = len(s)
    rem = [r["dur"] - a for r in s]
    rw = [r["dur"] - a for r in s if r["deal_stage"] == "Won"]
    rl = [r["dur"] - a for r in s if r["deal_stage"] == "Lost"]
    lo, hi = wilson(w, n)
    oa = sum(1 for x in ages if x > a)
    print(f"{a:4d} {n:16d} {w:6d} {n - w:6d} {pct(w / n) if n else '   -  '} "
          f"[{pct(lo, 0) if n else '-'},{pct(hi, 0) if n else '-'}] {fmt(quant(rem, .5), 0):>10s} "
          f"{fmt(quant(rem, .25), 0):>5s} {fmt(quant(rem, .75), 0):>5s} {fmt(quant(rw, .5), 0):>5s} {fmt(quant(rl, .5), 0):>5s} | {oa}")
print("(rW / rL = mediana dos dias que restavam, so Won / so Lost)")
print()
sup = max(r["dur"] for r in closed)
n_in = sum(1 for x in ages if x <= sup)
print(f"SUPORTE: o maior tempo ate fechar visto e {sup} dias. Engaging abertos com idade <= {sup}: {n_in} de {len(eng_open)} ({pct(n_in / len(eng_open))}); "
      f"com idade > {sup}: {len(eng_open) - n_in} ({pct(1 - n_in / len(eng_open))}), idade mediana {fmt(quant(ages, .5), 0)}.")
print("   Para esses ultimos nao existe um unico caso fechado comparavel: nada nos dados diz o que lhes acontece (abandonados? ainda vivos?).")
print("   Leitura da tabela: entre os que seguem abertos, a parcela ganha SOBE com a idade (perdas sao rapidas: mediana Lost 14 dias vs Won 57),")
print("   entao, dentro do suporte, 'ficar aberto mais tempo' nao reduz a chance; o que a tabela mede e a duracao restante, nao o esfriamento.")
print()
print("Mesma tabela restrita a coorte que ja teve tempo de fechar (engage_date <= REF - H), para reduzir o vies de censura:")
for H in (120, 240):
    cut = REF - timedelta(days=H)
    coh = [r for r in closed if r["eng"] <= cut]
    coh_all = [r for r in pipe if r["eng"] and r["eng"] <= cut]
    co = [r for r in coh_all if r["is_open"]]
    print(f"  H={H}: engage <= {cut}; fechados={len(coh)} abertos(Engaging)={len(co)} "
          f"(abertos/total da coorte = {pct(len(co) / len(coh_all)) if coh_all else '-'})")
    if coh:
        for a in [0, 30, 60, 90, 120]:
            if a > H:
                continue
            s = [r for r in coh if r["dur"] > a]
            w = sum(1 for r in s if r["deal_stage"] == "Won")
            print(f"     a={a:3d}: n={len(s):5d} vit={pct(w / len(s)) if s else '-'}")
print()
print("Censura: Engaging abertos (sem desfecho) no fim dos dados e seu efeito possivel nos numeros acima.")
tot_eng = len([r for r in pipe if r["deal_stage"] in ('Engaging', 'Won', 'Lost')])
print(f"   Engaging abertos={len(eng_open)} de {tot_eng} negocios engajados ({pct(len(eng_open) / tot_eng)}).")
print(f"   Por mes de engage, parcela ainda aberta:")
by_m = defaultdict(lambda: [0, 0])
for r in pipe:
    if r["eng"]:
        by_m[r["eng"].strftime("%Y-%m")][0] += 1
        by_m[r["eng"].strftime("%Y-%m")][1] += 1 if r["is_open"] else 0
for m in sorted(by_m):
    t, o = by_m[m]
    print(f"      {m}: engajados={t:5d} ainda abertos={o:4d} ({pct(o / t)})")
print("   Limites: se TODOS os Engaging abertos com idade > a virassem Won (ou todos Lost), a parcela ganha entre os 'ainda abertos em a' seria:")
print(f"   {'a':>4s} {'vit observada':>14s} {'se todos Lost':>14s} {'se todos Won':>14s} {'movimento max (pp)':>20s}")
for a in [0, 30, 60, 90, 120, 150]:
    s = [r for r in closed if r["dur"] > a]
    w = sum(1 for r in s if r["deal_stage"] == "Won")
    oa = sum(1 for x in ages if x > a)
    lowb = w / (len(s) + oa) if s else None
    upb = (w + oa) / (len(s) + oa) if s else None
    obs = w / len(s) if s else None
    mv = max(abs(upb - obs), abs(obs - lowb)) * 100 if s else None
    print(f"   {a:4d} {pct(obs):>14s} {pct(lowb):>14s} {pct(upb):>14s} {fmt(mv):>20s}")
print("   Leitura: os limites sao extremos (todos os abertos com um unico desfecho), nao uma estimativa. O vies real depende de os")
print("   abertos serem diferentes dos fechados; os dados nao permitem medir isso. Na coorte antiga (H acima) a censura e menor.")

# ---------------------------------------------------------------- 9
print()
print("-- 8 (2a tabela). Entre TODOS os deals ainda abertos na idade a, mantendo os que nunca fecham:")
FIRST = min(r["clo"] for r in closed)
print(f"   Coorte: engage_date >= {FIRST} (primeiro fechamento registrado; coorte de partida fora) e engage_date + a + 90 <= {REF}.")
print("   Aberto na idade a = (fechou com duracao > a) ou (ainda aberto na data de referencia). Janela: dias (a, a+90].")
print(f"   {'a':>4s} {'n':>6s} {'ganhos<=90d':>12s} {'perdidos<=90d':>14s} {'abertos apos 90d':>17s} {'chance ganhar 90d':>18s} {'IC95':>13s} {'chance perder':>14s} {'sem desfecho':>13s}")
cool = {}
for a in [0, 15, 30, 45, 60, 75, 90, 100, 110, 120, 130, 140]:
    co = [r for r in pipe if r["eng"] and r["eng"] >= FIRST and r["deal_stage"] != "Prospecting"
          and r["eng"] + timedelta(days=a + 90) <= REF and (r["is_open"] or r["dur"] > a)]
    w90 = sum(1 for r in co if r["deal_stage"] == "Won" and r["dur"] <= a + 90)
    l90 = sum(1 for r in co if r["deal_stage"] == "Lost" and r["dur"] <= a + 90)
    o90 = len(co) - w90 - l90
    lo, hi = wilson(w90, len(co))
    cool[a] = (len(co), w90, l90, o90)
    print(f"   {a:4d} {len(co):6d} {w90:12d} {l90:14d} {o90:17d} {pct(w90 / len(co) if co else None):>18s} "
          f"[{pct(lo, 0)},{pct(hi, 0)}] {pct(l90 / len(co) if co else None):>14s} {pct(o90 / len(co) if co else None):>13s}")
print("   Leitura: com idade crescente a chance de ganhar nos proximos 90 dias cai porque as idades altas se enchem de deals que nunca fecham.")

title("8b", "O prazo do trimestre (fim do trimestre seguinte ao do engage)")


def qdeadline(dt):
    q = (dt.month - 1) // 3 + 1
    y = dt.year
    q += 1
    if q == 5:
        q, y = 1, y + 1
    em = q * 3
    nxt = date(y + (em == 12), 1 if em == 12 else em + 1, 1)
    return nxt - timedelta(days=1)


for r in pipe:
    r["deadline"] = qdeadline(r["eng"]) if r["eng"] else None
inq = [r for r in closed if r["clo"] <= r["deadline"]]
lateq = [r for r in closed if r["clo"] > r["deadline"]]
print(f"Fechados dentro do prazo (close_date <= fim do trimestre seguinte ao do engage): {len(inq)} de {len(closed)} ({pct(len(inq) / len(closed))}); depois: {len(lateq)} ({pct(len(lateq) / len(closed))})")
for lab, rs in (("Won", won), ("Lost", lost)):
    n_in = sum(1 for r in rs if r["clo"] <= r["deadline"])
    print(f"   {lab}: dentro={n_in} depois={len(rs) - n_in}")
print(f"   Maior atraso entre fechados: {max((r['clo'] - r['deadline']).days for r in closed)} dias apos o prazo")
past = [r for r in eng_open if REF > r["deadline"]]
print(f"Engaging abertos na data de referencia {REF}: ja passaram do proprio prazo = {len(past)}; ainda dentro do prazo = {len(eng_open) - len(past)} (de {len(eng_open)})")

title(9, "Os deals abertos hoje (na data de referencia)")
print(f"Data de referencia = {REF}. Aberto = Prospecting + Engaging. Preco de lista = products.sales_price (close_value esta vazio em aberto).")
print(f"Abertos: {len(open_)}; por estagio: {dict(Counter(r['deal_stage'] for r in open_))}")
print()
per_sel = {n: [r for r in open_ if r["sales_agent"] == n] for n in sorted(team_names)}
sizes = sorted(len(v) for v in per_sel.values())
print(f"Tamanho da lista aberta por vendedor (os {len(team_names)} de sales_teams, incluindo os sem deal): {dist(sizes, 0)}")
print(f"Vendedores sem nenhum deal aberto: {sum(1 for v in per_sel.values() if not v)}  "
      f"-> {sorted(n for n, v in per_sel.items() if not v)}")
print(f"Vendedores com lista aberta < 5: {sum(1 for v in per_sel.values() if len(v) < 5)}; com Engaging abertos < 5: "
      f"{sum(1 for n in sorted(team_names) if sum(1 for r in per_sel[n] if r['deal_stage'] == 'Engaging') < 5)}")
engs = sorted(sum(1 for r in per_sel[n] if r["deal_stage"] == "Engaging") for n in sorted(team_names))
print(f"Lista so de Engaging por vendedor: {dist(engs, 0)}")
print()
print(f"{'vendedor':22s} {'manager':20s} {'reg':8s} {'abertos':>7s} {'Prosp':>6s} {'Engag':>6s} {'idade med Eng':>13s} {'valor lista (US$)':>18s}")
for n in sorted(team_names, key=lambda n: (-len(per_sel[n]), n)):
    v = per_sel[n]
    ea = [r["age"] for r in v if r["deal_stage"] == "Engaging"]
    print(f"{n:22s} {team[n]['manager']:20s} {team[n]['regional_office']:8s} {len(v):7d} "
          f"{sum(1 for r in v if r['deal_stage'] == 'Prospecting'):6d} {len(ea):6d} {fmt(quant(ea, .5), 0):>13s} "
          f"{sum(r['price'] for r in v if r['price']):18,.0f}")
print()
tot_val = sum(r["price"] for r in open_ if r["price"])
print(f"Valor de lista aberto total = US$ {tot_val:,.0f} (Engaging: US$ {sum(r['price'] for r in eng_open):,.0f}; "
      f"Prospecting: US$ {sum(r['price'] for r in pros):,.0f})")
vs = sorted(sum(r["price"] for r in v) for v in per_sel.values())
print(f"Valor de lista aberto por vendedor: {dist(vs, 0)}")
print()
print(f"{'manager':20s} {'reg':8s} {'vend':>5s} {'abertos':>8s} {'Engag':>6s} {'idade med Eng':>13s} {'valor lista (US$)':>18s}")
mg = defaultdict(list)
for r in open_:
    mg[(r["manager"], r["region"])].append(r)
for (m, g), v in sorted(mg.items(), key=lambda kv: (kv[0][1] or "", kv[0][0] or "")):
    ea = [r["age"] for r in v if r["deal_stage"] == "Engaging"]
    ns = len({r["sales_agent"] for r in v})
    print(f"{str(m):20s} {str(g):8s} {ns:5d} {len(v):8d} {len(ea):6d} {fmt(quant(ea, .5), 0):>13s} {sum(r['price'] for r in v):18,.0f}")
rg = defaultdict(list)
for r in open_:
    rg[r["region"]].append(r)
print()
print(f"{'regiao':10s} {'abertos':>8s} {'Engag':>6s} {'valor lista (US$)':>18s}")
for g, v in sorted(rg.items()):
    print(f"{str(g):10s} {len(v):8d} {sum(1 for r in v if r['deal_stage'] == 'Engaging'):6d} {sum(r['price'] for r in v):18,.0f}")
print()
print("Prospecting por regiao: " + str({g: sum(1 for r in pros if r["region"] == g) for g in sorted(rg)})
      + f"; vendedores com Prospecting: {len({r['sales_agent'] for r in pros})}")
print("Engaging abertos com idade <= maior duracao de fechados, por regiao: "
      + str({g: sum(1 for r in eng_open if r["region"] == g and r["age"] <= sup) for g in sorted(rg)}))
print("Linhas abertas a que falta algo que um escore precisaria:")
need = {
    "sem conta": lambda r: not r["account"],
    "conta que nao casa": lambda r: r["account"] and r["account"] not in acc_names,
    "sem engage_date": lambda r: not r["engage_date"],
    "sem produto casado": lambda r: r["product"] not in prod,
    "sem vendedor casado": lambda r: r["sales_agent"] not in team,
}
for lab, f in need.items():
    for s in ("Prospecting", "Engaging"):
        print(f"   {lab:22s} {s:12s}: {sum(1 for r in open_ if r['deal_stage'] == s and f(r))} de {sum(1 for r in open_ if r['deal_stage'] == s)}")
complete = [r for r in open_ if r["account"] and r["engage_date"] and r["product"] in prod and r["sales_agent"] in team]
print(f"   abertos com conta + engage_date + produto + vendedor: {len(complete)} de {len(open_)} "
      f"(Engaging completos: {sum(1 for r in complete if r['deal_stage'] == 'Engaging')} de {len(eng_open)})")
print(f"   Prospecting completos (conta, produto, vendedor; sem engage_date por definicao): "
      f"{sum(1 for r in pros if r['account'] and r['product'] in prod and r['sales_agent'] in team)} de {len(pros)}")
print("   Todo atributo derivado depende do casamento; accounts sem preenchimento: " + str({
    c: sum(1 for a in accounts if a[c] == "") for c in accounts[0].keys() if any(a[c] == "" for a in accounts)}))

# ---------------------------------------------------------------- 10
title(10, "Cada suposicao do PRODUTO.md, testada")

# 10.1 sellers
n_sel = len(teams)
with_deal = len(set(sc) & team_names)
ge5 = sum(1 for n in sorted(team_names) if len(per_sel[n]) >= 5)
ge5e = sum(1 for n in sorted(team_names) if sum(1 for r in per_sel[n] if r["deal_stage"] == "Engaging") >= 5)
v = "SUSTENTA" if with_deal == 35 and ge5 == 35 else "PARCIAL" if with_deal >= 30 else "NAO SUSTENTA"
print(f"10.1 'Sao 35 vendedores e cada um tem lista aberta para um top cinco' -> {v}")
print(f"     vendedores em sales_teams={n_sel}; com algum deal no pipeline={with_deal}; com >=5 abertos={ge5}; "
      f"com >=5 Engaging abertos (os que tem engage_date)={ge5e}; sem deal={len(nodeal)}.")
print(f"     lista aberta por vendedor (35): {dist(sizes, 0)}")

# 10.2 sort by value
print()
pr_rows = []
for p in prod:
    rs = [r for r in closed if r["product"] == p]
    w = sum(1 for r in rs if r["deal_stage"] == "Won")
    pr_rows.append((float(prod[p]["sales_price"]), p, len(rs), w))
pr_rows.sort()


def spearman(x, y):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for i, k in enumerate(s):
            r[k] = i + 1
        return r
    a, b = rk(x), rk(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


sp = spearman([x[0] for x in pr_rows], [x[3] / x[2] for x in pr_rows])
print("10.2 'Ordenar por valor nao resolve' (preco de lista x taxa de vitoria)")
for price, p, n, w in pr_rows:
    lo, hi = wilson(w, n)
    print(f"     {p:15s} preco={price:8.0f} n={n:5d} vit={pct(w / n)} IC95=[{pct(lo, 0)},{pct(hi, 0)}]")
print(f"     Spearman(preco, vit) entre os 7 produtos = {fmt(sp, 2)}")
# deal-level: win rate by price tertile of closed deals
pr_all = sorted(r["price"] for r in closed)
t1, t2 = quant(pr_all, 1 / 3), quant(pr_all, 2 / 3)
tert = defaultdict(lambda: [0, 0])
for r in closed:
    k = "barato" if r["price"] <= t1 else "medio" if r["price"] <= t2 else "caro"
    tert[k][0 if r["deal_stage"] == "Won" else 1] += 1
print("     por terco de preco dos deals fechados: " + "; ".join(
    f"{k}: n={sum(v)} vit={pct(v[0] / sum(v))}" for k, v in sorted(tert.items())))
# does price ordering rank deals by *expected value* the same as by price? rank correlation price vs price*winrate per product
ev = [x[0] * x[3] / x[2] for x in pr_rows]
sp2 = spearman([x[0] for x in pr_rows], ev)
print(f"     Spearman(preco, preco x taxa) entre produtos = {fmt(sp2, 2)}; valor esperado por produto (US$): "
      + ", ".join(f"{x[1]}={e:,.0f}" for x, e in zip(pr_rows, ev)))
# top-5 by price of open deals per seller vs. top-5 by price*product win rate
prod_wr = {p: w / n for _, p, n, w in pr_rows}
diff = 0
tot = 0
for n_, v_ in per_sel.items():
    if len(v_) >= 5:
        a_ = {r["opportunity_id"] for r in sorted(v_, key=lambda r: (-r["price"], r["opportunity_id"]))[:5]}
        b_ = {r["opportunity_id"] for r in sorted(v_, key=lambda r: (-r["price"] * prod_wr[r["product"]], r["opportunity_id"]))[:5]}
        diff += 5 - len(a_ & b_)
        tot += 5
print(f"     Top 5 por preco x top 5 por preco x taxa do produto, nos {sum(1 for v_ in per_sel.values() if len(v_) >= 5)} vendedores com >=5 abertos: "
      f"{diff} de {tot} posicoes mudam ({pct(diff / tot)}).")
r_ = chi2_won_lost({p: (w, n - w) for _, p, n, w in pr_rows})
spread = max(prod_wr.values()) - min(prod_wr.values())
v = "SUSTENTA" if (r_ and r_["p"] < 0.05) and spread > 0.03 else "NAO SUSTENTA"
print(f"     Taxa entre produtos: amplitude={pct(spread)}, qui2 p={r_['p']:.2g} V={r_['v']:.3f}. -> {v}")
print("     Leitura: a taxa e plana entre produtos (dentro do ruido), entao a chance por produto nao reordena a lista: ordenar por valor e")
print("     equivalente a ordenar por valor esperado por produto. Entre deals vivos a ordem por valor e a ordem certa.")
old_ = [r for r in eng_open if r["age"] > sup]
old_val = sum(r["price"] for r in old_)
print(f"     Segunda metade: Engaging abertos mais velhos que a maior duracao de qualquer fechado ({sup} dias): {len(old_)} de {len(eng_open)} "
      f"({pct(len(old_) / len(eng_open))}); carregam US$ {old_val:,.0f} de US$ {sum(r['price'] for r in eng_open):,.0f} de lista Engaging "
      f"({pct(old_val / sum(r['price'] for r in eng_open))}) e {pct(old_val / tot_val)} da lista aberta total (US$ {tot_val:,.0f}).")
print("     A ordem por valor ignora quais deals ja passaram do ponto de fechar.")
print("     -> PARCIAL: entre deals vivos a ordem por valor e a ordem certa (taxa plana por produto); sobre a lista aberta inteira nao e.")

# 10.3 time lowers chance
print()
print("10.3 'O tempo no funil reduz a chance' (secao 8)")
base = [r for r in closed if r["dur"] is not None]
wr0 = sum(1 for r in base if r["deal_stage"] == "Won") / len(base)
rows3 = []
for a in (0, 30, 60, 90, 120):
    s = [r for r in base if r["dur"] > a]
    w = sum(1 for r in s if r["deal_stage"] == "Won")
    rows3.append((a, len(s), w, w / len(s) if s else None))
for a, n, w, p_ in rows3:
    lo, hi = wilson(w, n) if n else (None, None)
    print(f"     idade>{a:3d}: n={n:5d} vit={pct(p_)} IC95=[{pct(lo, 0)},{pct(hi, 0)}]")
n30 = next(x for x in rows3 if x[0] == 30)
n90 = next(x for x in rows3 if x[0] == 90)
lo30, hi30 = wilson(n30[2], n30[1])
lo90, hi90 = wilson(n90[2], n90[1]) if n90[1] else (None, None)
if n90[1] and hi90 < lo30:
    v = "SUSTENTA (cai alem do IC)"
elif n90[1] and n90[3] < n30[3] - 0.02:
    v = "PARCIAL (cai, mas dentro do IC)"
else:
    v = "NAO SUSTENTA"
print(f"     Vista 1, entre deals que FECHAM (secao 8, 1a tabela): 0 -> 90 dias: {pct(rows3[0][3])} -> {pct(n90[3]) if n90[3] is not None else '-'} -> {v}")
print("     Vista 2, entre TODOS os abertos na idade a, chance de ganhar nos 90 dias seguintes (secao 8, 2a tabela): "
      + "; ".join(f"a={a}: {pct(cool[a][1] / cool[a][0], 1).strip()} (n={cool[a][0]})" for a in (0, 30, 60, 90, 120, 140)))
c0, c90, c140 = cool[0], cool[90], cool[140]
lo0, hi0 = wilson(c0[1], c0[0])
lo9, hi9 = wilson(c90[1], c90[0])
v2 = "cai alem do IC" if hi9 < lo0 else "nao cai alem do IC"
print(f"     Chance de ganhar em 90 dias: {pct(c0[1] / c0[0])} (a=0) -> {pct(c90[1] / c90[0])} (a=90) -> {pct(c140[1] / c140[0])} (a=140); {v2}.")
print("     VEREDITO 10.3: PARCIAL. Entre deals que fecham, a idade nao reduz a parcela ganha; entre todos os abertos, a chance de ganhar nos proximos 90 dias")
print("     cai com a idade, porque as idades altas se enchem de deals que nunca fecham.")
print("     Ressalva: a censura (secao 8) pode mover estes numeros ate os limites ali impressos.")
print(f"     Tambem: {sum(1 for a in ages if a > quant(wd, .9))} Engaging abertos ja passaram do p90 do tempo dos Won "
      f"({fmt(quant(wd, .9), 0)} dias): candidatos reais a 'esfriando'.")

# 10.4 separation known while open
print()
print("10.4 'Ha algo conhecido em aberto que separa ganhos de perdidos, e com que forca'")
print("     Teste fora da amostra: aprende a taxa de cada grupo nos fechados com close_date <= corte; avalia nos fechados DEPOIS,")
print("     usando so atributos conhecidos no engage. AUC 0,5 = nada; 1,0 = perfeito. (Aproximacao: o corte e por close_date.)")
cd = sorted(r["clo"] for r in closed)
cutoff = cd[len(cd) // 2]
tr = [r for r in closed if r["clo"] <= cutoff]
te = [r for r in closed if r["clo"] > cutoff]
print(f"     corte = {cutoff}; treino n={len(tr)} teste n={len(te)}; taxa treino={pct(sum(1 for r in tr if r['deal_stage'] == 'Won') / len(tr))} "
      f"teste={pct(sum(1 for r in te if r['deal_stage'] == 'Won') / len(te))}")
print(f"     {'atributo':34s} {'AUC':>6s} {'V (todos)':>10s} {'p':>9s} veredito-ruido")
feats = ["product", "series", "sector_l", "rev_band", "emp_band", "office", "subs", "sales_agent", "manager", "region",
         "acc_n_band", "acc_wr_band", "sel_n_band", "sel_wr_band", "prod_sector"]
glob = sum(1 for r in tr if r["deal_stage"] == "Won") / len(tr)
auc_res = {}
for f in feats:
    g = defaultdict(lambda: [0, 0])
    for r in tr:
        g[str(r[f])][0 if r["deal_stage"] == "Won" else 1] += 1
    sc_ = []
    for r in te:
        w, l = g.get(str(r[f]), (0, 0))
        k = 10  # shrink toward the global rate
        sc_.append((w + k * glob) / (w + l + k))
    a_ = auc(sc_, [1 if r["deal_stage"] == "Won" else 0 for r in te])
    auc_res[f] = a_
    if f not in seg_result:
        seg_table(f, f, show=False)
    rr = seg_result[f]
    print(f"     {f:34s} {fmt(a_, 3):>6s} {fmt(rr['v'] if rr else None, 3):>10s} {('%.2g' % rr['p']) if rr else '-':>9s} {verdict_noise(rr)}")
# naive multi-feature: average of shrunk rates of product, sector, acc_wr (kept honest and simple)
mf = ["product", "sector_l", "rev_band", "sales_agent", "acc_wr_band", "sel_wr_band"]
tabs = {}
for f in mf:
    g = defaultdict(lambda: [0, 0])
    for r in tr:
        g[str(r[f])][0 if r["deal_stage"] == "Won" else 1] += 1
    tabs[f] = g
sc_ = []
for r in te:
    ss = []
    for f in mf:
        w, l = tabs[f].get(str(r[f]), (0, 0))
        ss.append((w + 10 * glob) / (w + l + 10))
    sc_.append(sum(ss) / len(ss))
auc_mf = auc(sc_, [1 if r["deal_stage"] == "Won" else 0 for r in te])
print(f"     media simples das taxas encolhidas de {mf}: AUC = {fmt(auc_mf, 3)}")
best = max((v_ for v_ in auc_res.values() if v_ is not None))
v = "SUSTENTA" if auc_mf and auc_mf >= 0.60 else "PARCIAL" if auc_mf and auc_mf >= 0.55 else "NAO SUSTENTA"
print(f"     melhor atributo isolado AUC={fmt(best, 3)}; combinacao simples AUC={fmt(auc_mf, 3)} -> {v} "
      f"(limiares fixos: >=0,60 sustenta, 0,55-0,60 parcial)")

# 10.5 similar cases
print()
print("10.5 'Ha casos parecidos suficientes (produto x setor) para dizer o que fecha e o que nao fecha'")
cells = defaultdict(lambda: [0, 0])
for r in closed:
    if r["prod_sector"]:
        cells[r["prod_sector"]][0 if r["deal_stage"] == "Won" else 1] += 1
nc = len(cells)
ncl = sum(sum(v_) for v_ in cells.values())
for thr in (10, 30, 100):
    big = {k: v_ for k, v_ in cells.items() if sum(v_) >= thr}
    print(f"     celulas com n>={thr:3d}: {len(big)} de {nc} possiveis (7 produtos x {len({r['sector'] for r in pipe if r['sector']})} setores = "
          f"{7 * len({r['sector'] for r in pipe if r['sector']})}); cobrem {sum(sum(v_) for v_ in big.values())} de {ncl} fechados "
          f"({pct(sum(sum(v_) for v_ in big.values()) / ncl)})")
print(f"     tamanho das celulas: {dist([sum(v_) for v_ in cells.values()], 0)}")
rc = chi2_won_lost({k: tuple(v_) for k, v_ in cells.items()}, min_n=30)
if rc:
    print(f"     taxa de vitoria entre celulas n>=30: qui2={rc['chi']:.1f} gl={rc['df']} p={rc['p']:.2g} V={rc['v']:.3f} "
          f"-> {verdict_noise(rc)}")
big = {k: v_ for k, v_ in cells.items() if sum(v_) >= 30}
if big:
    wr_c = sorted(((v_[0] / sum(v_), k, sum(v_)) for k, v_ in big.items()))
    print("     3 menores e 3 maiores taxas (celulas n>=30): " +
          "; ".join(f"{k} {pct(x)} n={n}" for x, k, n in wr_c[:3]) + " | " + "; ".join(f"{k} {pct(x)} n={n}" for x, k, n in wr_c[-3:]))
share = sum(sum(v_) for v_ in big.values()) / ncl if ncl else 0
v = "SUSTENTA" if share >= 0.8 and rc and verdict_noise(rc).startswith("ACIMA") else "PARCIAL" if share >= 0.5 else "NAO SUSTENTA"
if rc and not verdict_noise(rc).startswith("ACIMA"):
    v = "NAO SUSTENTA (celulas existem, mas as taxas nao diferem alem do ruido)" if share >= 0.5 else "NAO SUSTENTA"
print(f"     -> {v}")

# 10.6 manager questions
print()
print("10.6 'As tres perguntas do gestor se respondem com estas colunas'")
p90w = quant(wd, .9)
print(f"     (a) pipeline parado: idade dos Engaging abertos por vendedor; 'parado' = idade > p90 do tempo dos Won ({fmt(p90w, 0)} dias).")
stall = {}
for n in sorted(team_names):
    e = [r for r in per_sel[n] if r["deal_stage"] == "Engaging"]
    stall[n] = (len(e), sum(1 for r in e if r["age"] > p90w))
tot_e = sum(x[0] for x in stall.values())
tot_s = sum(x[1] for x in stall.values())
shares = sorted(x[1] / x[0] for x in stall.values() if x[0] >= 5)
print(f"         parados no total = {tot_s} de {tot_e} Engaging abertos ({pct(tot_s / tot_e)}); "
      f"parcela parada por vendedor (>=5 Engaging): {dist([100 * x for x in shares], 0)} (%)")
rs_ = chi2_won_lost({n: (x[1], x[0] - x[1]) for n, x in stall.items() if x[0] > 0}, min_n=5)
print(f"         vendedores diferem na parcela parada? " + (f"qui2={rs_['chi']:.1f} gl={rs_['df']} p={rs_['p']:.2g} -> {verdict_noise(rs_)}" if rs_ else "sem teste"))
print("     (b) insiste no que nao fecha: parcela da carteira aberta dos vendedores em produto x setor de taxa historica baixa.")
if big:
    lowcut = quant([v_[0] / sum(v_) for v_ in big.values()], .25)
    lowcells = {k for k, v_ in big.items() if v_[0] / sum(v_) <= lowcut}
    print(f"         celula 'de baixa taxa' = n>=30 e taxa <= p25 das celulas ({pct(lowcut)}); {len(lowcells)} celulas.")
    ins = {}
    for n in sorted(team_names):
        e = [r for r in per_sel[n] if r["prod_sector"]]
        ins[n] = (sum(1 for r in e if r["prod_sector"] in lowcells), len(e))
    sh = sorted(x[0] / x[1] for x in ins.values() if x[1] >= 5)
    print(f"         parcela por vendedor (>=5 abertos): {dist([100 * x for x in sh], 0)} (%)")
    rr = chi2_won_lost({n: (x[0], x[1] - x[0]) for n, x in ins.items() if x[1] > 0}, min_n=5)
    print(f"         vendedores diferem? " + (f"qui2={rr['chi']:.1f} gl={rr['df']} p={rr['p']:.2g} -> {verdict_noise(rr)}" if rr else "sem teste"))
print("         Alternativa: o vendedor tem taxa propria abaixo da media? (secao 7.8):",
      verdict_noise(seg_result['sales_agent']))
print("     (c) onde esta o valor do time: soma do preco de lista dos abertos por manager/regiao (secao 9): pode ser respondida (e fato da tabela).")
print("         Ressalva: e preco de lista; close_value de Won difere do preco (secao 4); valor esperado exige a taxa por segmento (secao 7).")
ok_a = rs_ is not None and rs_["p"] < 0.001 and tot_s / tot_e < 0.8
if tot_s / tot_e >= 0.8:
    print(f"         (a) ressalva: {pct(tot_s / tot_e)} dos Engaging abertos passam do p90 dos Won; o limiar nao discrimina (secao 8, suporte).")
ok_b = (rr is not None and rr["p"] < 0.001) if big else False
sel_sig = seg_result["sales_agent"] and seg_result["sales_agent"]["p"] < 0.001
print(f"     Veredito: (a) {'sustenta, vendedores diferem' if ok_a else 'responde so em fato bruto (idade), sem diferenca provada entre vendedores'}; "
      f"(b) {'sustenta, vendedores diferem' if ok_b else 'responde so em fato bruto, sem diferenca provada entre vendedores'}; "
      f"(c) sustenta como fato de lista -> "
      f"{'SUSTENTA' if ok_a and ok_b else 'PARCIAL'}")

print()
print("== FIM ==")
