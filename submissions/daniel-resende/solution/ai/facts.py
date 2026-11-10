"""Facts builder: from the score file of the default Monday, the facts of every
target (living deal, seller with any deal, manager), with the keys of
docs/contrato-ia.md. A key exists only when the fact exists.

    python facts.py --examples    # writes docs/fatos-exemplo.json (five real targets)
"""
import contextlib
import io
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
SOLUTION = HERE.parent
OUT = SOLUTION / "out"
EXAMPLES = SOLUTION.parent / "docs" / "fatos-exemplo.json"
DEFAULT_SCORE = "score-2018-01-01.json"

# Label of the next step, from the table of contrato-score.md (sentence case, no final period).
PLAY_LABEL = {
    "trabalhar": "Trabalhar esta semana",
    "confirmar": "Confirmar esta semana se segue de pé",
    "engajar": "Engajar e registrar a data",
    "encerrar": "Encerrar no CRM e tirar da segunda-feira",
}

# How the renderer formats each key; anything not listed is text or an integer.
MONEY = {"value", "alive_value", "queue_value", "clean_value",
         "value_1", "value_2", "value_3"}
DATE = {"engage_date", "window_end", "counted_on", "monday"}
LIST = {"names_without_alive"}


def plural(n, one, many, zero=None):
    """Counted phrase with the right singular, plural and zero form."""
    if n == 0 and zero:
        return zero
    return f"{n} {one if n == 1 else many}"


def days_left_phrase(n):
    if n == 0:
        return "é o último dia na janela"
    return "falta 1 dia na janela" if n == 1 else f"faltam {n} dias na janela"


def days_open_phrase(n):
    return f"aberto há {n} {'dia' if n == 1 else 'dias'}"


def evidence_phrase(deals, won):
    if won == 0:
        return f"nenhum dos {deals} negócios distintos que saíram da janela foi ganho"
    verb = "foi ganho" if won == 1 else "foram ganhos"
    return f"{won} dos {deals} negócios distintos que saíram da janela {verb}"


def phrases(c):
    """Counted phrases of alive/queue/clean/cooling, built by code, never by the model."""
    p = {"alive_phrase": plural(c["alive"], "negócio vivo", "negócios vivos", "nenhum negócio vivo"),
         "queue_phrase": plural(c["queue"], "negócio na fila", "negócios na fila", "nenhum negócio na fila"),
         "clean_phrase": plural(c["clean"], "negócio para limpar", "negócios para limpar", "nada para limpar")}
    if c["cooling"] > 0:
        p["cooling_phrase"] = f"{c['cooling']} esfriando"
    return p


def ensure_out():
    """Load the score files; build them quietly if out/ is missing."""
    if not (OUT / DEFAULT_SCORE).exists() or not (OUT / "index.json").exists():
        sys.path.insert(0, str(SOLUTION))
        import build
        with contextlib.redirect_stdout(io.StringIO()):
            build.main()
    score = json.loads((OUT / DEFAULT_SCORE).read_text(encoding="utf-8"))
    index = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
    return score, index


def deal_facts(score, seller, deal):
    f = {"seller": seller["seller"], "product": deal["product"]}
    if deal.get("account"):
        f["account"] = deal["account"]
    f.update(value=deal["value"], engage_date=deal["engage_date"],
             days_open=deal["days_open"], days_open_phrase=days_open_phrase(deal["days_open"]),
             days_left=deal["days_left"], days_left_phrase=days_left_phrase(deal["days_left"]),
             window_end=deal["window_end"], block=deal["block"],
             play_label=PLAY_LABEL[deal["play"]])
    if deal["cooling"]:
        f["cooling_label"] = "esfriando"
    f.update(rank=deal["rank"], alive_count=seller["headline"]["alive"],
             longest_win_days=score["meta"]["window"]["longest_win_days"])
    if deal.get("time_sentence"):
        f["time_sentence"] = deal["time_sentence"]
    f["monday"] = score["meta"]["monday"]
    return f


