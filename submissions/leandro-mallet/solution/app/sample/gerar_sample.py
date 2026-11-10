"""Gera um arquivo de EXEMPLO no formato do contrato deals_scored.json.

Serve só para construir e testar a interface antes do score oficial existir.
Os números aqui são uma conta provisória e simples; o score de verdade é o de
solution/scoring/ e fica em solution/data/scored/deals_scored.json.

Uso (a partir da pasta solution/):
    python app/sample/gerar_sample.py
"""

import csv
import json
import statistics
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

SOLUTION = Path(__file__).resolve().parents[2]
DATA = SOLUTION / "data" / "raw"
OUT = Path(__file__).resolve().parent / "deals_scored.sample.json"

WEIGHTS = {"chance": 40, "valor": 25, "tempo": 20, "conta": 15}
PRODUCT_FIX = {"GTXPro": "GTX Pro"}


def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse(d):
    return date.fromisoformat(d) if d else None


def main():
    pipeline = read("sales_pipeline.csv")
    teams = {r["sales_agent"]: r for r in read("sales_teams.csv")}
    prices = {r["product"]: float(r["sales_price"]) for r in read("products.csv")}
    accounts = {r["account"]: r for r in read("accounts.csv")}

    for r in pipeline:
        r["product"] = PRODUCT_FIX.get(r["product"], r["product"])

    ref = max(parse(r["close_date"]) for r in pipeline if r["close_date"])

    closed = [r for r in pipeline if r["deal_stage"] in ("Won", "Lost")]
    won_by, tot_by = defaultdict(int), defaultdict(int)
    cycle = defaultdict(list)
    acc_won, acc_tot = defaultdict(int), defaultdict(int)
    for r in closed:
        win = r["deal_stage"] == "Won"
        tot_by[r["product"]] += 1
        won_by[r["product"]] += win
        if r["account"]:
            acc_tot[r["account"]] += 1
            acc_won[r["account"]] += win
        if win and r["engage_date"]:
            cycle[r["product"]].append((parse(r["close_date"]) - parse(r["engage_date"])).days)
    base = sum(won_by.values()) / sum(tot_by.values())
    median_cycle = {p: statistics.median(v) for p, v in cycle.items()}
    max_price = max(prices.values())

    deals = []
    for r in pipeline:
        if r["deal_stage"] not in ("Prospecting", "Engaging"):
            continue
        p = r["product"]
        team = teams.get(r["sales_agent"], {})
        acc = r["account"] or None
        eng = parse(r["engage_date"])
        days = (ref - eng).days if eng else None
        wr = won_by[p] / tot_by[p] if tot_by[p] else base

        chance = wr
        valor = (prices.get(p, 0) * wr) / (max_price * base)
        valor = min(1.0, valor ** 0.35)
        if days is None:
            tempo = 0.6
        else:
            tempo = max(0.0, min(1.0, 1.2 - days / (median_cycle.get(p, 60) * 2)))
        if acc and acc_tot[acc]:
            conta = acc_won[acc] / acc_tot[acc]
        else:
            conta = 0.4

        comp = {
            "chance": round(WEIGHTS["chance"] * chance),
            "valor": round(WEIGHTS["valor"] * valor),
            "tempo": round(WEIGHTS["tempo"] * tempo),
            "conta": round(WEIGHTS["conta"] * conta),
        }
        score = sum(comp.values())

        flags, reasons = [], []
        if days is not None and days > median_cycle.get(p, 60) * 1.5:
            flags.append("esfriando")
            reasons.append(
                f"Está há {days} dias aberto; deals de {p} costumam fechar em {round(median_cycle[p])} dias."
            )
        if not acc:
            flags.append("sem_conta")
            reasons.append("Ainda não tem empresa cadastrada: confirme quem é o cliente.")
        if days is None:
            flags.append("sem_data")
            reasons.append("Ainda em prospecção, sem primeiro contato registrado.")
        reasons.insert(0, f"{p} fecha {round(wr * 100)}% das vezes no histórico.")
        if acc and acc_tot[acc]:
            reasons.append(
                f"{acc} já fechou {acc_won[acc]} de {acc_tot[acc]} negociações com a gente."
            )
        if prices.get(p, 0) >= 3000:
            reasons.append(f"Ticket alto: {p} vale US$ {prices[p]:,.0f}.".replace(",", "."))

        if score >= 62:
            action = "focar"
        elif "esfriando" in flags and score < 45:
            action = "desistir"
        elif "esfriando" in flags or "sem_conta" in flags:
            action = "requalificar"
        else:
            action = "focar"

        deals.append({
            "opportunity_id": r["opportunity_id"],
            "sales_agent": r["sales_agent"],
            "manager": team.get("manager"),
            "regional_office": team.get("regional_office"),
            "product": p,
            "account": acc,
            "sector": accounts.get(acc, {}).get("sector") if acc else None,
            "deal_stage": r["deal_stage"],
            "engage_date": r["engage_date"] or None,
            "days_in_pipeline": days,
            "expected_value": round(prices.get(p, 0) * wr),
            "score": score,
            "components": comp,
            "reasons": reasons[:3],
            "flags": flags,
            "action": action,
        })

    deals.sort(key=lambda d: -d["score"])
    out = {
        "reference_date": ref.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_sample": True,
        "component_weights": WEIGHTS,
        "deals": deals,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{len(deals)} deals -> {OUT}")


if __name__ == "__main__":
    main()
