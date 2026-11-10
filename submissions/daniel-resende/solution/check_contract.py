"""Check that every file in solution/out/ obeys docs/contrato-score.md.

Exit 0 only if nothing is wrong. Each failure is one line: file | deal | rule.
When solution/ai/textos.json exists it also runs check_texts() from
solution/ai/check.py and fails on any error (or if that module is missing).

Run from anywhere:  python solution/check_contract.py   (after build.py)
Standard library only. The system clock is never read.
"""
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as v  # noqa: E402

OUT = HERE / "out"
AI = HERE / "ai"
DEFAULT = "2018-01-01"
PAST = ["2017-10-02", "2017-09-04", "2017-08-07", "2017-07-03", "2017-06-05"]
LAST_DAY = "2017-12-31"
AGES = [0, 30, 60, 90, 120, 138]
NUMBERS = ["alive", "alive_value", "cooling", "queue", "queue_value", "clean", "clean_value"]
DEAL_FIELDS = ["id", "block", "rank", "product", "account", "value", "engage_date", "days_open",
               "deadline", "days_left", "window_end", "cooling", "time_sentence", "clean_fact",
               "play", "flags", "after"]
AFTER_FIELDS = ["result", "close_date", "close_value", "days_after"]
SELLER_AFTER = ["alive_won", "alive_lost", "alive_open", "alive_won_value",
                "clean_won", "clean_lost", "clean_open"]
PLAY = {"vivo": "trabalhar", "fila": "engajar", "limpar": "encerrar"}
NO_HISTORY = "Sem histórico suficiente nesta data."
# `account` is a display-only field the contract gives every deal; it never enters a score.
FORBIDDEN_KEYS = v.LEAK_FIELDS - {"account"}

errors = []


def fail(file, deal, rule):
    errors.append(f"{file} | {deal or '-'} | {rule}")


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def is_date(x):
    try:
        return isinstance(x, str) and dt.date.fromisoformat(x).isoformat() == x
    except ValueError:
        return False


def day(x):
    return dt.date.fromisoformat(x)


def keys_are(file, who, obj, expected, label):
    if not isinstance(obj, dict) or sorted(obj) != sorted(expected):
        fail(file, who, f"{label}: fields must be exactly {sorted(expected)}, got "
                        f"{sorted(obj) if isinstance(obj, dict) else type(obj).__name__}")
        return False
    return True


def scan(file, node, path="", in_after=False):
    """No percent sign anywhere; no leak field as a key outside `after`."""
    if isinstance(node, dict):
        for k, val in node.items():
            if "%" in k:
                fail(file, path, "percent sign in a key")
            if k in FORBIDDEN_KEYS and not in_after:
                fail(file, path, f"leak field {k!r} as a key outside `after`")
            scan(file, val, f"{path}/{k}", in_after or k == "after")
    elif isinstance(node, list):
        for i, val in enumerate(node):
            scan(file, val, f"{path}/{i}", in_after)
    elif isinstance(node, str) and "%" in node:
        fail(file, path, "percent sign in a text")