def counts(src):
    return {k: src[k] for k in ("alive", "alive_value", "cooling", "queue",
                                "queue_value", "clean", "clean_value")}


def briefing_facts(score, index, seller):
    h = seller["headline"]
    ev = index["evidence"]
    f = {"seller": seller["seller"], "monday": score["meta"]["monday"], **counts(h),
         "longest_win_days": score["meta"]["window"]["longest_win_days"],
         "evidence_deals": ev["distinct_deals_past_window"], "evidence_won": ev["won_after"],
         "evidence_phrase": evidence_phrase(ev["distinct_deals_past_window"], ev["won_after"]),
         **phrases(h)}
    for n, d in enumerate(seller["alive"][:3], 1):
        f[f"product_{n}"] = d["product"]
        if d.get("account"):
            f[f"account_{n}"] = d["account"]
        f[f"value_{n}"] = d["value"]
        f[f"days_left_{n}"] = d["days_left"]
        f[f"days_left_phrase_{n}"] = days_left_phrase(d["days_left"])
    return f


def manager_facts(score, index, m):
    ev = index["evidence"]
    names = [s["seller"] for s in score["team"]["by_seller"]
             if s["manager"] == m["manager"] and s["alive"] == 0]
    f = {"manager": m["manager"], "region": m["region"], "monday": score["meta"]["monday"],
         "sellers": m["sellers"], "sellers_without_alive": m["sellers_without_alive"]}
    if names:
        f["names_without_alive"] = names
    n, w = m["sellers"], m["sellers_without_alive"]
    f["without_alive_phrase"] = ("nenhum vendedor sem negócio vivo" if w == 0 else
                                 f"{w} de {n} vendedores sem nenhum negócio vivo")
    f.update(counts(m))
    f.update(phrases(m))
    f.update(evidence_deals=ev["distinct_deals_past_window"], evidence_won=ev["won_after"],
             evidence_phrase=evidence_phrase(ev["distinct_deals_past_window"], ev["won_after"]))
    return f


def build_all(score=None, index=None):
    """Every target as {id: {id, kind, target, facts}}, in a stable order."""
    if score is None:
        score, index = ensure_out()
    out = {}
    for s in score["sellers"]:
        for d in s["alive"]:
            out[f"deal:{d['id']}"] = {
                "id": f"deal:{d['id']}", "kind": "deal",
                "target": {"deal_id": d["id"], "seller": s["seller"]},
                "facts": deal_facts(score, s, d)}
    for s in score["sellers"]:
        if s["alive"] or s["queue"] or s["clean"]:
            out[f"briefing:{s['seller']}"] = {
                "id": f"briefing:{s['seller']}", "kind": "briefing",
                "target": {"seller": s["seller"]},
                "facts": briefing_facts(score, index, s)}
    for m in score["team"]["by_manager"]:
        out[f"manager:{m['manager']}"] = {
            "id": f"manager:{m['manager']}", "kind": "manager",
            "target": {"manager": m["manager"]},
            "facts": manager_facts(score, index, m)}
    return out


def pick_examples(targets):
    """Five targets: a cooling deal, a deal without account, a deal with one, a seller, a manager."""
    deals = [t for t in targets.values() if t["kind"] == "deal"]
    chosen = []
    for pred in (lambda t: "cooling_label" in t["facts"],
                 lambda t: "account" not in t["facts"] and "cooling_label" not in t["facts"],
                 lambda t: "account" in t["facts"] and "cooling_label" not in t["facts"]):
        chosen.append(next(t for t in deals if pred(t)))
    chosen.append(next(t for t in targets.values()
                       if t["kind"] == "briefing" and "product_1" in t["facts"]))
    chosen.append(next(t for t in targets.values() if t["kind"] == "manager"))
    return chosen


def main():
    if "--examples" not in sys.argv:
        print(__doc__)
        return 0
    targets = build_all()
    EXAMPLES.write_text(json.dumps(pick_examples(targets), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"wrote {EXAMPLES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
