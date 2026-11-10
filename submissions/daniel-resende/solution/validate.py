"""Compare scoring candidates for OPEN deals without leakage.

The split is by time and by what was known. For a cut date C the script builds
"the world as known at C" (every later event is removed before any scoring code
runs), scores the deals that were open at C, and only then looks up what
happened to them in the HORIZON days after C.

Run from anywhere:  python submissions/daniel-resende/solution/validate.py
Standard library only. The system clock is never read.
"""
import contextlib
import csv
import datetime as dt
import io
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

HORIZON = 90  # days after the cut in which the outcome is observed
# Two cuts at the start of a quarter and one in the middle of a quarter; the window of
# the last one ends on the last day of data.
CUTS = [dt.date(2017, 7, 1), dt.date(2017, 8, 16), dt.date(2017, 10, 2)]
SNAPSHOT_STEP = 30  # days between the past snapshots a cut learns from
AGE_BANDS = [(0, 30), (31, 60), (61, 90), (91, 120), (121, 10**6)]
TOP_KS = (5, 10)
MIN_AT_RISK = 30  # an age is read only if at least this many deals were seen reaching it
SHRINK = 50  # pseudo-observations pulling a small segment towards the base rate

# Group thresholds on the learned chance (see section 6 for what they deliver).
ALIVE_MIN = 0.25  # chance >= 25%: the deal is alive
FOCUS_EV_MIN = 1000.0  # "focar agora": alive and chance x list price >= 1,000
# Extra cuts, reported only in the robustness table (section 7b): every half month
# in which both a learning window and a 90-day outcome window fit inside the data.
EXTRA_CUTS = [dt.date(2017, 6, 1), dt.date(2017, 6, 16), dt.date(2017, 7, 16),
              dt.date(2017, 8, 1), dt.date(2017, 9, 1), dt.date(2017, 9, 16)]
COOL_DAYS = 30  # "esfriando": alive today, below ALIVE_MIN if still open in 30 days
DEADLINE_MAX_LATE = 0.01  # the quarter deadline is applied only if <= 1% of past closings broke it

# Everything a scoring function may see about a deal. Nothing else is passed in.
KNOWN_FIELDS = {"id", "seller", "manager", "region", "product", "series", "price", "age", "engage"}
# Fields that carry (or may carry) the outcome. `account` is here because it is
# blank on most open rows and never blank on a closed one: the file cannot show
# that it was known while the deal was open.
LEAK_FIELDS = {"close_date", "close_value", "deal_stage", "days_to_close", "outcome",
               "account", "sector", "revenue", "employees", "office_location", "subsidiary_of"}
assert not (KNOWN_FIELDS & LEAK_FIELDS)

PRODUCT_FIX = {"GTXPro": "GTX Pro"}  # spelling in sales_pipeline.csv vs products.csv


def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse(day):
    return dt.date.fromisoformat(day) if day else None


def load():
    products = {r["product"]: r for r in read("products.csv")}
    teams = {r["sales_agent"]: r for r in read("sales_teams.csv")}
    deals = []
    for r in read("sales_pipeline.csv"):
        product = PRODUCT_FIX.get(r["product"], r["product"])
        deals.append({
            "id": r["opportunity_id"],
            "seller": r["sales_agent"],
            "manager": teams[r["sales_agent"]]["manager"],
            "region": teams[r["sales_agent"]]["regional_office"],
            "product": product,
            "series": products[product]["series"],
            "price": float(products[product]["sales_price"]),
            "engage": parse(r["engage_date"]),
            "stage": r["deal_stage"],
            "close": parse(r["close_date"]),
            "close_value": r["close_value"],
            "account": r["account"],
        })
    return deals