def check_deal(file, d, block, meta, rank, seller_name):
    who = f"{d.get('id')} ({seller_name})" if isinstance(d, dict) else str(d)
    if not keys_are(file, who, d, DEAL_FIELDS, "deal"):
        return
    past, longest = meta["past"], meta["window"]["longest_win_days"]
    monday, cut = day(meta["monday"]), day(meta["data_closed"])
    if not (isinstance(d["id"], str) and d["id"]):
        fail(file, who, "id must be text")
    if d["block"] != block:
        fail(file, who, f"block {d['block']!r} inside the list {block!r}")
    if d["rank"] != rank or not is_int(d["rank"]):
        fail(file, who, f"rank {d['rank']!r}, expected {rank}")
    if not isinstance(d["product"], str) or not d["product"]:
        fail(file, who, "product must be text")
    if d["account"] is not None and not isinstance(d["account"], str):
        fail(file, who, "account must be text or null")
    if not is_num(d["value"]) or d["value"] <= 0:
        fail(file, who, "value must be a positive number")
    if not isinstance(d["cooling"], bool):
        fail(file, who, "cooling must be a boolean")
    want_flags = ["sem_conta"] if d["account"] is None else []
    if d["flags"] != want_flags:
        fail(file, who, f"flags {d['flags']!r}, expected {want_flags!r}")
    if d["play"] != PLAY[d["block"]] and not (d["block"] == "vivo" and d["play"] == "confirmar"):
        fail(file, who, f"play {d['play']!r} does not fit block {d['block']!r}")

    if block == "fila":
        if past:
            fail(file, who, "queue deal in a past Monday")
        for f in ("engage_date", "days_open", "deadline", "days_left", "window_end",
                  "time_sentence", "clean_fact", "after"):
            if d[f] is not None:
                fail(file, who, f"{f} must be null in the queue")
        if d["cooling"]:
            fail(file, who, "cooling must be false in the queue")
        return

    # every dated deal: dates and ages
    if not (is_date(d["engage_date"]) and is_date(d["deadline"]) and is_int(d["days_open"])):
        fail(file, who, "engage_date, deadline and days_open must be dates and an integer")
        return
    engage = day(d["engage_date"])
    if d["days_open"] != (cut - engage).days or d["days_open"] < 0:
        fail(file, who, f"days_open {d['days_open']} is not cut minus engage_date")
    if d["deadline"] != v.deadline(engage).isoformat():
        fail(file, who, f"deadline {d['deadline']} is not the end of the quarter after the engage quarter")
    deadline = day(d["deadline"])
    applied = meta["window"]["deadline_applied"]
    outside = d["days_open"] > longest or (applied and (deadline - cut).days <= 0)

    if block == "vivo":
        if outside:
            fail(file, who, "living deal is outside the window")
        want_left = longest - d["days_open"]
        if applied:
            want_left = min(want_left, (deadline - monday).days)
        if not is_int(d["days_left"]) or d["days_left"] < 0:
            fail(file, who, f"days_left {d['days_left']!r} must be an integer >= 0")
        elif d["days_left"] != want_left:
            fail(file, who, f"days_left {d['days_left']} expected {want_left}")
        if is_int(d["days_left"]) and d["window_end"] != (monday + dt.timedelta(days=d["days_left"])).isoformat():
            fail(file, who, "window_end is not the Monday plus days_left")
        if d["cooling"] != (d["days_open"] > meta["cooling_after_days"]):
            fail(file, who, "cooling must be true exactly when days_open > 90")
        if d["play"] != ("confirmar" if d["cooling"] else "trabalhar"):
            fail(file, who, "play of a living deal must follow cooling")
        if d["clean_fact"] is not None:
            fail(file, who, "clean_fact must be null on a living deal")
        sentence = d["time_sentence"]
        table = meta["time_table"]
        if not isinstance(sentence, str):
            fail(file, who, "time_sentence missing on a living deal")
        elif not table["exists"]:
            if sentence != NO_HISTORY:
                fail(file, who, "no table on this date: time_sentence must be the no-history sentence")
        else:
            counted = cut.strftime("%d/%m/%Y")
            row = [r for r in table["rows"] if r["reached_days"] <= d["days_open"]][-1]
            if "Cerca de" not in sentence or counted not in sentence:
                fail(file, who, "time_sentence must carry 'Cerca de' and the date of the count")
            if f"Cerca de {row['won_per_100']} em cada 100" not in sentence:
                fail(file, who, f"time_sentence does not state the {row['reached_days']}-day row ({row['won_per_100']})")
            if (row["reached_days"] == 0) == (f"aos {row['reached_days']} dias" in sentence):
                fail(file, who, "time_sentence uses the wrong form for its age band")
    else:  # limpar
        if not outside:
            fail(file, who, "deal to clean is inside the window")
        for f in ("days_left", "window_end", "time_sentence"):
            if d[f] is not None:
                fail(file, who, f"{f} must be null in a deal to clean")
        if d["cooling"]:
            fail(file, who, "cooling must be false in a deal to clean")
        if d["clean_fact"] not in ("prazo", "idade"):
            fail(file, who, f"clean_fact {d['clean_fact']!r} must be 'prazo' or 'idade'")

    # what happened afterwards
    after = d["after"]
    if not past:
        if after is not None:
            fail(file, who, "after must be null on the default Monday")
        return
    if not keys_are(file, who, after, AFTER_FIELDS, "after"):
        return
    if after["result"] not in ("ganho", "perdido", "aberto"):
        fail(file, who, f"after.result {after['result']!r}")
    elif after["result"] == "aberto":
        if any(after[f] is not None for f in AFTER_FIELDS[1:]):
            fail(file, who, "after of an open deal must carry nulls")
    else:
        if not is_date(after["close_date"]) or not is_num(after["close_value"]) or not is_int(after["days_after"]):
            fail(file, who, "after of a closed deal needs close_date, close_value, days_after")
        else:
            closed = day(after["close_date"])
            if not cut < closed <= day(LAST_DAY):
                fail(file, who, "after.close_date must fall after the cut and within the data")
            if after["days_after"] != (closed - cut).days:
                fail(file, who, "after.days_after is not close_date minus the cut")


