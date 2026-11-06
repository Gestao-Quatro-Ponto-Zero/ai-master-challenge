"""Lead Scorer: prioriza deals abertos do CRM e explica o porquê.

Somente stdlib (Python 3.9+). Uso:
    python scorer.py                 # gera app/data.js e ../docs/validacao.md
    python scorer.py --csv out.csv   # também exporta o pipeline priorizado (CSV ; para Excel pt-BR)

Score 0-100 = Valor (0-60) + Momento (0-40). Detalhes: ../docs/logica.md

O score é uma POLÍTICA de priorização, não um preditor de ganho. No backtest
nenhum atributo (vendedor, conta, produto...) nem a idade do deal ordenam
ganhos melhor que o acaso (AUC ~0,50-0,55). O que é real e acionável:
  - valor do deal (preço de tabela, 500x de variação)
  - em que momento do ciclo ele está: metade das perdas acontece nos 14
    primeiros dias, todo deal histórico fechou até o dia 138
Fatores de atributo entram sozinhos se passarem no gate em todos os cortes.
"""
import csv
import datetime as dt
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# Data de referência = último close_date do dataset. Em produção: date.today().
REF_DATE = dt.date(2017, 12, 31)
PRIOR_K = 40          # shrinkage: grupo com 40 deals pesa metade a própria taxa, metade a média
EARLY_WINDOW = 14     # dias: janela onde se concentra metade das perdas
FINAL_STRETCH = 90    # dias: a partir daqui o deal entra na reta final antes do teto histórico
GATE = 0.55           # AUC mínimo, em TODOS os cortes do backtest, para um atributo pontuar
CUTOFFS = (dt.date(2017, 5, 1), dt.date(2017, 7, 1), dt.date(2017, 9, 1))
PTS_VALOR, PTS_MOMENTO = 60, 40

MOMENTO = {"janela_risco": 40, "reta_final": 35, "maduro": 25, "prospecting": 10, "zumbi": 0}
ACTIONS = {
    "janela_risco": "Contato urgente",
    "reta_final": "Empurrar fechamento",
    "maduro": "Manter cadência",
    "prospecting": "Avançar para Engaging",
    "zumbi": "Verificar no CRM",
}

# Moeda: o dataset está em US$. Convertido para R$ pela PTAX de venda do Banco Central
# (https://olinda.bcb.gov.br/olinda/servico/PTAX, CotacaoDolarDia). Taxa fixa para o
# resultado ser reproduzível; atualize as duas linhas ao trocar a data de referência.
USD_BRL = 5.4621
USD_BRL_DATE = "2026-11-05"

# Correções de qualidade de dado encontradas na EDA
PRODUCT_FIX = {"GTXPro": "GTX Pro"}
SECTOR_FIX = {"technolgy": "technology"}
SECTOR_PT = {"employment": "Recrutamento", "entertainment": "Entretenimento", "finance": "Finanças",
             "marketing": "Marketing", "medical": "Saúde", "retail": "Varejo", "services": "Serviços",
             "software": "Software", "technology": "Tecnologia", "telecommunications": "Telecom"}


