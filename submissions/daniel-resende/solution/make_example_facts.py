"""Write docs/fatos-exemplo.json: for five real open deals, the exact facts the
AI layer would receive (see docs/contrato-ia.md). No text is generated here.

Run from anywhere:  python submissions/daniel-resende/solution/make_example_facts.py
"""
import contextlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "fatos-exemplo.json"
GROUP_ORDER = ["focar agora", "manter aquecido", "sem data", "deixar ir"]


def play_of(record):
    """The next step, chosen by rule (docs/contrato-score.md, section "Jogadas")."""
    if record["stage"] == "Prospecting":
        return "qualificar"
    if record["group"] == "deixar ir":
        return "encerrar_ou_requalificar"
    if record["chance_in_30_days"] < v.ALIVE_MIN:
        return "confirmar_esta_semana"
    return "priorizar" if record["group"] == "focar agora" else "toque_leve"


def main():
    deals = v.load()
    last_day = max(d[k] for d in deals for k in ("engage", "close") if d[k])
    world = v.world_at(deals, last_day)
    rules = v.fit_rules(world, last_day)
    with contextlib.redirect_stdout(io.StringIO()):
        evidence = v.group_evidence([v.run_cut(deals, cut, last_day) for cut in v.CUTS])
    account = {d["id"]: d["account"] for d in deals}
    longest_win = max((d["close"] - d["engage"]).days for d in deals if d["stage"] == "Won")

    records = []
    for known in v.open_at(world, last_day):
        chance = v.chance_rules(rules, known)
        records.append({
            "id": known["id"], "stage": "Engaging", "seller": known["seller"],
            "manager": known["manager"], "region": known["region"],
            "product": known["product"], "account": account[known["id"]] or None,
            "value": known["price"], "engage_date": known["engage"].isoformat(),
            "days_open": known["age"], "deadline": v.deadline(known["engage"]).isoformat(),
            "days_to_deadline": (v.deadline(known["engage"]) - last_day).days,
            "chance": round(chance, 4),
            "chance_in_30_days": round(v.chance_rules(rules, known, ahead=v.COOL_DAYS), 4),
            "expected_value": round(chance * known["price"], 2),
            "group": v.group_of(rules, known, chance),
        })
    for d in deals:
        if d["stage"] == "Prospecting":
            records.append({
                "id": d["id"], "stage": "Prospecting", "seller": d["seller"],
                "manager": d["manager"], "region": d["region"], "product": d["product"],
                "account": d["account"] or None, "value": d["price"], "engage_date": None,
                "days_open": None, "deadline": None, "days_to_deadline": None, "chance": None,
                "chance_in_30_days": None, "expected_value": None, "group": "sem data",
            })

    lists = defaultdict(list)
    for r in records:
        lists[r["seller"]].append(r)
    for items in lists.values():
        items.sort(key=lambda r: (GROUP_ORDER.index(r["group"]), -(r["expected_value"] or 0),
                                  -r["value"], r["id"]))
        in_group = {g: sum(1 for r in items if r["group"] == g) for g in GROUP_ORDER}
        for position, r in enumerate(items, 1):
            r["rank"], r["list_size"] = position, len(items)
            r["play"] = play_of(r)
            r["list_groups"] = in_group

    # Five real deals, one per situation the screen has to explain; ties by id.
    wanted = ["priorizar", "confirmar_esta_semana", "toque_leve", "encerrar_ou_requalificar",
              "qualificar"]
    examples = []
    for play in wanted:
        pool = sorted((r for r in records if r["play"] == play), key=lambda r: (r["rank"], r["id"]))
        r = pool[0]
        facts = {
            "seller": r["seller"], "product": r["product"], "value": r["value"],
            "group": r["group"], "play": r["play"], "rank": r["rank"],
            "list_size": r["list_size"], "list_focus": r["list_groups"]["focar agora"],
            "list_warm": r["list_groups"]["manter aquecido"],
            "list_no_date": r["list_groups"]["sem data"], "list_drop": r["list_groups"]["deixar ir"],
            "reference_date": last_day.isoformat(),
            "window_days": v.HORIZON, "longest_win_days": longest_win,
            "closings_total": rules["closed"], "closings_after_deadline": rules["late"],
        }
        if r["account"]:
            facts["account"] = r["account"]
        if r["stage"] == "Engaging":
            ev = evidence[r["group"]]
            facts.update({
                "engage_date": r["engage_date"], "days_open": r["days_open"],
                "deadline": r["deadline"], "days_to_deadline": r["days_to_deadline"],
                "group_test_deals": ev["n"], "group_test_won": ev["won"],
                "group_test_won_value": round(ev["won_value"]),
            })
        examples.append({"deal_id": r["id"], "stage": r["stage"], "facts": facts, "score_record": r})

    OUT.write_text(json.dumps({
        "reference_date": last_day.isoformat(),
        "written_by": "solution/make_example_facts.py",
        "note": "facts = everything a generated text may cite; score_record = the record of"
                " docs/contrato-score.md the facts were taken from",
        "examples": examples,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT.name}: {len(examples)} negocios reais ({', '.join(e['deal_id'] for e in examples)})")


if __name__ == "__main__":
    main()
