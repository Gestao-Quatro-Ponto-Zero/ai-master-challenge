"""Build the files the interface and the AI layer read (docs/contrato-score.md).

One score file per Monday into solution/out/, plus index.json. The rule that
separates a living deal from one to clean is imported from the frozen
validate.py and is not rewritten here: a Monday is scored with the cut on the
day before, using only what was known then.

Run from anywhere:  python submissions/daniel-resende/solution/build.py
Standard library only. The system clock is never read.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import confirm  # noqa: E402
import validate as v  # noqa: E402

OUT = HERE / "out"
DEFAULT_MONDAY = dt.date(2018, 1, 1)
PAST_MONDAYS = [dt.date(2017, 10, 2), dt.date(2017, 9, 4), dt.date(2017, 8, 7),
                dt.date(2017, 7, 3), dt.date(2017, 6, 5)]
TABLE_AGES = (0, 30, 60, 90, 120, 138)
COOLING_AFTER_DAYS = 90
OPEN_STAGES = ("Prospecting", "Engaging")
NUMBERS = ("alive", "alive_value", "cooling", "queue", "queue_value", "clean", "clean_value")


def br_date(day):
    return day.strftime("%d/%m/%Y")


def time_table(world, rules, cut):
    """Who reached each age still open and what happened afterwards, as known at the cut.

    Only deals engaged since the first recorded closing and longer ago than the
    slowest win: chosen by engage date, never by outcome.
    """
    settled_until = cut - dt.timedelta(days=rules["longest_win"] + 1)
    settled = [w for w in world if rules["first_close"] <= w["engage"] <= settled_until]
    table = {"exists": bool(settled), "counted_on": cut.isoformat(),
             "settled_until": settled_until.isoformat(), "deals": len(settled), "rows": []}
    for age in TABLE_AGES if settled else ():
        reached = [w for w in settled if w["close"] is None or (w["close"] - w["engage"]).days > age]
        won = sum(1 for w in reached if w["close"] and w["won"])
        lost = sum(1 for w in reached if w["close"] and not w["won"])
        table["rows"].append({"reached_days": age, "deals": len(reached), "won_after": won,
                              "lost_after": lost, "never_closed": len(reached) - won - lost,
                              "won_per_100": round(100 * won / len(reached)) if reached else 0})
    return table


def time_sentence(table, days_open):
    if not table["exists"]:
        return "Sem histórico suficiente nesta data."
    row = [r for r in table["rows"] if r["reached_days"] <= days_open][-1]
    counted = br_date(dt.date.fromisoformat(table["counted_on"]))
    if row["reached_days"] == 0:
        return (f"Cerca de {row['won_per_100']} em cada 100 negócios foram ganhos depois de"
                f" engajados (conta de {counted}).")
    return (f"Cerca de {row['won_per_100']} em cada 100 negócios que chegaram abertos aos"
            f" {row['reached_days']} dias foram ganhos depois (conta de {counted}).")


def after_of(deal, cut):
    """What happened to a listed deal after a past Monday, up to the end of the data."""
    if deal["close"] is None:
        return {"result": "aberto", "close_date": None, "close_value": None, "days_after": None}
    return {"result": "ganho" if deal["stage"] == "Won" else "perdido",
            "close_date": deal["close"].isoformat(), "close_value": float(deal["close_value"]),
            "days_after": (deal["close"] - cut).days}


def build_monday(deals, teams, monday, last_day):
    cut = monday - dt.timedelta(days=1)
    past = cut < last_day
    by_id = {d["id"]: d for d in deals}
    world = v.world_at(deals, cut)  # everything after the cut is removed here
    rules = v.fit_rules(world, cut)
    table = time_table(world, rules, cut)
    blocks = {t["sales_agent"]: {"alive": [], "queue": [], "clean": []} for t in teams}

    for known in v.open_at(world, cut):
        deal = by_id[known["id"]]
        deadline = v.deadline(known["engage"])
        dead = v.is_dead(rules, known)
        record = {
            "id": known["id"], "block": "limpar" if dead else "vivo", "rank": 0,
            "product": known["product"], "account": deal["account"] or None,
            "value": known["price"], "engage_date": known["engage"].isoformat(),
            "days_open": known["age"], "deadline": deadline.isoformat(),
            "days_left": None, "window_end": None, "cooling": False, "time_sentence": None,
            "clean_fact": None, "play": "encerrar",
            "flags": [] if deal["account"] else ["sem_conta"],
            "after": after_of(deal, cut) if past else None,
        }
        if dead:
            record["clean_fact"] = "idade" if known["age"] > rules["longest_win"] else "prazo"
        else:
            left = rules["longest_win"] - known["age"]
            if rules["use_deadline"]:  # the deadline bounds the window only when the rule applies it
                left = min(left, (deadline - monday).days)
            if left < 0:  # an explicit check: `assert` vanishes under python -O
                raise ValueError(f"negative days_left for {known['id']} on {monday}")
            record.update({
                "days_left": left, "window_end": (monday + dt.timedelta(days=left)).isoformat(),
                "cooling": known["age"] > COOLING_AFTER_DAYS,
                "time_sentence": time_sentence(table, known["age"]),
            })
            record["play"] = "confirmar" if record["cooling"] else "trabalhar"
        blocks[known["seller"]]["clean" if dead else "alive"].append(record)

    if not past:  # the queue cannot be placed in the past: Prospecting rows carry no date
        for deal in deals:
            if deal["stage"] == "Prospecting":
                blocks[deal["seller"]]["queue"].append({
                    "id": deal["id"], "block": "fila", "rank": 0, "product": deal["product"],
                    "account": deal["account"] or None, "value": deal["price"],
                    "engage_date": None, "days_open": None, "deadline": None, "days_left": None,
                    "window_end": None, "cooling": False, "time_sentence": None,
                    "clean_fact": None, "play": "engajar",
                    "flags": [] if deal["account"] else ["sem_conta"], "after": None})

    sellers = []
    for team in sorted(teams, key=lambda t: t["sales_agent"]):
        b = blocks[team["sales_agent"]]
        b["alive"].sort(key=lambda r: (-r["value"], -r["days_left"], r["id"]))
        b["queue"].sort(key=lambda r: (-r["value"], r["id"]))
        b["clean"].sort(key=lambda r: (-r["value"], -r["days_open"], r["id"]))
        for items in b.values():
            for position, record in enumerate(items, 1):
                record["rank"] = position
        headline = {
            "alive": len(b["alive"]), "alive_value": float(sum(r["value"] for r in b["alive"])),
            "cooling": sum(r["cooling"] for r in b["alive"]),
            "queue": None if past else len(b["queue"]),
            "queue_value": None if past else float(sum(r["value"] for r in b["queue"])),
            "clean": len(b["clean"]), "clean_value": float(sum(r["value"] for r in b["clean"])),
        }
        after = None
        if past:
            count = lambda items, result: sum(r["after"]["result"] == result for r in items)
            after = {"alive_won": count(b["alive"], "ganho"), "alive_lost": count(b["alive"], "perdido"),
                     "alive_open": count(b["alive"], "aberto"),
                     "alive_won_value": sum(r["after"]["close_value"] for r in b["alive"]
                                            if r["after"]["result"] == "ganho"),
                     "clean_won": count(b["clean"], "ganho"), "clean_lost": count(b["clean"], "perdido"),
                     "clean_open": count(b["clean"], "aberto")}
        sellers.append({"seller": team["sales_agent"], "manager": team["manager"],
                        "region": team["regional_office"], "headline": headline,
                        "alive": b["alive"], "queue": b["queue"], "clean": b["clean"], "after": after})

    def total(rows):
        out = {n: sum(r["headline"][n] or 0 for r in rows) for n in NUMBERS}
        out.update({n: float(out[n]) for n in NUMBERS if n.endswith("_value")})
        out["sellers"] = len(rows)
        out["sellers_without_alive"] = sum(r["headline"]["alive"] == 0 for r in rows)
        return out

    by_seller = [{"seller": s["seller"], "manager": s["manager"], "region": s["region"],
                  **total([s])} for s in sellers]
    by_manager = [{"manager": m, "region": next(s["region"] for s in sellers if s["manager"] == m),
                   **total([s for s in sellers if s["manager"] == m])}
                  for m in sorted({s["manager"] for s in sellers})]
    by_region = [{"region": g, **total([s for s in sellers if s["region"] == g])}
                 for g in sorted({s["region"] for s in sellers})]
    return {
        "meta": {"monday": monday.isoformat(), "data_closed": cut.isoformat(), "past": past,
                 "window": {"longest_win_days": rules["longest_win"],
                            "deadline_applied": rules["use_deadline"],
                            "closings_known": rules["closed"],
                            "closings_after_deadline": rules["late"]},
                 "cooling_after_days": COOLING_AFTER_DAYS, "time_table": table,
                 "outcomes_until": last_day.isoformat() if past else None},
        "sellers": sellers,
        "team": {"by_seller": by_seller, "by_manager": by_manager, "by_region": by_region,
                 "total": total(sellers)},
    }


def evidence(deals):
    """Distinct deals ever placed outside the window on the twelve measured cuts."""
    final = {d["id"]: d["stage"] for d in deals}
    cuts = sorted(confirm.SHAPING_CUTS + confirm.CONFIRM_CUTS)
    dropped = set()
    for cut in cuts:
        dropped |= {i for i, group in confirm.membership(deals, cut).items() if group == "deixar ir"}
    won = sum(final[i] == "Won" for i in dropped)
    lost = sum(final[i] == "Lost" for i in dropped)
    return {"cuts": len(cuts), "distinct_deals_past_window": len(dropped), "won_after": won,
            "lost_after": lost, "still_open_at_data_end": len(dropped) - won - lost,
            "source": "docs/confirmacao-saida.txt"}


def write(name, payload):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    deals = v.load()
    teams = v.read("sales_teams.csv")
    last_day = max(d[k] for d in deals for k in ("engage", "close") if d[k])
    if DEFAULT_MONDAY - dt.timedelta(days=1) != last_day:
        raise SystemExit(f"the default Monday does not follow the last day of data ({last_day})")
    mondays = []
    for monday in [DEFAULT_MONDAY] + PAST_MONDAYS:
        score = build_monday(deals, teams, monday, last_day)
        name = f"score-{monday.isoformat()}.json"
        write(name, score)
        mondays.append({"monday": monday.isoformat(), "data_closed": score["meta"]["data_closed"],
                        "file": name, "past": score["meta"]["past"]})
        if monday == DEFAULT_MONDAY:
            # no seller has all three blocks on the default Monday: open on the longest living list
            default_seller = min(score["sellers"], key=lambda s: (-len(s["alive"]), s["seller"]))["seller"]
        t = score["team"]["total"]
        print(f"{name}: vivos={t['alive']} fila={t['queue']} limpar={t['clean']}")
    write("index.json", {
        "written_by": "solution/build.py", "default_monday": DEFAULT_MONDAY.isoformat(),
        "default_seller": default_seller, "mondays": mondays,
        "sellers": [{"seller": t["sales_agent"], "manager": t["manager"], "region": t["regional_office"]}
                    for t in sorted(teams, key=lambda t: t["sales_agent"])],
        "evidence": evidence(deals),
        "value_note": {"list_prices": len({d["price"] for d in deals}),
                       "closed_without_value_on_open_rows": all(
                           d["close_value"] == "" for d in deals if d["stage"] in OPEN_STAGES)},
    })
    print(f"index.json: segunda padrao {DEFAULT_MONDAY}, vendedor padrao {default_seller}")


if __name__ == "__main__":
    main()