def _read(name, data_dir):
    with open(os.path.join(data_dir, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _date(s):
    return dt.date.fromisoformat(s) if s else None


def br_names(data_dir=DATA):
    """Mapa 1:1 de vendedores, managers e regiões para nomes brasileiros (data/nomes_br.csv).

    Os CSVs originais ficam intactos; a troca é só de exibição e é auditável.
    Sem o arquivo, os nomes originais são usados.
    """
    m = {"vendedor": {}, "manager": {}, "regiao": {}}
    if os.path.exists(os.path.join(data_dir, "nomes_br.csv")):
        for r in _read("nomes_br.csv", data_dir):
            m[r["tipo"]][r["original"]] = r["br"]
    for tipo, d in m.items():
        if len(set(d.values())) != len(d):
            raise ValueError(f"nomes_br.csv: nome brasileiro repetido em {tipo}")
    return m


def load(data_dir=DATA):
    accounts = {a["account"]: {**a, "sector": SECTOR_FIX.get(a["sector"], a["sector"])}
                for a in _read("accounts.csv", data_dir)}
    products = {p["product"]: p for p in _read("products.csv", data_dir)}
    br = br_names(data_dir)
    teams = {}
    for t in _read("sales_teams.csv", data_dir):
        agent = br["vendedor"].get(t["sales_agent"], t["sales_agent"])
        teams[agent] = {"sales_agent": agent, "original": t["sales_agent"],
                        "manager": br["manager"].get(t["manager"], t["manager"]),
                        "regional_office": br["regiao"].get(t["regional_office"], t["regional_office"])}
    deals = []
    for r in _read("sales_pipeline.csv", data_dir):
        prod = PRODUCT_FIX.get(r["product"], r["product"])
        if prod not in products:
            raise ValueError(f"produto desconhecido: {r['product']}")
        agent = br["vendedor"].get(r["sales_agent"], r["sales_agent"])
        if agent not in teams:
            raise ValueError(f"vendedor sem time: {r['sales_agent']}")
        if r["deal_stage"] == "Engaging" and not r["engage_date"]:
            raise ValueError(f"deal Engaging sem engage_date: {r['opportunity_id']}")
        deals.append({
            "id": r["opportunity_id"], "agent": agent, "product": prod,
            "account": r["account"] or None, "stage": r["deal_stage"],
            "engage": _date(r["engage_date"]), "close": _date(r["close_date"]),
            "value": int(r["close_value"]) if r["close_value"] else None,
        })
    return accounts, products, teams, deals


def logit(p):
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def cycle(d):
    return (d["close"] - d["engage"]).days


def smoothed(c, prior, k=PRIOR_K):
    wins, n = c
    return (wins + k * prior) / (n + k)


# ---------------------------------------------------------------- fit

def fit(closed, factors=()):
    """Aprende a partir de deals Won/Lost: média, contagens por grupo, curva de sobrevivência."""
    base = sum(d["stage"] == "Won" for d in closed) / len(closed)
    cnt = {k: defaultdict(lambda: [0, 0]) for k in ("agent", "product", "account", "agent_product")}
    for d in closed:
        w = d["stage"] == "Won"
        for key, val in (("agent", d["agent"]), ("product", d["product"]),
                         ("account", d["account"]), ("agent_product", (d["agent"], d["product"]))):
            cnt[key][val][0] += w
            cnt[key][val][1] += 1
    cycles = [cycle(d) for d in closed]
    max_cycle = max(cycles)
    # survival[t] = (ganhos, total) entre deals cujo ciclo foi >= t dias
    hist = defaultdict(lambda: [0, 0])
    for d, c in zip(closed, cycles):
        hist[c][0] += d["stage"] == "Won"
        hist[c][1] += 1
    survival, w_acc, n_acc = [None] * (max_cycle + 2), 0, 0
    survival[max_cycle + 1] = (0, 0)
    for t in range(max_cycle, -1, -1):
        w_acc += hist[t][0]
        n_acc += hist[t][1]
        survival[t] = (w_acc, n_acc)
    losses = [c for d, c in zip(closed, cycles) if d["stage"] == "Lost"]
    early_loss = sum(c <= EARLY_WINDOW for c in losses) / len(losses)
    return {"base": base, "n": len(closed), "cnt": cnt, "max_cycle": max_cycle,
            "survival": survival, "early_loss": early_loss, "factors": list(factors)}


# ---------------------------------------------------------------- predict

def history(model, d):
    """Taxas históricas do vendedor x produto e da conta (cruas e suavizadas)."""
    base, cnt = model["base"], model["cnt"]
    agent_rate = smoothed(cnt["agent"].get(d["agent"], [0, 0]), base)
    ap = cnt["agent_product"].get((d["agent"], d["product"]), [0, 0])
    out = {"vendedor_produto": {"rate": ap[0] / ap[1] if ap[1] else None, "n": ap[1],
                                "smooth": smoothed(ap, agent_rate)}}
    if d["account"]:
        ac = cnt["account"].get(d["account"], [0, 0])
        out["conta"] = {"rate": ac[0] / ac[1] if ac[1] else None, "n": ac[1], "smooth": smoothed(ac, base)}
    return out


def time_prob(model, age):
    """P(ganho | deal aberto há `age` dias e ainda não fechado).

    Quem está aberto há `age` dias vai ter ciclo >= age+1, por isso survival[age+1].
    None = sem dado: Prospecting (nunca observamos Prospecting -> Won) ou zumbi (fora da curva).
    """
    if age is None or age > model["max_cycle"]:
        return None
    return smoothed(model["survival"][age + 1], model["base"])


def chance(model, d, age):
    """P(ganho): curva de sobrevivência + atributos aprovados no gate (hoje nenhum)."""
    p = time_prob(model, age)
    if p is None:
        return None
    x = logit(p)
    h = history(model, d)
    for k in model["factors"]:
        if k in h:
            x += logit(h[k]["smooth"]) - logit(model["base"])
    return sigmoid(x)


def deal_age(d, ref=REF_DATE):
    return (ref - d["engage"]).days if d["engage"] else None


def state(model, d, age):
    if age is None:
        return "prospecting"
    if age > model["max_cycle"]:
        return "zumbi"
    if age <= EARLY_WINDOW:
        return "janela_risco"
    return "reta_final" if age >= FINAL_STRETCH else "maduro"


def value_pts(price, lo, hi):
    return PTS_VALOR * (math.log(price) - math.log(lo)) / (math.log(hi) - math.log(lo))


# ---------------------------------------------------------------- explicações

def brl(usd):
    return round(usd * USD_BRL)


def fmt_brl(v):
    """Valor já em reais -> 'R$ 1.234'."""
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def fmt_brl_mi(usd_mi):
    """Receita em milhões de US$ -> 'R$ 6,0 bi' ou 'R$ 873 mi'."""
    v = usd_mi * USD_BRL
    if v >= 1000:
        return "R$ " + f"{v / 1000:.1f}".replace(".", ",") + " bi"
    return f"R$ {v:.0f} mi"


def reasons(d, st, age, p, price, model, accounts):
    """Frases curtas em PT-BR. Tipos: + positivo, - negativo, ! alerta, i info, h histórico (não pontua)."""
    out = []
    mc = model["max_cycle"]
    if st == "zumbi":
        out.append(("!", f"Aberto há {age} dias. Nenhum dos {model['n']:,} deals do histórico levou mais de {mc} dias "
                         "para fechar. Confirme no CRM se ainda está vivo: requalifique ou encerre".replace(",", ".")))
    elif st == "janela_risco":
        out.append(("!", f"Engajado há {age} dias: {model['early_loss']:.0%} das perdas acontecem até o dia "
                         f"{EARLY_WINDOW}. Um contato agora pesa mais que em qualquer outro momento"))
    elif st == "reta_final":
        left = mc - age
        when = "hoje é o último dia" if left == 0 else "falta 1 dia" if left == 1 else f"faltam {left} dias"
        out.append(("!", f"Engajado há {age} dias: {when} dentro do maior ciclo já visto ({mc}). Hora de pedir a decisão"))
    elif st == "maduro":
        out.append(("+", f"Engajado há {age} dias: passou da janela de perda precoce"))
    else:
        out.append(("i", "Em prospecção: sem data de engajamento. O histórico não tem como medir a chance"))
    if p is not None:
        out.append(("i", f"Deals nesta idade fecharam {p:.0%} das vezes (média {model['base']:.0%}): "
                         "quase igual para todos, por isso não pesa no score"))
    if price >= 4000:
        out.append(("+", f"Ticket alto: {d['product']} tabela {fmt_brl(brl(price))}"))
    elif price <= 600:
        out.append(("-", f"Ticket baixo: {d['product']} tabela {fmt_brl(brl(price))}"))
    else:
        out.append(("i", f"Ticket médio: {d['product']} tabela {fmt_brl(brl(price))}"))
    if d["account"] is None:
        out.append(("!", "Conta não preenchida no CRM"))
    elif d["account"] in accounts:
        a = accounts[d["account"]]
        emp = f"{int(a['employees']):,}".replace(",", ".")
        out.append(("i", f"{SECTOR_PT.get(a['sector'], a['sector'].capitalize())}, receita {fmt_brl_mi(float(a['revenue']))}/ano, {emp} funcionários"))
    h = history(model, d)
    ap = h["vendedor_produto"]
    if ap["n"]:
        out.append(("h", f"{d['agent'].split()[0]} fechou {ap['rate']:.0%} de {d['product']} ({ap['n']} deals)"))
    if "conta" in h and h["conta"]["n"]:
        out.append(("h", f"{d['account']} converteu {h['conta']['rate']:.0%} ({h['conta']['n']} deals)"))
    return out


# ---------------------------------------------------------------- pipeline

def score_deal(model, d, price, lo, hi, ref=REF_DATE):
    age = deal_age(d, ref)
    st = state(model, d, age)
    p = chance(model, d, age)
    v_pts = value_pts(price, lo, hi)
    m_pts = MOMENTO[st]
    return {"age": age, "state": st, "p": None if p is None else round(p, 3),
            "ev": None if p is None else brl(p * price),
            "pts": {"valor": round(v_pts, 1), "momento": m_pts},
            "score": round(v_pts + m_pts), "action": ACTIONS[st]}


def score_open(model, accounts, products, teams, deals, ref=REF_DATE):
    prices = [int(p["sales_price"]) for p in products.values()]
    lo, hi = min(prices), max(prices)
    rows = []
    for d in deals:
        if d["stage"] not in ("Prospecting", "Engaging"):
            continue
        price = int(products[d["product"]]["sales_price"])
        s = score_deal(model, d, price, lo, hi, ref)
        t = teams[d["agent"]]
        acc = accounts.get(d["account"]) if d["account"] else None
        rows.append({
            "id": d["id"], "agent": d["agent"], "manager": t["manager"], "region": t["regional_office"],
            "product": d["product"], "account": d["account"], "sector": SECTOR_PT.get(acc["sector"]) if acc else None,
            "stage": d["stage"], "engage": d["engage"].isoformat() if d["engage"] else None,
            "price": brl(price), "price_usd": price, **s,
            "reasons": reasons(d, s["state"], s["age"], s["p"], price, model, accounts),
        })
    # zumbis vão para o fim: precisam de verificação, não de prioridade
    rows.sort(key=lambda r: (r["state"] == "zumbi", -r["score"], -r["price_usd"], r["id"]))
    return rows


# ---------------------------------------------------------------- validação

def auc(scores, labels):
    """AUC via Mann-Whitney, empates contam 0.5."""
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    pos = sum(labels)
    neg = len(labels) - pos
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        rank_sum += (i + j + 1) / 2 * sum(l for _, l in pairs[i:j])
        i = j
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


def auc_ci(scores, labels, n_boot=200, seed=7):
    """Intervalo de 95% por bootstrap."""
    rnd = random.Random(seed)
    idx = range(len(scores))
    vals = []
    for _ in range(n_boot):
        s = [rnd.choice(idx) for _ in idx]
        ys = [labels[i] for i in s]
        if 0 < sum(ys) < len(ys):
            vals.append(auc([scores[i] for i in s], ys))
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def snapshot(deals, cutoff):
    """Simula o uso real: no dia `cutoff`, quais deals estavam abertos e como terminaram.

    Treino = fechados antes do corte. Teste = Engaging no corte (engajado antes, fechado depois),
    com a idade que tinham NAQUELE dia. Sem vazamento: nada do futuro entra no treino.
    """
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    train = [d for d in closed if d["close"] < cutoff]
    test = [d for d in closed if d["engage"] < cutoff <= d["close"]]
    return fit(train), test


def backtest(deals, cutoffs=CUTOFFS):
    """Avalia cada componente como ordenador, em vários cortes, com IC 95%.

    Gate: um atributo só pontua se AUC >= GATE em todos os cortes.
    """
    rows, wins = [], {}
    for c in cutoffs:
        m, test = snapshot(deals, c)
        y = [d["stage"] == "Won" for d in test]
        base = m["base"]
        cands = {
            "idade do deal (curva de sobrevivência)": lambda d: time_prob(m, (c - d["engage"]).days) or base,
            "vendedor x produto": lambda d: history(m, d)["vendedor_produto"]["smooth"],
            "conta": lambda d: smoothed(m["cnt"]["account"].get(d["account"], [0, 0]), base),
            "vendedor": lambda d: smoothed(m["cnt"]["agent"].get(d["agent"], [0, 0]), base),
            "produto": lambda d: smoothed(m["cnt"]["product"].get(d["product"], [0, 0]), base),
        }
        res = {}
        for k, f in cands.items():
            s = [f(d) for d in test]
            res[k] = (auc(s, y), *auc_ci(s, y))
        rows.append({"cutoff": c.isoformat(), "n_train": m["n"], "n_test": len(test),
                     "win_test": sum(y) / len(y), "auc": res})
    key_map = {"vendedor x produto": "vendedor_produto", "conta": "conta"}
    selected = [v for k, v in key_map.items() if all(r["auc"][k][0] >= GATE for r in rows)]
    # estabilidade do sinal de perda precoce: treino vs teste no corte do meio
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    mid = cutoffs[len(cutoffs) // 2]
    tr = [d for d in closed if d["close"] < mid]
    te = [d for d in closed if d["close"] >= mid]

    def surv(xs, t):
        s = [d for d in xs if cycle(d) >= t]
        return sum(d["stage"] == "Won" for d in s) / len(s), len(s)

    stab = [(t, surv(tr, t), surv(te, t)) for t in (0, 7, 14, 30, 60, 90, 120)]
    return {"snapshots": rows, "selected": selected, "stability": stab, "mid": mid.isoformat()}


def write_validation(bt, model, rows, path):
    zomb = [r for r in rows if r["state"] == "zumbi"]
    eng = [r for r in rows if r["stage"] == "Engaging"]
    pros = [r for r in rows if r["stage"] == "Prospecting"]
    L = ["# Validação do modelo", "", "> Gerado por `solution/scorer.py`. Não editar à mão.", "",
         "## 1. Backtest por snapshot: alguém consegue ordenar quem vai ganhar?", "",
         "Simula o uso real. Em cada data de corte, o modelo vê só o passado e ordena os deals que estavam "
         "em Engaging naquele dia, com a idade que tinham. Depois compara com o resultado real.", "",
         f"AUC 0,50 = cara ou coroa. Gate para um atributo entrar no score: AUC >= {GATE} em todos os cortes.", ""]
    names = list(bt["snapshots"][0]["auc"])
    L += ["| Fator | " + " | ".join(s["cutoff"] for s in bt["snapshots"]) + " |",
          "|---|" + "---|" * len(bt["snapshots"])]
    for k in names:
        L.append(f"| {k} | " + " | ".join(
            f"{s['auc'][k][0]:.3f} [{s['auc'][k][1]:.2f}-{s['auc'][k][2]:.2f}]" for s in bt["snapshots"]) + " |")
    L += ["| deals no teste (taxa de ganho) | " + " | ".join(
        f"{s['n_test']} ({s['win_test']:.0%})" for s in bt["snapshots"]) + " |", "",
          f"Atributos aprovados no gate: {', '.join(bt['selected']) or 'nenhum'}.", "",
          "**Leitura honesta:** nenhum componente ordena ganhos de forma confiável. A idade fica entre 0,51 e 0,55 conforme o corte, "
          "e em dois dos três cortes o intervalo de 95% inclui 0,50. Por isso o score NÃO usa probabilidade: é uma política explícita de "
          "valor x momento (docs/logica.md). Setor, região, porte, preço, carga do vendedor e 'conta já comprou' "
          "também foram testados (`process-log/eda3_sinais.py`): AUC entre 0,49 e 0,51.", "",
          f"## 2. Onde as perdas acontecem (corte {bt['mid']})", "",
          "P(ganho | deal ainda aberto após t dias). Treino e teste mostram o mesmo formato.", "",
          "| t (dias) | Treino | Teste |", "|---|---|---|"]
    L += [f"| {t} | {a[0]:.1%} (n={a[1]}) | {b[0]:.1%} (n={b[1]}) |" for t, a, b in bt["stability"]]
    L += ["", f"{model['early_loss']:.0%} das perdas acontecem até o dia {EARLY_WINDOW}. "
          f"Maior ciclo já observado: {model['max_cycle']} dias (era o mesmo no corte de maio/2017).", "",
          "## 3. Pipeline aberto na data de referência", "",
          f"Valores em reais pela PTAX de venda de {USD_BRL_DATE}: US$ 1 = R$ {str(USD_BRL).replace('.', ',')}.", "",
          f"- Deals abertos: {len(rows)} ({len(eng)} Engaging, {len(pros)} Prospecting)",
          f"- Engaging além de {model['max_cycle']} dias ('zumbis', verificar no CRM): {len(zomb)} = "
          f"{len(zomb) / len(eng):.0%} do Engaging, {fmt_brl(brl(sum(r['price_usd'] for r in zomb)))} em tabela",
          f"- Engaging dentro do ciclo: {len(eng) - len(zomb)} deals, valor esperado "
          f"{fmt_brl(sum(r['ev'] for r in eng if r['ev'] is not None))}",
          f"- Prospecting: {len(pros)} deals, {fmt_brl(brl(sum(r['price_usd'] for r in pros)))} em tabela, "
          "chance desconhecida (o histórico nunca registra Prospecting -> Won)",
          f"- Valor de tabela nominal de tudo: {fmt_brl(brl(sum(r['price_usd'] for r in rows)))}",
          f"- Deals sem conta preenchida: {sum(r['account'] is None for r in rows)}", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------- main

def build(csv_out=None, data_dir=DATA, out_dir=HERE):
    accounts, products, teams, deals = load(data_dir)
    bt = backtest(deals)
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    model = fit(closed, bt["selected"])
    rows = score_open(model, accounts, products, teams, deals)
    agents = [{"agent": a, "manager": t["manager"], "region": t["regional_office"]} for a, t in sorted(teams.items())]
    last = bt["snapshots"][1]["auc"]
    meta = {"ref_date": REF_DATE.isoformat(), "base": round(model["base"], 3), "max_cycle": model["max_cycle"],
            "n_closed": model["n"], "early_window": EARLY_WINDOW, "final_stretch": FINAL_STRETCH,
            "early_loss": round(model["early_loss"], 3), "factors": model["factors"],
            "auc_range": [round(min(min(s["auc"][k][0] for k in s["auc"]) for s in bt["snapshots"]), 2),
                          round(max(max(s["auc"][k][0] for k in s["auc"]) for s in bt["snapshots"]), 2)],
            "auc_mid": {k: round(v[0], 3) for k, v in last.items()},
            "weights": {"valor": PTS_VALOR, "momento": PTS_MOMENTO}, "momento": MOMENTO,
            "fx": {"usd_brl": USD_BRL, "date": USD_BRL_DATE, "source": "PTAX venda, Banco Central do Brasil"}}
    with open(os.path.join(out_dir, "app", "data.js"), "w", encoding="utf-8") as f:
        f.write("window.LEAD_DATA = ")
        json.dump({"meta": meta, "agents": agents, "deals": rows}, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    write_validation(bt, model, rows, os.path.join(out_dir, "..", "docs", "validacao.md"))
    if csv_out:
        num = lambda v: "" if v is None else str(v).replace(".", ",")  # noqa: E731
        with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["opportunity_id", "score", "acao", "p_ganho", "valor_esperado", "vendedor", "manager",
                        "regiao", "produto", "conta", "estagio", "dias_aberto", "motivos"])
            for r in rows:
                w.writerow([r["id"], r["score"], r["action"], num(r["p"]), num(r["ev"]), r["agent"], r["manager"],
                            r["region"], r["product"], r["account"] or "", r["stage"], num(r["age"]),
                            " | ".join(t for k, t in r["reasons"] if k != "h")])
    return model, rows, bt


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None
    model, rows, bt = build(out)
    print(f"{len(rows)} deals abertos priorizados -> app/data.js, docs/validacao.md")
    for s in bt["snapshots"]:
        print(f"  corte {s['cutoff']}: " + ", ".join(f"{k} {v[0]:.3f}" for k, v in s["auc"].items()))
    print("  atributos no score:", bt["selected"] or "nenhum")
    from collections import Counter
    print(" ", dict(Counter(r["action"] for r in rows)))