def world_at(deals, cut):
    """The pipeline as it could be known on `cut`: later events are removed."""
    world = []
    for d in deals:
        if d["engage"] is None or d["engage"] > cut:
            continue  # not yet engaged (or no date at all): cannot be placed in time
        closed = d["close"] is not None and d["close"] <= cut
        world.append({
            "id": d["id"], "seller": d["seller"], "manager": d["manager"],
            "region": d["region"], "product": d["product"], "series": d["series"],
            "price": d["price"], "engage": d["engage"],
            "close": d["close"] if closed else None,
            "won": (d["stage"] == "Won") if closed else None,
        })
    for w in world:  # the proof that no future leaks into training or scoring
        assert w["engage"] <= cut and (w["close"] is None or w["close"] <= cut)
    return world


def open_at(world, day):
    """Deals open on `day`, each reduced to the fields a score may use."""
    rows = []
    for w in world:
        if w["engage"] <= day and (w["close"] is None or w["close"] > day):
            known = {"id": w["id"], "seller": w["seller"], "manager": w["manager"],
                     "region": w["region"], "product": w["product"], "series": w["series"],
                     "price": w["price"], "age": (day - w["engage"]).days, "engage": w["engage"]}
            assert set(known) == KNOWN_FIELDS
            rows.append(known)
    return rows


def deadline(engage):
    """Last day of the quarter that follows the quarter of engagement."""
    q = (engage.month - 1) // 3 + 1  # 0-based index of the following quarter
    year, q = (engage.year + 1, 0) if q > 3 else (engage.year, q)
    first_next = dt.date(year + (q == 3), 3 * q + 4 if q < 3 else 1, 1)
    return first_next - dt.timedelta(days=1)


def band_of(age):
    for i, (lo, hi) in enumerate(AGE_BANDS):
        if lo <= age <= hi:
            return i
    raise ValueError(age)


def band_label(i):
    lo, hi = AGE_BANDS[i]
    return f"{lo}-{hi} dias" if hi < 10**6 else f"mais de {lo - 1} dias"


def training_rows(world, cut):
    """Past snapshots whose HORIZON-day window had fully elapsed by the cut."""
    by_id = {w["id"]: w for w in world}
    first_close = min(w["close"] for w in world if w["close"])
    rows, snaps = [], []
    day = cut - dt.timedelta(days=HORIZON)
    while day > first_close:
        snaps.append(day)
        limit = day + dt.timedelta(days=HORIZON)
        assert limit <= cut
        closed_before = [w for w in world if w["close"] and w["close"] <= day]
        for known in open_at(world, day):
            w = by_id[known["id"]]
            if w["engage"] < first_close:
                continue  # start-up cohort, see fit_rules
            won = 1 if (w["close"] and w["close"] <= limit and w["won"]) else 0
            rows.append((known, won, seller_rates(closed_before)))
        day -= dt.timedelta(days=SNAPSHOT_STEP)
    return rows, snaps


def seller_rates(closed):
    """Each seller's win rate on deals already closed, pulled towards the average."""
    total = Counter(w["seller"] for w in closed)
    wins = Counter(w["seller"] for w in closed if w["won"])
    base = sum(wins.values()) / max(1, sum(total.values()))
    return defaultdict(lambda: base, {s: (wins[s] + SHRINK * base) / (total[s] + SHRINK)
                                      for s in total})


# --- Candidate A: transparent rules -----------------------------------------
def fit_rules(world, cut):
    """Life table by days since engage, from everything known at the cut.

    For each age t: of the deals that reached day t still open, how many were won
    and how many were lost on that day. A deal that never closes stays "at risk"
    until the cut, so old ages fill up with deals that go nowhere and the chance
    falls by itself. Deals engaged before the first closing ever recorded are left
    out: the file has no closing before that day, so their ages say nothing about
    how long a deal takes (the start-up cohort).
    """
    first_close = min(w["close"] for w in world if w["close"])
    at_risk, won, lost = Counter(), Counter(), Counter()
    cohort = [w for w in world if w["engage"] >= first_close]
    for w in cohort:
        end = w["close"] or cut
        days = (end - w["engage"]).days
        for t in range(1, days + 1):
            at_risk[t] += 1
        if w["close"]:
            (won if w["won"] else lost)[days] += 1
    closed = [w for w in world if w["close"]]
    late = sum(1 for w in closed if w["close"] > deadline(w["engage"]))
    return {"at_risk": at_risk, "won": won, "lost": lost, "n": len(cohort),
            "max_seen": max(at_risk) if at_risk else 0, "first_close": first_close,
            "closed": len(closed), "late": late, "cut": cut,
            "use_deadline": late <= DEADLINE_MAX_LATE * len(closed),
            "longest_win": max(((w["close"] - w["engage"]).days for w in closed if w["won"]),
                               default=None)}


