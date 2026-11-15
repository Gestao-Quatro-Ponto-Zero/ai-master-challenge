#!/usr/bin/env python3
"""Conferência independente dos números do app.

Uso, dentro de solution/:
    python3 verify.py          tabela legível
    python3 verify.py --json   os mesmos fatos em JSON

O script tem uma segunda implementação, curta e direta, das regras do modelo
(chance, score, ordem, prova). Ela lê os CSVs de data/ e não usa nada do
engine para calcular. Depois chama o engine e compara, linha a linha, o valor
do app com o valor desta conferência. Sai com código 1 se algo não bater.

Só biblioteca padrão. Compatível com Python 3.9.
"""
import bisect
import csv
import json
import os
import re
import sys
import time
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

DEFAULT_DATE = date(2017, 12, 4)
EXTRA_DATES = [date(2017, 7, 3), date(2017, 10, 2)]
SELLER = "Daniell Hammack"
MANAGER = "Rocco Neubert"

BAND_LIMITS = [14, 30, 45, 60, 75, 90, 105, 120, 138]  # acima de 138: última faixa
MIN_CASES = 30
HORIZON = 30  # dias
TOP_N = 10
MONEY_TOL = 0.5
FRAC_TOL = 1e-9


# --------------------------------------------------------------------------
# 1. Leitura dos CSVs (com as três correções de grafia)
# --------------------------------------------------------------------------

def _d(text):
    return date.fromisoformat(text) if text else None