def seller_totals(sellers):
    out = {n: sum(s["headline"][n] or 0 for s in sellers) for n in NUMBERS}
    out["sellers"] = len(sellers)
    out["sellers_without_alive"] = sum(s["headline"]["alive"] == 0 for s in sellers)
    return out


def same_numbers(file, who, row, want):
    for k, w in want.items():
        got = row.get(k)
        if not is_num(got) or abs(got - w) > 1e-6:
            fail(file, who, f"team number {k} is {got!r}, the sellers sum to {w!r}")
    for k in NUMBERS:
        if k.endswith("_value") and not isinstance(row.get(k), float):
            fail(file, who, f"{k} must be a float")


def check_score(name, index, deals_by_cut):
    path = OUT / name
    data = json.loads(path.read_text(encoding="utf-8"))
    scan(name, data)
    if not keys_are(name, None, data, ["meta", "sellers", "team"], "file"):
        return None
    meta = data["meta"]
    if not keys_are(name, None, meta, ["monday", "data_closed", "past", "window", "cooling_after_days",
                                       "time_table", "outcomes_until"], "meta"):
        return None
    monday_s = name[len("score-"):-len(".json")]
    if meta["monday"] != monday_s or not is_date(monday_s):
        fail(name, None, "meta.monday does not match the file name")
        return None
    monday = day(monday_s)
    if monday.weekday() != 0:
        fail(name, None, "the date is not a Monday")
    cut = monday - dt.timedelta(days=1)
    if meta["data_closed"] != cut.isoformat():
        fail(name, None, "data_closed must be the Monday minus one day")
    past = monday_s != DEFAULT
    if meta["past"] is not past:
        fail(name, None, f"meta.past must be {past}")
    if meta["outcomes_until"] != (LAST_DAY if past else None):
        fail(name, None, "meta.outcomes_until wrong")
    if meta["cooling_after_days"] != 90:
        fail(name, None, "cooling_after_days must be 90")
    w = meta["window"]
    if keys_are(name, None, w, ["longest_win_days", "deadline_applied", "closings_known",
                                "closings_after_deadline"], "meta.window"):
        if not (is_int(w["longest_win_days"]) and isinstance(w["deadline_applied"], bool)
                and is_int(w["closings_known"]) and is_int(w["closings_after_deadline"])):
            fail(name, None, "meta.window types")
    else:
        return None

    t = meta["time_table"]
    if keys_are(name, None, t, ["exists", "counted_on", "settled_until", "deals", "rows"], "time_table"):
        if t["counted_on"] != cut.isoformat():
            fail(name, None, "time_table.counted_on must be the cut")
        if t["settled_until"] != (cut - dt.timedelta(days=w["longest_win_days"] + 1)).isoformat():
            fail(name, None, "time_table.settled_until must be cut minus longest win minus one")
        if not t["exists"] and t["rows"] != []:
            fail(name, None, "time_table.rows must be [] when exists is false")
        if t["exists"] and [r.get("reached_days") for r in t["rows"]] != AGES:
            fail(name, None, f"time_table rows must be the ages {AGES}")
        last = None
        for r in t["rows"]:
            if not keys_are(name, f"row {r.get('reached_days')}", r,
                            ["reached_days", "deals", "won_after", "lost_after", "never_closed", "won_per_100"],
                            "time_table row"):
                continue
            if r["won_after"] + r["lost_after"] + r["never_closed"] != r["deals"]:
                fail(name, f"row {r['reached_days']}", "won + lost + never_closed != deals")
            if r["won_per_100"] != (round(100 * r["won_after"] / r["deals"]) if r["deals"] else 0):
                fail(name, f"row {r['reached_days']}", "won_per_100 is not won_after / deals")
            if last is not None and r["deals"] > last:
                fail(name, f"row {r['reached_days']}", "deals must not grow with age")
            last = r["deals"]
        if t["exists"] and t["rows"] and t["rows"][0]["deals"] != t["deals"]:
            fail(name, None, "first row must hold all the settled deals")
    else:
        return None

    sellers = data["sellers"]
    names = [s.get("seller") for s in sellers]
    if names != sorted(names) or names != [s["seller"] for s in index["sellers"]] or len(names) != 35:
        fail(name, None, "sellers must be the 35 of index.json, in alphabetical order")
    seen_ids, per_block = set(), {"vivo": set(), "limpar": set(), "fila": set()}
    for s in sellers:
        if not keys_are(name, s.get("seller"), s, ["seller", "manager", "region", "headline",
                                                   "alive", "queue", "clean", "after"], "seller"):
            continue
        who = s["seller"]
        if not keys_are(name, who, s["headline"], NUMBERS, "headline"):
            continue
        if past and s["queue"]:
            fail(name, who, "queue must be [] in a past Monday")
        for block, key in (("vivo", "alive"), ("fila", "queue"), ("limpar", "clean")):
            items = s[key]
            for pos, d in enumerate(items, 1):
                check_deal(name, d, block, meta, pos, who)
                if isinstance(d, dict) and "id" in d:
                    if d["id"] in seen_ids:
                        fail(name, d["id"], "deal listed twice")
                    seen_ids.add(d["id"])
                    per_block[block].add(d["id"])
            ordered = ok_order(key, items)
            if not ordered:
                fail(name, who, f"order of {key!r} breaks the contract")
        h = s["headline"]
        want = {"alive": len(s["alive"]), "alive_value": sum(d["value"] for d in s["alive"]),
                "cooling": sum(bool(d["cooling"]) for d in s["alive"]),
                "queue": None if past else len(s["queue"]),
                "queue_value": None if past else sum(d["value"] for d in s["queue"]),
                "clean": len(s["clean"]), "clean_value": sum(d["value"] for d in s["clean"])}
        for k, wv in want.items():
            if wv is None:
                if h[k] is not None:
                    fail(name, who, f"headline.{k} must be null in a past Monday")
            elif not is_num(h[k]) or abs(h[k] - wv) > 1e-6:
                fail(name, who, f"headline.{k} is {h[k]!r}, the list gives {wv!r}")
        for k in ("alive_value", "clean_value"):
            if not isinstance(h[k], float):
                fail(name, who, f"headline.{k} must be a float")
        if past:
            check_seller_after(name, s)
        elif s["after"] is not None:
            fail(name, who, "seller.after must be null on the default Monday")

    # the open deals of the frozen world must be exactly the listed ones, with the same block
    world = v.world_at(deals_by_cut["deals"], cut)
    rules = v.fit_rules(world, cut)
    open_known = v.open_at(world, cut)
    want_alive = {k["id"] for k in open_known if not v.is_dead(rules, k)}
    want_clean = {k["id"] for k in open_known if v.is_dead(rules, k)}
    if per_block["vivo"] != want_alive:
        fail(name, None, f"living ids differ from the frozen rule ({len(per_block['vivo'])} vs {len(want_alive)})")
    if per_block["limpar"] != want_clean:
        fail(name, None, f"ids to clean differ from the frozen rule ({len(per_block['limpar'])} vs {len(want_clean)})")
    prospecting = {d["id"] for d in deals_by_cut["deals"] if d["stage"] == "Prospecting"}
    if per_block["fila"] != (set() if past else prospecting):
        fail(name, None, "queue ids must be exactly the Prospecting deals (none in the past)")
    if (w["longest_win_days"], w["deadline_applied"], w["closings_known"], w["closings_after_deadline"]) != (
            rules["longest_win"], rules["use_deadline"], rules["closed"], rules["late"]):
        fail(name, None, "meta.window differs from validate.fit_rules at the cut")

    check_team(name, data, sellers, past)
    if monday_s == DEFAULT:
        check_default(name, data, index)
    return data