def is_dead(model, known, ahead=0):
    """Positive evidence that a deal no longer closes: it is older than the slowest
    win ever seen, or its quarter deadline has run out. Lack of evidence is not this."""
    if model["longest_win"] is not None and known["age"] + ahead > model["longest_win"]:
        return True
    return (model["use_deadline"] and "engage" in known
            and (deadline(known["engage"]) - model["cut"]).days - ahead <= 0)


def chance_rules(model, known, _rates=None, horizon=HORIZON, ahead=0):
    """Chance that a deal open at this age is won in the next `horizon` days.

    `ahead` asks the same question as if the deal were still open that many days
    from now (used to tell which live deals are about to go cold).
    """
    if is_dead(model, known, ahead):
        return 0.0
    alive, chance = 1.0, 0.0
    age = known["age"] + ahead
    if age and model["at_risk"][age + 1] < MIN_AT_RISK:
        # nobody was seen reaching this age yet: no evidence either way, so the
        # deal is treated as an average one (the chance of a deal on day 0)
        return chance_rules(model, {"age": 0}, horizon=horizon)
    if model["use_deadline"] and "engage" in known:
        # no win is counted after the deal's quarter deadline: the past shows none
        horizon = min(horizon, (deadline(known["engage"]) - model["cut"]).days - ahead)
    for t in range(age + 1, age + horizon + 1):
        n = model["at_risk"][t]
        if n < MIN_AT_RISK:
            break  # the table ends here; what is counted so far is a lower bound
        chance += alive * model["won"][t] / n
        alive *= 1 - (model["won"][t] + model["lost"][t]) / n
    return chance


# --- Candidate B: additive points (age band + product + seller) --------------
def logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def fit_points(rows):
    base = sum(y for _, y, _ in rows) / len(rows)
    n, won = Counter(), Counter()
    for known, y, _ in rows:
        for key in (("band", band_of(known["age"])), ("product", known["product"]),
                    ("seller", known["seller"])):
            n[key] += 1
            won[key] += y
    delta = {k: logit((won[k] + SHRINK * base) / (n[k] + SHRINK)) - logit(base) for k in n}
    return {"base": base, "delta": delta}


def chance_points(model, known, _rates):
    z = logit(model["base"])
    for key in (("band", band_of(known["age"])), ("product", known["product"]),
                ("seller", known["seller"])):
        z += model["delta"].get(key, 0.0)
    return 1 / (1 + math.exp(-z))


# --- Candidate C: logistic regression (hand-written, ridge, Newton steps) -----
def features(known, rates, products, regions):
    x = [(0, 1.0)]
    b = band_of(known["age"])
    if b:
        x.append((b, 1.0))
    off = len(AGE_BANDS)
    x.append((off, known["age"] / 100.0))
    x.append((off + 1, math.log(known["price"]) / 10.0))
    x.append((off + 2, rates[known["seller"]]))
    off += 3
    p = products.index(known["product"])
    if p:
        x.append((off + p - 1, 1.0))
    off += len(products) - 1
    r = regions.index(known["region"])
    if r:
        x.append((off + r - 1, 1.0))
    return x, off + len(regions) - 1


def solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[piv] = m[piv], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for c in range(n - 1, -1, -1):
        x[c] = (m[c][n] - sum(m[c][k] * x[k] for k in range(c + 1, n))) / m[c][c]
    return x