def load():
    with open(os.path.join(DATA, "products.csv"), newline="", encoding="utf-8") as f:
        price = {r["product"]: int(float(r["sales_price"])) for r in csv.DictReader(f)}
    with open(os.path.join(DATA, "sales_teams.csv"), newline="", encoding="utf-8") as f:
        teams = {r["sales_agent"]: (r["manager"], r["regional_office"]) for r in csv.DictReader(f)}
    with open(os.path.join(DATA, "accounts.csv"), newline="", encoding="utf-8") as f:
        accounts = [r["account"] for r in csv.DictReader(f)]
    deals = []
    with open(os.path.join(DATA, "sales_pipeline.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            product = "GTX Pro" if r["product"] == "GTXPro" else r["product"]
            deals.append({
                "id": r["opportunity_id"],
                "seller": r["sales_agent"],
                "product": product,
                "price": price[product],
                "account": r["account"] or None,
                "stage": r["deal_stage"],
                "engage": _d(r["engage_date"]),
                "close": _d(r["close_date"]),
                "close_value": float(r["close_value"]) if r["close_value"] else 0.0,
            })
    return deals, teams, accounts


# --------------------------------------------------------------------------
# 2. Segunda implementação do modelo
# --------------------------------------------------------------------------

def band_of(age):
    for i, limit in enumerate(BAND_LIMITS):
        if age <= limit:
            return i
    return len(BAND_LIMITS)


def week_of_quarter(d):
    start = date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
    return (d - start).days // 7


def month_of_quarter(d):
    return (d.month - 1) % 3


def is_open(deal, d):
    return deal["engage"] is not None and deal["engage"] < d and (deal["close"] is None or deal["close"] >= d)


def won_within(deal, d):
    return deal["stage"] == "Won" and deal["close"] < d + timedelta(days=HORIZON)


class Model:
    """Contagens de treino por segunda-feira e chance por data."""

    def __init__(self, deals):
        self.deals = deals
        self.mondays = []
        m = date(2017, 3, 6)
        while m <= date(2017, 12, 25):
            self.mondays.append(m)
            m += timedelta(days=7)
        # por segunda: contagens {chave: [n, y]}
        self.per_monday = {}
        for m in self.mondays:
            counts = {}
            w, mq = week_of_quarter(m), month_of_quarter(m)
            for deal in deals:
                if not is_open(deal, m):
                    continue
                b = band_of((m - deal["engage"]).days)
                y = 1 if won_within(deal, m) else 0
                for key in (("w", b, w), ("m", b, mq), ("b", b), ("all",)):
                    c = counts.setdefault(key, [0, 0])
                    c[0] += 1
                    c[1] += y
            self.per_monday[m] = counts
        self._cache = {}
        self.closed = sorted((d["close"], (d["close"] - d["engage"]).days) for d in deals if d["close"])

    def counts_for(self, d):
        if d not in self._cache:
            total = {}
            for m in self.mondays:
                if m + timedelta(days=HORIZON) <= d:
                    for key, (n, y) in self.per_monday[m].items():
                        c = total.setdefault(key, [0, 0])
                        c[0] += n
                        c[1] += y
            self._cache[d] = total
        return self._cache[d]

    def chance(self, d, age):
        counts = self.counts_for(d)
        b = band_of(age)
        for level, key in (("semana", ("w", b, week_of_quarter(d))),
                           ("mes", ("m", b, month_of_quarter(d))),
                           ("faixa", ("b", b))):
            n, y = counts.get(key, (0, 0))
            if n >= MIN_CASES:
                return y / n, n, y, level
        n, y = counts.get(("all",), (0, 0))
        return (y / n if n else 0.0), n, y, "geral"

    def max_cycle(self, d):
        return max((c for close, c in self.closed if close < d), default=0)

    def snapshot(self, d):
        """Deals abertos na data, com chance, receita esperada, score e faixa."""
        cap = self.max_cycle(d)
        rows = []
        for deal in self.deals:
            if not is_open(deal, d):
                continue
            age = (d - deal["engage"]).days
            stale = age > cap
            if stale:
                ch, n, y, level = 0.0, None, None, None
            else:
                ch, n, y, level = self.chance(d, age)
            rows.append(dict(deal, age=age, stale=stale, chance=ch, n=n, y=y, level=level,
                             ev=ch * deal["price"], score=None, band="sem_desfecho"))
        live_ev = sorted(r["ev"] for r in rows if not r["stale"])
        total = len(live_ev)
        for r in rows:
            if r["stale"]:
                continue
            k = bisect.bisect_right(live_ev, r["ev"])
            r["score"] = int(round(100 * k / total))
            r["band"] = "quente" if r["score"] >= 80 else ("morno" if r["score"] >= 40 else "frio")
        rows.sort(key=lambda r: (r["stale"], -r["ev"], r["engage"], r["id"]))
        return rows


def summarize(rows):
    live = [r for r in rows if not r["stale"]]
    stale = [r for r in rows if r["stale"]]
    return {
        "open_count": len(rows),
        "live_count": len(live),
        "stale_count": len(stale),
        "declared_value": sum(r["price"] for r in rows),
        "live_value": sum(r["price"] for r in live),
        "stale_value": sum(r["price"] for r in stale),
        "expected_30d": sum(r["ev"] for r in live),
        "hot_count": sum(1 for r in live if r["band"] == "quente"),
    }


def expected_top(items, key, slots=TOP_N):
    """Vendas e receita esperadas do top N por chave; empate pela fração vagas/tamanho."""
    groups = {}
    for it in items:
        groups.setdefault(key(it), []).append(it)
    wins = revenue = 0.0
    for k in sorted(groups, reverse=True):
        group = groups[k]
        frac = 1.0 if len(group) <= slots else slots / len(group)
        wins += frac * sum(1 for it in group if it["won"])
        revenue += frac * sum(it["rev"] for it in group)
        slots -= min(slots, len(group))
        if slots == 0:
            break
    return wins, revenue


RULES = {
    "score": lambda it: it["ev"],
    "value_only": lambda it: it["price"],
    "value_no_stale": lambda it: (not it["stale"], it["price"]),
    "value_no_stale_newest": lambda it: (not it["stale"], it["price"], it["engage"].toordinal()),
    "random": lambda it: 0,
}
COMPARED = ["value_only", "value_no_stale", "value_no_stale_newest"]


def run_proof(model):
    dates = [date(2017, 7, 3) + timedelta(days=7 * i) for i in range(22)]
    totals = {r: [0.0, 0.0] for r in RULES}
    per_date = []
    n_lists = 0
    for d in dates:
        by_seller = {}
        for r in model.snapshot(d):
            won = won_within(r, d)
            by_seller.setdefault(r["seller"], []).append(
                dict(r, won=won, rev=r["close_value"] if won else 0.0))
        row = {"date": d, "lists": 0}
        for rule in RULES:
            row[rule] = [0.0, 0.0]
        for items in by_seller.values():
            if len(items) < TOP_N:
                continue
            row["lists"] += 1
            for rule, key in RULES.items():
                w, v = expected_top(items, key)
                row[rule][0] += w
                row[rule][1] += v
        n_lists += row["lists"]
        for rule in RULES:
            totals[rule][0] += row[rule][0]
            totals[rule][1] += row[rule][1]
        per_date.append(row)

    def gain(rows, rule):
        s = sum(x["score"][1] for x in rows)
        o = sum(x[rule][1] for x in rows)
        return s / o - 1

    periods = {
        "jul-set": [x for x in per_date if x["date"].month <= 9],
        "out-nov": [x for x in per_date if x["date"].month >= 10],
    }
    return {
        "dates": dates,
        "n_lists": n_lists,
        "totals": totals,
        "per_date": per_date,
        "gains": {r: gain(per_date, r) for r in COMPARED},
        "dates_won": {r: [x["date"] for x in per_date if x["score"][1] > x[r][1]] for r in COMPARED},
        "periods": {k: {"n": len(v), "gains": {r: gain(v, r) for r in COMPARED}} for k, v in periods.items()},
    }


# --------------------------------------------------------------------------
# 3. Comparação
# --------------------------------------------------------------------------

MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def br_int(text):
    """'1.185 deals' -> 1185 (primeiro número do texto)."""
    m = re.search(r"\d[\d.]*", text)
    return int(m.group(0).replace(".", "")) if m else None


def br_date(day, mon, year):
    return date(int(year), MONTHS.index(mon) + 1, int(day))


def label_date(d):
    return "{} {}".format(d.day, MONTHS[d.month - 1])


def fmt(v, kind):
    if v is None:
        return "-"
    if kind == "money":
        s = "{:,.2f}".format(v)
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    if kind == "frac":
        return "{:.6f}".format(v).replace(".", ",")
    if kind == "int":
        return "{:,}".format(v).replace(",", ".")
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v)
    return str(v)


def jsonable(v):
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    return v


class Checks:
    def __init__(self):
        self.rows = []
        self.section = ""

    def head(self, title):
        self.section = title

    def add(self, what, app, mine, kind="int"):
        if app is None or mine is None:
            ok = False
        elif kind == "money":
            ok = abs(app - mine) <= MONEY_TOL
        elif kind == "frac":
            ok = abs(app - mine) <= FRAC_TOL
        else:
            ok = app == mine
        self.rows.append({"section": self.section, "what": what, "kind": kind,
                          "app": jsonable(app), "check": jsonable(mine), "ok": bool(ok)})

    def deal(self, what, app, mine):
        """Deal da lista: id, score, chance e receita esperada."""
        ok = (app["id"] == mine["id"] and app["score"] == mine["score"]
              and abs(app["chance"] - mine["chance"]) <= FRAC_TOL
              and abs(app["expected_value"] - mine["ev"]) <= MONEY_TOL)
        a = "{} score {} chance {} US$ {}".format(app["id"], app["score"], fmt(app["chance"], "frac"),
                                                   fmt(app["expected_value"], "money"))
        c = "{} score {} chance {} US$ {}".format(mine["id"], mine["score"], fmt(mine["chance"], "frac"),
                                                   fmt(mine["ev"], "money"))
        self.rows.append({"section": self.section, "what": what, "kind": "text",
                          "app": a, "check": c, "ok": ok})


def company_checks(ck, model, d, team, score_model, ds):
    rows = model.snapshot(d)
    mine = summarize(rows)
    app = team(ds, d)["summary"]
    ck.head("Empresa em {}".format(d.isoformat()))
    ck.add("deals abertos (sem Prospecting)", app["open_count"], mine["open_count"])
    ck.add("vivos", app["live_count"], mine["live_count"])
    ck.add("sem desfecho", app["stale_count"], mine["stale_count"])
    ck.add("valor declarado (US$)", app["declared_value"], mine["declared_value"], "money")
    ck.add("valor vivo (US$)", app["live_value"], mine["live_value"], "money")
    ck.add("valor sem desfecho (US$)", app["stale_value"], mine["stale_value"], "money")
    ck.add("receita esperada em 30 dias (US$)", app["expected_30d"], mine["expected_30d"], "money")
    ck.add("deals quentes", app["hot_count"], mine["hot_count"])
    sm = score_model(ds, d)
    ck.add("maior ciclo conhecido (dias)", sm["max_cycle"], model.max_cycle(d))
    # tabela de chance: idade de referência de cada faixa (o limite superior)
    refs = BAND_LIMITS + [BAND_LIMITS[-1] + 1]
    for row, ref in zip(sm["table"], refs):
        ch, n, y, level = model.chance(d, ref)
        if ref > model.max_cycle(d):
            ch = 0.0
        ck.add("tabela, faixa {}: chance".format(row["label"]), row["chance"], ch, "frac")
        ck.add("tabela, faixa {}: casos".format(row["label"]), row["n"], n)
    return rows


def main():
    as_json = "--json" in sys.argv[1:]
    t0 = time.time()
    sys.path.insert(0, HERE)

    deals, teams, accounts = load()
    model = Model(deals)

    # o engine entra só aqui, para dar o valor do app
    from engine.core import get_dataset, parse_date
    from engine.seller import focus
    from engine.team import team
    from engine.proof import proof, time_machine
    from engine.quality import data_quality
    from engine.model_page import score_model

    ds = get_dataset()
    d = parse_date(ds, DEFAULT_DATE.isoformat())
    ck = Checks()

    # --- Base -------------------------------------------------------------
    dq = data_quality(ds, d)
    cov = dq["coverage"]
    ck.head("Base")
    ck.add("deals", br_int(cov[0]["value"]), len(deals))
    stage_text = cov[0]["detail"]
    for label, stage in (("ganhos", "Won"), ("perdidos", "Lost"),
                         ("em negociação", "Engaging"), ("em prospecção", "Prospecting")):
        m = re.search(r"([\d.]+) " + label, stage_text)
        ck.add("deals {}".format(stage), br_int(m.group(1)) if m else None,
               sum(1 for x in deals if x["stage"] == stage))
    ck.add("clientes", br_int(cov[1]["value"]), len(accounts))
    m = re.search(r"([\d.]+) com deals", cov[2]["detail"])
    ck.add("vendedores com deals", br_int(m.group(1)) if m else None, len({x["seller"] for x in deals}))
    m = re.search(r"de (\d+) (\w+) (\d{4}) a (\d+) (\w+) (\d{4})", cov[3]["detail"])
    app_period = [br_date(*m.group(1, 2, 3)), br_date(*m.group(4, 5, 6))] if m else None
    first = min(x["engage"] for x in deals if x["engage"])
    last = max(x["close"] for x in deals if x["close"])
    ck.add("período (primeira entrada, último fechamento)", app_period, [first, last], "text")

    # --- Empresa ----------------------------------------------------------
    snap = company_checks(ck, model, d, team, score_model, ds)
    for extra in EXTRA_DATES:
        company_checks(ck, model, parse_date(ds, extra.isoformat()), team, score_model, ds)

    # --- Vendedor ---------------------------------------------------------
    f = focus(ds, d, SELLER)
    mine_rows = [r for r in snap if r["seller"] == SELLER]
    mine = summarize(mine_rows)
    ck.head("Vendedor {} em {}".format(SELLER, d.isoformat()))
    for key, label in (("open_count", "abertos"), ("live_count", "vivos"), ("stale_count", "sem desfecho")):
        ck.add(label, f["summary"][key], mine[key])
    for key, label in (("declared_value", "valor declarado (US$)"), ("live_value", "valor vivo (US$)"),
                       ("stale_value", "valor sem desfecho (US$)"),
                       ("expected_30d", "receita esperada em 30 dias (US$)")):
        ck.add(label, f["summary"][key], mine[key], "money")
    for b in f["bands"]:
        group = [r for r in mine_rows if r["band"] == b["key"]]
        ck.add("faixa {}: deals".format(b["key"]), b["count"], len(group))
        ck.add("faixa {}: com cliente".format(b["key"]), b["with_account"],
               sum(1 for r in group if r["account"]))
    closed = [x for x in deals if x["seller"] == SELLER and x["close"] and x["close"] < d]
    won = sum(1 for x in closed if x["stage"] == "Won")
    lost = len(closed) - won
    ck.add("vendas fechadas antes da data", f["rates"]["won"], won)
    ck.add("perdas fechadas antes da data", f["rates"]["lost"], lost)
    ck.add("taxa de ganho oficial", f["rates"]["official"], won / (won + lost), "frac")
    ck.add("taxa de ganho contando os sem desfecho", f["rates"]["with_stale"],
           won / (won + lost + mine["stale_count"]), "frac")
    for i in range(TOP_N):
        ck.deal("deal {} da lista".format(i + 1), f["deals"][i], mine_rows[i])

    # --- Time -------------------------------------------------------------
    t = team(ds, d, manager=MANAGER)["summary"]
    members = {s for s, (mgr, _) in teams.items() if mgr == MANAGER and any(x["seller"] == s for x in deals)}
    mine = summarize([r for r in snap if r["seller"] in members])
    ck.head("Time de {} em {}".format(MANAGER, d.isoformat()))
    ck.add("vendedores", t["seller_count"], len(members))
    for key, label in (("open_count", "abertos"), ("live_count", "vivos"),
                       ("stale_count", "sem desfecho"), ("hot_count", "quentes")):
        ck.add(label, t[key], mine[key])
    for key, label in (("declared_value", "valor declarado (US$)"), ("live_value", "valor vivo (US$)"),
                       ("stale_value", "valor sem desfecho (US$)"),
                       ("expected_30d", "receita esperada em 30 dias (US$)")):
        ck.add(label, t[key], mine[key], "money")
    ck.add("parte viva do valor", t["live_share"], mine["live_value"] / mine["declared_value"], "frac")

    # --- Prova ------------------------------------------------------------
    p = proof(ds)
    mp = run_proof(model)
    ck.head("Prova (22 segundas, top 10 por vendedor)")
    ck.add("segundas", p["n_dates"], len(mp["dates"]))
    ck.add("primeira e última segunda", [p["first_date"]["iso"], p["last_date"]["iso"]],
           [mp["dates"][0].isoformat(), mp["dates"][-1].isoformat()], "text")
    ck.add("listas", p["n_lists"], mp["n_lists"])
    names = {"score": "score", "value_only": "só por valor", "value_no_stale": "valor sem os sem desfecho",
             "value_no_stale_newest": "idem, mais novo primeiro", "random": "sorteio"}
    for rule, label in names.items():
        ck.add("{}: receita (US$)".format(label), p["rules"][rule]["revenue"], mp["totals"][rule][1], "money")
        ck.add("{}: vendas".format(label), p["rules"][rule]["wins"], mp["totals"][rule][0], "frac")
    for rule in COMPARED:
        ck.add("ganho do score contra {}".format(names[rule]), p["gains"]["vs_" + rule],
               mp["gains"][rule], "frac")
        ck.add("segundas em que o score vence ({})".format(names[rule]),
               p["dates_won"]["vs_" + rule]["won"], len(mp["dates_won"][rule]))
    lost_mine = [label_date(x["date"]) for x in mp["per_date"] if x["score"][1] <= x["value_no_stale"][1]]
    ck.add("segundas em que perde (valor sem os sem desfecho)",
           p["dates_won"]["vs_value_no_stale"].get("lost_labels"), lost_mine, "text")
    for per in p["by_period"]:
        mine_p = mp["periods"][per["key"]]
        ck.add("{}: segundas".format(per["label"]), per["n_dates"], mine_p["n"])
        for rule in COMPARED:
            ck.add("{}: ganho contra {}".format(per["label"], names[rule]),
                   per["gain_vs_" + rule], mine_p["gains"][rule], "frac")
    # por data: as 4 regras, vendas e receita
    bad = 0
    total = 0
    by_iso = {x["date"].isoformat(): x for x in mp["per_date"]}
    for row in p["per_date"]:
        mine_row = by_iso.get(row["date"])
        for rule in ["score"] + COMPARED:
            total += 2
            if mine_row is None:
                bad += 2
                continue
            bad += abs(row[rule]["revenue"] - mine_row[rule][1]) > MONEY_TOL
            bad += abs(row[rule]["wins"] - mine_row[rule][0]) > FRAC_TOL
        if mine_row is not None:
            total += 1
            bad += row["lists"] != mine_row["lists"]
    ck.add("por segunda: valores que não batem (de {})".format(total), bad, 0)

    # --- Máquina do tempo -------------------------------------------------
    tm = time_machine(ds, d, SELLER)
    mine_rows = [dict(r, won=won_within(r, d)) for r in snap if r["seller"] == SELLER]
    for r in mine_rows:
        r["rev"] = r["close_value"] if r["won"] else 0.0
    by_value = sorted(mine_rows, key=lambda r: (-r["price"], r["engage"], r["id"]))
    lists = {"score": mine_rows[:TOP_N], "value_only": by_value[:TOP_N]}
    ck.head("Máquina do tempo de {} em {}".format(SELLER, d.isoformat()))
    for key, label in (("score", "lista do score"), ("value_only", "lista só por valor")):
        ck.add("{}: deals".format(label), [x["id"] for x in tm["lists"][key]["rows"]],
               [x["id"] for x in lists[key]], "text")
        ck.add("{}: vendas".format(label), tm["lists"][key]["wins"], sum(1 for x in lists[key] if x["won"]))
        ck.add("{}: receita (US$)".format(label), tm["lists"][key]["revenue"],
               sum(x["rev"] for x in lists[key]), "money")
    w, v = expected_top(mine_rows, RULES["value_no_stale"])
    ck.add("valor sem os sem desfecho, empate dividido: vendas", tm["fair"]["expected"]["wins"], w, "frac")
    ck.add("valor sem os sem desfecho, empate dividido: receita (US$)",
           tm["fair"]["expected"]["revenue"], v, "money")

    # --- Qualidade dos dados ----------------------------------------------
    items = {it["key"]: it for it in dq["items"]}
    fields = {fl["field"]: fl["text"] for fl in dq["fields"]}
    ck.head("Qualidade dos dados")
    ck.add("deals que entraram antes de 2017-03-01", br_int(items["early_engage"]["number"]),
           sum(1 for x in deals if x["engage"] and x["engage"] < date(2017, 3, 1)))
    open_all = [x for x in deals if x["stage"] in ("Engaging", "Prospecting")]
    closed_all = [x for x in deals if x["stage"] in ("Won", "Lost")]
    no_acc = sum(1 for x in open_all if not x["account"])
    ck.add("deals abertos sem cliente", br_int(fields["Cliente"]), no_acc)
    ck.add("parte dos abertos sem cliente (%)", br_int(items["open_account"]["number"]),
           int(round(100 * no_acc / len(open_all))))
    app_closed_empty = 0 if "todos abertos" in fields["Cliente"] else None
    ck.add("deals fechados sem cliente", app_closed_empty, sum(1 for x in closed_all if not x["account"]))
    body = items["account_leak"]["body"]
    live = [r for r in snap if not r["stale"]]
    with_acc = [r for r in live if r["account"]]
    without = [r for r in live if not r["account"]]
    m1 = re.search(r"nenhum dos ([\d.]+) deals vivos sem cliente fechou", body)
    m2 = re.search(r"Dos ([\d.]+) com cliente, ([\d.]+) viraram venda", body)
    ck.add("vivos sem cliente em 2017-12-04", br_int(m1.group(1)) if m1 else None, len(without))
    ck.add("desses, fechados até o fim da base", br_int(items["account_leak"]["number"]),
           sum(1 for r in without if r["close"]))
    ck.add("vivos com cliente em 2017-12-04", br_int(m2.group(1)) if m2 else None, len(with_acc))
    ck.add("desses, vendas até o fim da base", br_int(m2.group(2)) if m2 else None,
           sum(1 for r in with_acc if r["stage"] == "Won"))
    ck.add("maior ciclo da base (dias)", br_int(items["max_cycle"]["number"]),
           max((x["close"] - x["engage"]).days for x in closed_all))
    m = re.search(r"([\d.]+) dos ([\d.]+) deals abertos", items["max_cycle"]["body"])
    ck.add("abertos em 2017-12-04", br_int(m.group(2)) if m else None, len(snap))
    ck.add("desses, sem desfecho", br_int(m.group(1)) if m else None, sum(1 for r in snap if r["stale"]))
    body = items["quarter_rhythm"]["body"]
    m = re.search(r"havia ([\d.]+), ([\d.]+) e ([\d.]+) deals", body)
    olds = []
    for i, day in enumerate((date(2017, 4, 1), date(2017, 7, 1), date(2017, 10, 1))):
        old = [x for x in deals if is_open(x, day) and (day - x["engage"]).days > 30]
        ck.add("abertos com mais de 30 dias em {}".format(day.isoformat()),
               br_int(m.group(i + 1)) if m else None, len(old))
        olds.append((day, old))
    m = re.search(r"\(([\d.]+) somando", body)
    ck.add("soma dos três dias", br_int(m.group(1)) if m else None, sum(len(o) for _, o in olds))
    ck.add("desses, fechados no mesmo mês", br_int(items["quarter_rhythm"]["number"]),
           sum(1 for day, old in olds for x in old
               if x["close"] and x["close"] < date(day.year, day.month + 1, 1)))
    pcts = re.findall(r"(\d+)%", body)
    last_m = [x for x in closed_all if x["close"].month % 3 == 0]
    other = [x for x in closed_all if x["close"].month % 3 != 0]
    ck.add("vendas entre os fechamentos do último mês do trimestre (%)", int(pcts[0]) if pcts else None,
           int(round(100 * sum(x["stage"] == "Won" for x in last_m) / len(last_m))))
    ck.add("vendas entre os fechamentos dos outros meses (%)", int(pcts[1]) if len(pcts) > 1 else None,
           int(round(100 * sum(x["stage"] == "Won" for x in other) / len(other))))

    elapsed = time.time() - t0
    n_ok = sum(1 for r in ck.rows if r["ok"])
    result = {"checks": ck.rows, "total": len(ck.rows), "ok": n_ok, "seconds": round(elapsed, 1)}

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print_table(ck.rows)
        print()
        print("{} conferências, {} bateram{}. Tempo: {:.1f} s.".format(
            len(ck.rows), n_ok, "" if n_ok == len(ck.rows) else ", {} NÃO bateram".format(len(ck.rows) - n_ok),
            elapsed))
    return 0 if n_ok == len(ck.rows) else 1


def print_table(rows):
    w_what = max(len(r["what"]) for r in rows)
    cells = [(fmt(r["app"], r["kind"]), fmt(r["check"], r["kind"])) for r in rows]
    w_val = min(26, max(max(len(a), len(c)) for a, c in cells))
    line = "{:<%d}  {:>%d}  {:>%d}  {}" % (w_what, w_val, w_val)
    section = None
    for r, (a, c) in zip(rows, cells):
        if r["section"] != section:
            section = r["section"]
            print()
            print("== {} ==".format(section))
            print(line.format("o que", "app", "conferência", "bate?"))
        if max(len(a), len(c)) > w_val:
            print(line.format(r["what"], "", "", "sim" if r["ok"] else "NÃO"))
            print("    app:         {}".format(a))
            print("    conferência: {}".format(c))
        else:
            print(line.format(r["what"], a, c, "sim" if r["ok"] else "NÃO"))


if __name__ == "__main__":
    sys.exit(main())