def ok_order(key, items):
    if not all(isinstance(d, dict) and is_num(d.get("value")) for d in items):
        return True  # shape errors are reported elsewhere
    try:
        if key == "alive":
            keyf = lambda d: (-d["value"], -d["days_left"], d["id"])
        elif key == "queue":
            keyf = lambda d: (-d["value"], d["id"])
        else:
            keyf = lambda d: (-d["value"], -d["days_open"], d["id"])
        return [keyf(d) for d in items] == sorted(keyf(d) for d in items)
    except TypeError:
        return True


def check_seller_after(name, s):
    who = s["seller"]
    a = s["after"]
    if not keys_are(name, who, a, SELLER_AFTER, "seller.after"):
        return
    count = lambda items, r: sum(1 for d in items if isinstance(d.get("after"), dict) and d["after"].get("result") == r)
    want = {"alive_won": count(s["alive"], "ganho"), "alive_lost": count(s["alive"], "perdido"),
            "alive_open": count(s["alive"], "aberto"),
            "alive_won_value": sum(d["after"]["close_value"] for d in s["alive"]
                                   if isinstance(d.get("after"), dict) and d["after"].get("result") == "ganho"),
            "clean_won": count(s["clean"], "ganho"), "clean_lost": count(s["clean"], "perdido"),
            "clean_open": count(s["clean"], "aberto")}
    for k, wv in want.items():
        if not is_num(a[k]) or abs(a[k] - wv) > 1e-6:
            fail(name, who, f"seller.after.{k} is {a[k]!r}, the deals give {wv!r}")