def fit_logistic(rows, ridge=1.0, steps=12):
    products = sorted({k["product"] for k, _, _ in rows})
    regions = sorted({k["region"] for k, _, _ in rows})
    xs, ys, size = [], [], 0
    for known, y, rates in rows:
        x, size = features(known, rates, products, regions)
        xs.append(x)
        ys.append(y)
    w = [0.0] * size
    for _ in range(steps):
        grad = [-ridge * wi for wi in w]
        grad[0] = 0.0
        hess = [[0.0] * size for _ in range(size)]
        for i in range(1, size):
            hess[i][i] = ridge
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-sum(w[i] * v for i, v in x)))
            for i, v in x:
                grad[i] += (y - p) * v
                for j, u in x:
                    hess[i][j] += p * (1 - p) * v * u
        w = [wi + di for wi, di in zip(w, solve(hess, grad))]
    return {"w": w, "products": products, "regions": regions}


def chance_logistic(model, known, rates):
    if known["product"] not in model["products"]:
        return 0.0
    x, _ = features(known, rates, model["products"], model["regions"])
    return 1 / (1 + math.exp(-sum(model["w"][i] * v for i, v in x)))


# --- Measurement ------------------------------------------------------------
def outcome(deal, cut):
    """What happened to a scored deal in the HORIZON days after the cut."""
    limit = cut + dt.timedelta(days=HORIZON)
    if deal["close"] is not None and deal["close"] <= limit:
        return "ganho" if deal["stage"] == "Won" else "perdido"
    return "sem desfecho"


def top_k(items, k):
    """Expected wins and won value in the top k; ties share the slots evenly."""
    items = sorted(items, key=lambda it: -it[0])
    slots, wins, value, i = k, 0.0, 0.0, 0
    while slots > 0 and i < len(items):
        j = i
        while j < len(items) and items[j][0] == items[i][0]:
            j += 1
        take = min(slots, j - i)
        frac = take / (j - i)
        wins += frac * sum(it[1] for it in items[i:j])
        value += frac * sum(it[2] for it in items[i:j])
        slots -= take
        i = j
    return wins, value, k - slots


CURVE_AGES = (0, 15, 30, 45, 60, 75, 90, 100, 110, 120, 130, 140)


def print_curve(rules):
    print(f"regra A: de cada 100 negocios que chegaram abertos a esta idade, quantos foram ganhos nos"
          f" {HORIZON} dias seguintes\n  (tabela de vida com {rules['n']} negocios engajados desde"
          f" {rules['first_close']}, o 1o fechamento registrado; idade maxima ja vista: {rules['max_seen']} dias)")
    print(f"  prazo: dos {rules['closed']} fechamentos conhecidos nesta data, {rules['late']} ocorreram depois do"
          f" fim do trimestre seguinte ao do engajamento -> prazo aplicado: {'sim' if rules['use_deadline'] else 'nao'}")
    print("  curva so pela idade (antes de aplicar o prazo):")
    for a in CURVE_AGES:
        print(f"  {a:>4} dias: {chance_rules(rules, {'age': a}):6.1%}   (chegaram abertos a essa idade:"
              f" {rules['at_risk'][a + 1]})")


def group_of(model, known, chance):
    price = known["price"]
    if is_dead(model, known):
        return "deixar ir"
    if chance >= ALIVE_MIN and chance * price >= FOCUS_EV_MIN:
        return "focar agora"
    return "manter aquecido"


def money(v):
    return f"{v:,.0f}".replace(",", ".")


