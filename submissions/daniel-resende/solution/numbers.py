"""Every number the README cites, one labelled line each, in Portuguese.

All of it is computed from the CSVs and the frozen rule (validate.py, confirm.py),
never read from solution/out/. Deterministic: two runs print the same bytes.

Run from anywhere:  python solution/numbers.py > docs/numeros-saida.txt
Standard library only. The system clock is never read.
"""
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402  (only for the Monday dates and the time-table function)
import confirm  # noqa: E402
import validate as v  # noqa: E402


def money(x):
    return v.money(x)


def split_open(deals, cut):
    """The deals open at the cut, split by the frozen rule into (alive, to_clean)."""
    world = v.world_at(deals, cut)
    rules = v.fit_rules(world, cut)
    alive, clean = [], []
    for known in v.open_at(world, cut):
        (clean if v.is_dead(rules, known) else alive).append(known)
    return world, rules, alive, clean


def line_totals(label, alive, queue, clean):
    value = lambda rows: money(sum(r["price"] for r in rows))
    print(f"{label}: vivos={len(alive)} (valor de tabela {value(alive)}); fila={len(queue)} "
          f"(valor de tabela {value(queue)}); para limpar={len(clean)} (valor de tabela {value(clean)})")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    deals = v.load()
    teams = v.read("sales_teams.csv")
    by_id = {d["id"]: d for d in deals}
    last_day = max(d[k] for d in deals for k in ("engage", "close") if d[k])
    default = build.DEFAULT_MONDAY
    cut = default - dt.timedelta(days=1)
    region_of = {t["sales_agent"]: t["regional_office"] for t in teams}

    print(f"== 1. A segunda padrao {default} (dados fechados em {cut}) ==")
    world, rules, alive, clean = split_open(deals, cut)
    queue = [d for d in deals if d["stage"] == "Prospecting"]
    line_totals("total", alive, queue, clean)
    for region in sorted(set(region_of.values())):
        line_totals(f"regional {region}",
                    [r for r in alive if r["region"] == region],
                    [d for d in queue if d["region"] == region],
                    [r for r in clean if r["region"] == region])
    sellers = sorted(region_of)
    alive_by, queue_by = Counter(r["seller"] for r in alive), Counter(d["seller"] for d in queue)
    print(f"vendedores no total: {len(sellers)}")
    print(f"vendedores sem nenhum negocio vivo: {sum(alive_by[s] == 0 for s in sellers)}")
    print(f"vendedores com fila: {sum(queue_by[s] > 0 for s in sellers)}")
    print(f"vendedores com os tres blocos (vivo, fila e limpar): "
          f"{sum(alive_by[s] > 0 and queue_by[s] > 0 and any(r['seller'] == s for r in clean) for s in sellers)}")

    print("\n== 2. A janela ==")
    inside = rules["closed"] - rules["late"]
    print(f"ganho mais demorado conhecido: {rules['longest_win']} dias")
    print(f"fechamentos dentro do prazo (fim do trimestre seguinte ao do engajamento): "
          f"{inside} de {rules['closed']} ({rules['late']} depois do prazo)")
    print(f"prazo aplicado pela regra: {'sim' if rules['use_deadline'] else 'nao'}")

    print("\n== 3. A evidencia, em negocios distintos, nos doze cortes ==")
    evidence = build.evidence(deals)
    print(f"cortes medidos: {evidence['cuts']}")
    print(f"negocios distintos postos fora da janela: {evidence['distinct_deals_past_window']}")
    print(f"  ganhos depois: {evidence['won_after']}")
    print(f"  perdidos depois: {evidence['lost_after']}")
    print(f"  ainda abertos no fim dos dados: {evidence['still_open_at_data_end']}")

    print("\n== 4. Os tres cortes de confirmacao: top 5 de cada vendedor, 90 dias ==")
    print("(ordenar por valor contra a regra A, medidos por confirm.py/validate.py; so ordem entre vivos, nao confirmada)")
    for confirm_cut in confirm.CONFIRM_CUTS:
        summary = confirm.quiet_cut(deals, confirm_cut, last_day)[0]
        ref_wins, slots, ref_value = summary[(confirm.REFERENCES[0], 5)]
        rule_wins, _, rule_value = summary[(confirm.RULE, 5)]
        print(f"corte {confirm_cut}: ordenar por valor = {ref_wins:.1f} ganhos de {slots:.0f} vagas, "
              f"valor ganho {money(ref_value)}; regra A = {rule_wins:.1f} ganhos, valor ganho {money(rule_value)}")

    print(f"\n== 5. A tabela do tempo em {cut} (a que a tela usa) ==")
    table = build.time_table(world, rules, cut)
    print(f"negocios que tiveram tempo de fechar (engajados ate {table['settled_until']}): {table['deals']}")
    for row in table["rows"]:
        print(f"chegaram abertos aos {row['reached_days']} dias: {row['deals']} negocios; ganhos depois "
              f"{row['won_after']}; perdidos depois {row['lost_after']}; nunca fecharam {row['never_closed']}; "
              f"ganhos em cada 100: {row['won_per_100']}")

    print("\n== 6. As segundas do passado: o que aconteceu com cada bloco ate o fim dos dados ==")
    for monday in build.PAST_MONDAYS:
        past_cut = monday - dt.timedelta(days=1)
        _, _, past_alive, past_clean = split_open(deals, past_cut)
        print(f"segunda {monday} (dados fechados em {past_cut}): vivos={len(past_alive)}; "
              f"para limpar={len(past_clean)}")
        for label, rows in (("vivos", past_alive), ("para limpar", past_clean)):
            end = Counter()
            won_value = 0.0
            for r in rows:
                deal = by_id[r["id"]]
                if deal["close"] is None:
                    end["abertos"] += 1
                elif deal["stage"] == "Won":
                    end["ganhos"] += 1
                    won_value += float(deal["close_value"])
                else:
                    end["perdidos"] += 1
            print(f"  {label}: ganhos={end['ganhos']} perdidos={end['perdidos']} "
                  f"ainda abertos={end['abertos']} valor ganho={money(won_value)}")

    print("\n== 7. Contas e valores ==")
    open_rows = [d for d in deals if d["stage"] in build.OPEN_STAGES]
    print(f"negocios abertos: {len(open_rows)}; sem conta: {sum(not d['account'] for d in open_rows)}")
    print(f"precos de tabela distintos: {len({d['price'] for d in deals})}")
    pairs = ties = 0
    for seller in sellers:
        prices = sorted((r["price"] for r in alive if r["seller"] == seller), reverse=True)
        pairs += max(0, len(prices) - 1)
        ties += sum(a == b for a, b in zip(prices, prices[1:]))
    print(f"pares vizinhos nas listas dos vivos da segunda padrao: {pairs}; com o mesmo valor "
          f"(o desempate decidiu): {ties}")


if __name__ == "__main__":
    main()