def check_team(name, data, sellers, past):
    team = data["team"]
    if not keys_are(name, None, team, ["by_seller", "by_manager", "by_region", "total"], "team"):
        return
    base = ["sellers", "sellers_without_alive"] + NUMBERS
    if [r.get("seller") for r in team["by_seller"]] != [s["seller"] for s in sellers]:
        fail(name, None, "team.by_seller must list the 35 sellers in order")
    for r in team["by_seller"]:
        s = next((x for x in sellers if x["seller"] == r.get("seller")), None)
        if s is None or not keys_are(name, r.get("seller"), r, ["seller", "manager", "region"] + base, "by_seller"):
            continue
        if (r["manager"], r["region"]) != (s["manager"], s["region"]):
            fail(name, r["seller"], "by_seller manager or region differs")
        same_numbers(name, r["seller"], r, seller_totals([s]))
    managers = sorted({s["manager"] for s in sellers})
    if [r.get("manager") for r in team["by_manager"]] != managers:
        fail(name, None, "team.by_manager must list each manager once, in order")
    for r in team["by_manager"]:
        group = [s for s in sellers if s["manager"] == r.get("manager")]
        if group and keys_are(name, r["manager"], r, ["manager", "region"] + base, "by_manager"):
            if r["region"] != group[0]["region"]:
                fail(name, r["manager"], "by_manager region differs")
            same_numbers(name, r["manager"], r, seller_totals(group))
    regions = sorted({s["region"] for s in sellers})
    if [r.get("region") for r in team["by_region"]] != regions:
        fail(name, None, "team.by_region must list each region once, in order")
    for r in team["by_region"]:
        group = [s for s in sellers if s["region"] == r.get("region")]
        if group and keys_are(name, r["region"], r, ["region"] + base, "by_region"):
            same_numbers(name, r["region"], r, seller_totals(group))
    if keys_are(name, "total", team["total"], NUMBERS + ["sellers", "sellers_without_alive"], "total") \
            or isinstance(team["total"], dict):
        same_numbers(name, "total", team["total"], seller_totals(sellers))
    if past:
        for level in ("by_seller", "by_manager", "by_region"):
            for r in team[level]:
                if r.get("queue") != 0 or r.get("queue_value") != 0:
                    fail(name, r.get("seller") or r.get("manager") or r.get("region"),
                         "queue numbers in team must be 0 in a past Monday")
        if team["total"].get("queue") != 0 or team["total"].get("queue_value") != 0:
            fail(name, "total", "queue numbers in team must be 0 in a past Monday")


def check_default(name, data, index):
    by_region = {r["region"]: r for r in data["team"]["by_region"]}
    # the contract's claims about the default Monday
    if by_region.get("Central", {}).get("queue") != 500 or by_region.get("Central", {}).get("alive") != 0:
        fail(name, "Central", "contract: Central holds the whole queue (500) and no living deal")
    for region, n in (("East", 45), ("West", 70)):
        r = by_region.get(region, {})
        if r.get("alive") != n or r.get("queue") != 0:
            fail(name, region, f"contract: {region} has {n} living deals and no queue")
    for s in data["sellers"]:
        if s["alive"] and s["queue"] and s["clean"]:
            fail(name, s["seller"], "contract: no seller has the three blocks on the default Monday")
    best = min(data["sellers"], key=lambda s: (-len(s["alive"]), s["seller"]))["seller"]
    if index.get("default_seller") != best:
        fail("index.json", best, f"default_seller is {index.get('default_seller')!r}, expected the one with most living deals")