def run_cut(deals, cut, last_day):
    by_id = {d["id"]: d for d in deals}
    world = world_at(deals, cut)
    rows, snaps = training_rows(world, cut)
    rates_now = seller_rates([w for w in world if w["close"]])
    scored = open_at(world, cut)
    limit = cut + dt.timedelta(days=HORIZON)
    print(f"\n==== CORTE {cut} (desfecho observado ate {limit}, {HORIZON} dias) ====")
    print(f"aprende de {len(snaps)} fotos passadas ({', '.join(str(s) for s in sorted(snaps))}),"
          f" {len(rows)} linhas, todas com janela encerrada ate o corte (candidatos B e C)")
    print(f"negocios abertos (Engaging) no corte: {len(scored)}")

    result = {k["id"]: outcome(by_id[k["id"]], cut) for k in scored}
    won_value = {k["id"]: float(by_id[k["id"]]["close_value"]) if result[k["id"]] == "ganho" else 0.0
                 for k in scored}
    count = Counter(result.values())
    still_open_end = sum(1 for k in scored if by_id[k["id"]]["close"] is None)
    closed_later = count["sem desfecho"] - still_open_end
    print(f"desfecho na janela: ganho={count['ganho']} perdido={count['perdido']}"
          f" sem desfecho={count['sem desfecho']} (destes, {still_open_end} seguem abertos no"
          f" fim dos dados em {last_day} e {closed_later} fecharam depois da janela)")
    base = count["ganho"] / len(scored)
    print(f"taxa geral de ganho na janela (todos os abertos): {base:.1%};"
          f" so entre os que tiveram desfecho: {count['ganho'] / (count['ganho'] + count['perdido']):.1%}")

    rules = fit_rules(world, cut)
    print_curve(rules)
    models = {
        "A regras (tempo x valor)": (rules, chance_rules),
        "B pontos (tempo+produto+vendedor)": (fit_points(rows), chance_points),
        "C regressao logistica": (fit_logistic(rows), chance_logistic),
    }
    chances = {name: {k["id"]: fn(model, k, rates_now) for k in scored}
               for name, (model, fn) in models.items()}

    orderings = {"ref: ordenar por valor": {k["id"]: k["price"] for k in scored},
                 "ref: taxa geral (ordem qualquer)": {k["id"]: 0.0 for k in scored}}
    for name in models:
        orderings[name] = {k["id"]: round(chances[name][k["id"]] * k["price"], 6) for k in scored}
    orderings["A' regras, so a chance"] = {k["id"]: chances["A regras (tempo x valor)"][k["id"]]
                                          for k in scored}

    lists = defaultdict(list)
    for k in scored:
        lists[k["seller"]].append(k)
    sizes = sorted(len(v) for v in lists.values())
    print(f"listas: {len(lists)} vendedores, tamanho min={sizes[0]} mediana={sizes[len(sizes) // 2]}"
          f" max={sizes[-1]}")
    summary = {}
    for k in TOP_KS:
        print(f"-- top {k} da lista de cada vendedor (empates dividem as vagas) --")
        print(f"  {'ordenacao':<36}{'ganhos':>8}{'de':>6}{'acerto':>8}{'valor ganho':>14}{'vend. melhor que valor':>24}")
        per_seller = {}
        for name, score in orderings.items():
            wins = value = slots = 0.0
            per_seller[name] = {}
            for seller, items in lists.items():
                w, v, used = top_k([(score[i["id"]], result[i["id"]] == "ganho", won_value[i["id"]])
                                    for i in items], k)
                per_seller[name][seller] = (w, v)
                wins, value, slots = wins + w, value + v, slots + used
            ref = per_seller["ref: ordenar por valor"]
            better = sum(1 for s in lists if per_seller[name][s][1] > ref[s][1] + 1e-9)
            summary[(name, k)] = (wins, slots, value)
            print(f"  {name:<36}{wins:8.1f}{slots:6.0f}{wins / slots:8.1%}{money(value):>14}"
                  f"{(str(better) + '/' + str(len(lists))) if not name.startswith('ref: ordenar') else '-':>24}")

    print("-- previsto x observado (chance de ganhar em 90 dias), por faixa --")
    edges = [0.0, 0.05, 0.25, 0.40, 0.55, 1.01]
    for name in models:
        print(f"  {name}")
        for lo, hi in zip(edges, edges[1:]):
            ids = [i for i, c in chances[name].items() if lo <= c < hi]
            if ids:
                pred = sum(chances[name][i] for i in ids) / len(ids)
                obs = sum(1 for i in ids if result[i] == "ganho") / len(ids)
                print(f"    faixa {lo:4.0%}-{min(hi, 1):4.0%}: n={len(ids):5d} previsto={pred:6.1%} observado={obs:6.1%}")

    print(f"-- os tres grupos pela regra A (deixar ir: passou do prazo ou e mais velho que o ganho mais"
          f" demorado ja visto, {rules['longest_win']} dias;\n   focar agora: chance >= {ALIVE_MIN:.0%} e"
          f" chance x valor >= {FOCUS_EV_MIN:.0f}; manter aquecido: o resto) --")
    print(f"  {'grupo':<18}{'n':>6}{'ganhos':>8}{'perdidos':>10}{'sem desf.':>11}{'% ganho':>9}"
          f"{'valor ganho':>14}{'valor de tabela':>17}")
    groups = defaultdict(list)
    for k in scored:
        groups[group_of(rules, k, chances["A regras (tempo x valor)"][k["id"]])].append(k)
    warm = Counter("vivo de valor baixo" if chances["A regras (tempo x valor)"][k["id"]] >= ALIVE_MIN
                   else "chance abaixo de 25%" for k in groups["manter aquecido"])
    warm_won = Counter("vivo de valor baixo" if chances["A regras (tempo x valor)"][k["id"]] >= ALIVE_MIN
                       else "chance abaixo de 25%" for k in groups["manter aquecido"]
                       if result[k["id"]] == "ganho")
    group_stats = {}
    for g in ("focar agora", "manter aquecido", "deixar ir"):
        ids = [k["id"] for k in groups[g]]
        c = Counter(result[i] for i in ids)
        n = max(1, len(ids))
        group_stats[g] = {"n": len(ids), "won": c["ganho"], "lost": c["perdido"],
                          "no_outcome": c["sem desfecho"],
                          "won_value": sum(won_value[i] for i in ids)}
        print(f"  {g:<18}{len(ids):6d}{c['ganho']:8d}{c['perdido']:10d}{c['sem desfecho']:11d}"
              f"{c['ganho'] / n:9.1%}{money(sum(won_value[i] for i in ids)):>14}"
              f"{money(sum(k['price'] for k in groups[g])):>17}")
    for part in sorted(warm):
        print(f"    manter aquecido / {part}: n={warm[part]} ganhos={warm_won[part]}")
    print(f"-- esfriando: vivo hoje (chance >= {ALIVE_MIN:.0%}), mas abaixo disso se seguir aberto por"
          f" mais {COOL_DAYS} dias --")
    soon = cut + dt.timedelta(days=COOL_DAYS)
    for label, want in (("esfriando", True), ("vivo, sem pressa", False)):
        ks = [k for k in scored if chances["A regras (tempo x valor)"][k["id"]] >= ALIVE_MIN
              and (chance_rules(rules, k, ahead=COOL_DAYS) < ALIVE_MIN) == want]
        wins = [k for k in ks if result[k["id"]] == "ganho"]
        early = sum(1 for k in wins if by_id[k["id"]]["close"] <= soon)
        print(f"  {label:<18} n={len(ks):5d} ganhos em {HORIZON} dias={len(wins):4d}"
              f" dos quais nos primeiros {COOL_DAYS} dias={early:4d}"
              f" ({early / max(1, len(wins)):.0%})")
    dropped = [by_id[k["id"]] for k in groups["deixar ir"]]
    later = Counter(d["stage"] for d in dropped)
    print(f"  'deixar ir' ate o fim dos dados ({last_day}): ganhos={later['Won']} perdidos={later['Lost']}"
          f" ainda abertos={later['Engaging']} de {len(dropped)}")
    return summary, rules, group_stats


