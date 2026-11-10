"""Upkeep report: has the closing window moved since it was last stored?

    python drift.py --store   writes solution/window.json from the current CSVs
    python drift.py           re-fits from the CSVs and prints how far each value moved

Exit 0 in both cases; exit 1 only if window.json is missing. The window is read
with the frozen rule of validate.py, never rewritten here. When the CSVs get new
rows, run it, read the verdict, and store again only on purpose.

Standard library only. The system clock is never read: "the date" is the last
day that appears in the data.
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402  (the same time-table function the score files use)
import validate as v  # noqa: E402

STORE = HERE / "window.json"
ROW_KEYS = ("deals", "won_after", "lost_after", "never_closed", "won_per_100")


def fit():
    deals = v.load()
    last_day = max(d[k] for d in deals for k in ("engage", "close") if d[k])
    world = v.world_at(deals, last_day)
    rules = v.fit_rules(world, last_day)
    table = build.time_table(world, rules, last_day)
    return {"date": last_day.isoformat(), "longest_win_days": rules["longest_win"],
            "closings_known": rules["closed"], "closings_after_deadline": rules["late"],
            "time_table": table["rows"]}


def report(old, new):
    lines, moved = [], []
    for key, label in (("longest_win_days", "ganho mais demorado (dias)"),
                       ("closings_known", "fechamentos conhecidos"),
                       ("closings_after_deadline", "fechamentos depois do prazo")):
        diff = new[key] - old[key]
        lines.append(f"{label}: guardado {old[key]}, agora {new[key]} ({diff:+d})")
        if diff:
            moved.append(f"{label} {diff:+d}")
    old_rows = {r["reached_days"]: r for r in old["time_table"]}
    new_rows = {r["reached_days"]: r for r in new["time_table"]}
    for age in sorted(set(old_rows) | set(new_rows)):
        if age not in old_rows or age not in new_rows:
            lines.append(f"tabela do tempo, {age} dias: linha {'nova' if age in new_rows else 'sumiu'}")
            moved.append(f"linha de {age} dias {'nova' if age in new_rows else 'sumiu'}")
            continue
        parts = [f"{k} {old_rows[age][k]} -> {new_rows[age][k]}" for k in ROW_KEYS
                 if old_rows[age][k] != new_rows[age][k]]
        lines.append(f"tabela do tempo, {age} dias: " + ("; ".join(parts) if parts else "sem mudanca"))
        if old_rows[age]["won_per_100"] != new_rows[age]["won_per_100"]:
            moved.append(f"ganhos em cada 100 aos {age} dias {old_rows[age]['won_per_100']} -> "
                         f"{new_rows[age]['won_per_100']}")
    lines.insert(0, f"data guardada {old['date']}; data agora {new['date']}")
    if not moved:
        verdict = "janela estável"
        if old["date"] != new["date"]:
            verdict += " (a data dos dados mudou, a janela não)"
    else:
        verdict = "janela mudou: " + "; ".join(moved)
    return lines, verdict


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    store = "--store" in sys.argv[1:]
    new = fit()
    if store:
        STORE.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"janela guardada em window.json (data {new['date']}, ganho mais demorado "
              f"{new['longest_win_days']} dias)")
        return 0
    if not STORE.is_file():
        print("window.json nao existe: rode `python drift.py --store` uma vez")
        return 1
    old = json.loads(STORE.read_text(encoding="utf-8"))
    lines, verdict = report(old, new)
    print("\n".join(lines))
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