def check_index():
    name = "index.json"
    data = json.loads((OUT / name).read_text(encoding="utf-8"))
    scan(name, data)
    if not keys_are(name, None, data, ["written_by", "default_monday", "default_seller", "mondays",
                                       "sellers", "evidence", "value_note"], "index"):
        return None
    if data["written_by"] != "solution/build.py":
        fail(name, None, "written_by")
    if data["default_monday"] != DEFAULT:
        fail(name, None, "default_monday must be 2018-01-01")
    want = [DEFAULT] + PAST
    if [m.get("monday") for m in data["mondays"]] != want:
        fail(name, None, f"mondays must be {want}, most recent first")
    for m in data["mondays"]:
        if keys_are(name, m.get("monday"), m, ["monday", "data_closed", "file", "past"], "mondays row"):
            if m["file"] != f"score-{m['monday']}.json" or not (OUT / m["file"]).is_file():
                fail(name, m["monday"], "file missing or misnamed")
            if m["data_closed"] != (day(m["monday"]) - dt.timedelta(days=1)).isoformat():
                fail(name, m["monday"], "data_closed")
            if m["past"] is not (m["monday"] != DEFAULT):
                fail(name, m["monday"], "past flag")
    teams = sorted(v.read("sales_teams.csv"), key=lambda t: t["sales_agent"])
    want_sellers = [{"seller": t["sales_agent"], "manager": t["manager"], "region": t["regional_office"]}
                    for t in teams]
    if data["sellers"] != want_sellers or len(want_sellers) != 35:
        fail(name, None, "sellers must be the 35 of sales_teams.csv, alphabetical")
    if data["default_seller"] not in [t["seller"] for t in want_sellers]:
        fail(name, None, "default_seller is not a seller")
    ev = data["evidence"]
    if keys_are(name, None, ev, ["cuts", "distinct_deals_past_window", "won_after", "lost_after",
                                 "still_open_at_data_end", "source"], "evidence"):
        if not all(is_int(ev[k]) for k in ev if k != "source"):
            fail(name, None, "evidence numbers must be integers")
        elif ev["won_after"] + ev["lost_after"] + ev["still_open_at_data_end"] != ev["distinct_deals_past_window"]:
            fail(name, None, "evidence parts do not add up")
    vn = data["value_note"]
    if keys_are(name, None, vn, ["list_prices", "closed_without_value_on_open_rows"], "value_note"):
        if vn["closed_without_value_on_open_rows"] is not True or not is_int(vn["list_prices"]):
            fail(name, None, "value_note")
    return data


def check_ai():
    texts = AI / "textos.json"
    if not texts.exists():
        return
    module = AI / "check.py"
    if not module.is_file():
        fail("ai/textos.json", None, "ai/check.py is missing")
        return
    sys.path.insert(0, str(AI))
    try:
        spec = importlib.util.spec_from_file_location("ai_check", module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        problems = mod.check_texts(texts)
    except Exception as exc:  # a broken checker is a failure, not a pass
        fail("ai/check.py", None, f"check_texts could not run: {type(exc).__name__}: {exc}")
        return
    finally:
        sys.path.remove(str(AI))
    for p in problems:
        fail("ai/textos.json", None, str(p))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not (OUT / "index.json").is_file():
        print("out/index.json | - | missing: run build.py first")
        return 1
    index = check_index()
    deals = {"deals": v.load()}
    expected = {f"score-{m}.json" for m in [DEFAULT] + PAST}
    found = {p.name for p in OUT.glob("score-*.json")}
    for name in sorted(expected - found):
        fail(name, None, "file missing")
    for name in sorted(found - expected):
        fail(name, None, "file is not one of the six Mondays")
    for name in sorted(expected & found):
        if index is not None:
            check_score(name, index, deals)
    check_ai()
    for line in errors[:200]:
        print(line)
    if len(errors) > 200:
        print(f"... e mais {len(errors) - 200} falhas")
    if errors:
        print(f"FALHOU: {len(errors)} falhas")
        return 1
    print(f"contrato ok: index.json e {len(expected)} segundas conferidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