def group_evidence(results):
    """The three groups summed over the cuts: what the screen may promise."""
    total = {}
    for _, _, stats in results:
        for g, st in stats.items():
            acc = total.setdefault(g, dict.fromkeys(st, 0))
            for key, value in st.items():
                acc[key] += value
    return total


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    deals = load()
    dates = [d[k] for d in deals for k in ("engage", "close") if d[k]]
    last_day = max(dates)
    print("== 1. O que um negocio aberto carrega ==")
    open_deals = [d for d in deals if d["stage"] in ("Prospecting", "Engaging")]
    print(f"negocios abertos: {len(open_deals)} (Engaging={sum(d['stage'] == 'Engaging' for d in open_deals)},"
          f" Prospecting={sum(d['stage'] == 'Prospecting' for d in open_deals)})")
    print(f"abertos com close_value preenchido: {sum(1 for d in open_deals if d['close_value'] != '')}"
          f" | com close_date: {sum(1 for d in open_deals if d['close'])}"
          f" | sem engage_date: {sum(1 for d in open_deals if d['engage'] is None)}"
          f" | sem account: {sum(1 for d in open_deals if not d['account'])}")
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    print(f"fechados sem account: {sum(1 for d in closed if not d['account'])} de {len(closed)}")
    ratios = sorted(float(d["close_value"]) / d["price"] for d in deals if d["stage"] == "Won")
    q = lambda p: ratios[int(p * (len(ratios) - 1))]
    print(f"Won: close_value / preco de tabela -> p05={q(.05):.2f} mediana={q(.5):.2f} p95={q(.95):.2f}"
          f" (n={len(ratios)})")
    print("=> 'valor' de um negocio aberto = preco de tabela do produto (unico valor que a linha aberta tem)")
    print(f"data de referencia (ultima data nos dados): {last_day}")
    print(f"produto renomeado para casar com products.csv: {PRODUCT_FIX}")

    print("\n== 2. Campos que vazariam o desfecho e a prova ==")
    print(f"vazam (nunca entram no score): {sorted(LEAK_FIELDS)}")
    print(f"o score recebe apenas: {sorted(KNOWN_FIELDS)}")
    print("prova: world_at() apaga todo evento posterior ao corte antes de qualquer score e afirma"
          " (assert) que nao sobra data futura; open_at() afirma que so os campos acima saem.")

    print("\n== 3 a 6. Comparacao em tres cortes ==")
    summaries = [run_cut(deals, cut, last_day) for cut in CUTS]

    print("\n== 7. Resumo dos cortes (top 5 por vendedor) ==")
    print(f"  {'ordenacao':<36}" + "".join(f"{'ganhos ' + str(c):>20}{'valor ganho':>14}" for c in CUTS))
    for name in [n for (n, k) in summaries[0][0] if k == 5]:
        line = f"  {name:<36}"
        for summary, _, _ in summaries:
            wins, slots, value = summary[(name, 5)]
            line += f"{f'{wins:.1f} de {slots:.0f}':>20}{money(value):>14}"
        print(line)

    print(f"-- os tres grupos, somando os {len(CUTS)} cortes --")
    evidence = group_evidence(summaries)
    all_won_value = sum(st["won_value"] for st in evidence.values())
    for g, st in evidence.items():
        print(f"  {g:<18} n={st['n']:5d} ganhos={st['won']:5d} ({st['won'] / st['n']:.1%})"
              f" perdidos={st['lost']:5d} sem desfecho={st['no_outcome']:5d}"
              f" valor ganho={money(st['won_value'])} ({st['won_value'] / all_won_value:.1%} do total)")

    print("\n== 7b. Robustez: os mesmos numeros em mais seis cortes (top 5 por vendedor, valor ganho) ==")
    names = ["ref: ordenar por valor", "A regras (tempo x valor)", "B pontos (tempo+produto+vendedor)",
             "C regressao logistica"]
    print(f"  {'corte':<12}" + "".join(f"{n[:22]:>24}" for n in names) + f"{'deixar ir: ganhos/n':>22}")
    wins_over_value = Counter()
    every = []
    for cut in sorted(CUTS + EXTRA_CUTS):
        if cut in CUTS:
            summary, _, stats = summaries[CUTS.index(cut)]
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                summary, _, stats = run_cut(deals, cut, last_day)
        every.append(stats)
        values = [summary[(n, 5)][2] for n in names]
        for n, value in zip(names[1:], values[1:]):
            wins_over_value[n] += value > values[0]
        print(f"  {str(cut):<12}" + "".join(f"{money(x):>24}" for x in values)
              + f"{str(stats['deixar ir']['won']) + '/' + str(stats['deixar ir']['n']):>22}")
    for n in names[1:]:
        print(f"  {n}: ganha de 'ordenar por valor' em {wins_over_value[n]} de {len(every)} cortes")
    dropped_n = sum(st["deixar ir"]["n"] for st in every)
    dropped_won = sum(st["deixar ir"]["won"] for st in every)
    print(f"  'deixar ir' nos {len(every)} cortes: {dropped_won} ganhos em {dropped_n} negocios-corte"
          f" ({dropped_won / dropped_n:.2%}); as janelas se sobrepoem, o mesmo negocio conta em mais de um corte")

    print(f"\n== 8. Hoje ({last_day}): a regra A aplicada aos abertos ==")
    world = world_at(deals, last_day)
    rules = fit_rules(world, last_day)
    print_curve(rules)
    today = open_at(world, last_day)
    group = {k["id"]: group_of(rules, k, chance_rules(rules, k)) for k in today}
    groups = Counter(group.values())
    for g in ("focar agora", "manter aquecido", "deixar ir"):
        value = sum(k["price"] for k in today if group[k["id"]] == g)
        print(f"  {g:<18} n={groups[g]:5d}  valor de tabela={money(value)}")
    cooling = sum(1 for k in today if chance_rules(rules, k) >= ALIVE_MIN
                  and chance_rules(rules, k, ahead=COOL_DAYS) < ALIVE_MIN)
    print(f"  esfriando hoje (vivos que caem abaixo de {ALIVE_MIN:.0%} em {COOL_DAYS} dias): {cooling}")
    per_seller = Counter(k["seller"] for k in today if group[k["id"]] == "focar agora")
    sellers = sorted({k["seller"] for k in today})
    focus = sorted(per_seller[s] for s in sellers)
    print(f"  'focar agora' por vendedor: min={focus[0]} mediana={focus[len(focus) // 2]} max={focus[-1]}"
          f" ({len(sellers)} vendedores com Engaging aberto)")
    alive_by = Counter(k["seller"] for k in today if group[k["id"]] != "deixar ir")
    alive = sorted(alive_by[s] for s in sellers)
    print(f"  vivos (focar agora + manter aquecido) por vendedor: min={alive[0]}"
          f" mediana={alive[len(alive) // 2]} max={alive[-1]}; vendedores sem nenhum vivo:"
          f" {sum(a == 0 for a in alive)} de {len(sellers)}; sem nenhum em 'focar agora':"
          f" {sum(f == 0 for f in focus)} de {len(sellers)}")
    ages = sorted(k["age"] for k in today)
    oldest_won = max((d["close"] - d["engage"]).days for d in deals if d["stage"] == "Won")
    print(f"  idade dos Engaging abertos hoje: min={ages[0]} mediana={ages[len(ages) // 2]} max={ages[-1]};"
          f" o ganho mais demorado da historia levou {oldest_won} dias;"
          f" abertos hoje mais velhos que isso: {sum(a > oldest_won for a in ages)} de {len(ages)}")
    prospecting = [d for d in deals if d["stage"] == "Prospecting"]
    print(f"  Prospecting: {len(prospecting)} negocios sem data nenhuma: nao podem ser postos no tempo,"
          " nenhum corte os mede; ficam fora dos tres grupos e a tela diz isso.")


if __name__ == "__main__":
    main()
