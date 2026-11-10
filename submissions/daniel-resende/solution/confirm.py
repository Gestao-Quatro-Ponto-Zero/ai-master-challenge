"""Confirm the frozen rule A on cut dates it never saw, count each deal once,
and print the time signal in a seller's words.

Nothing of the rule lives here: everything is imported from validate.py, which
stays byte for byte as it was when the rule was frozen.

Run from anywhere:  python submissions/daniel-resende/solution/confirm.py
Standard library only. The system clock is never read.
"""
import contextlib
import datetime as dt
import io
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402

# Fixed by the orchestrator before any run; none of them shaped the rule.
CONFIRM_CUTS = [dt.date(2017, 7, 8), dt.date(2017, 8, 24), dt.date(2017, 9, 24)]
SHAPING_CUTS = sorted(v.CUTS + v.EXTRA_CUTS)  # the nine cuts rule A was revised against
AGES = (0, 30, 60, 90, 120, 138)
GROUPS = ("focar agora", "manter aquecido", "deixar ir")
RULE = "A regras (tempo x valor)"
REFERENCES = ("ref: ordenar por valor", "ref: taxa geral (ordem qualquer)")


def quiet_cut(deals, cut, last_day):
    """validate.run_cut without its printed detail."""
    with contextlib.redirect_stdout(io.StringIO()):
        return v.run_cut(deals, cut, last_day)


def membership(deals, cut):
    """The group rule A gives each deal open at the cut, from what was known then."""
    world = v.world_at(deals, cut)
    rules = v.fit_rules(world, cut)
    return {k["id"]: v.group_of(rules, k, v.chance_rules(rules, k))
            for k in v.open_at(world, cut)}


def group_lines(stats):
    print(f"    {'grupo':<18}{'negocios':>9}{'ganhos':>8}{'perdidos':>10}{'sem desfecho':>14}{'valor ganho':>14}")
    for g in GROUPS:
        st = stats[g]
        print(f"    {g:<18}{st['n']:9d}{st['won']:8d}{st['lost']:10d}{st['no_outcome']:14d}"
              f"{v.money(st['won_value']):>14}")


def m1(deals, last_day):
    print("== M1. A regra congelada em tres cortes que ela nunca viu ==")
    print(f"cortes que moldaram a regra A: {', '.join(str(c) for c in SHAPING_CUTS)}")
    print(f"cortes de confirmacao (fixados antes de rodar): {', '.join(str(c) for c in CONFIRM_CUTS)}")
    print("medida: top 5 da lista de cada vendedor, ganhos e valor ganho em"
          f" {v.HORIZON} dias; empates dividem as vagas")
    results = {}
    for cut in CONFIRM_CUTS:
        summary, _, stats = quiet_cut(deals, cut, last_day)
        results[cut] = stats
        measured = sum(st["n"] for st in stats.values())
        no_outcome = sum(st["no_outcome"] for st in stats.values())
        print(f"\n  corte {cut} (janela ate {cut + dt.timedelta(days=v.HORIZON)}):"
              f" {measured} negocios abertos medidos, {no_outcome} sem desfecho na janela")
        print(f"    {'ordenacao':<36}{'ganhos':>8}{'de':>6}{'valor ganho':>14}")
        for name in REFERENCES + (RULE,):
            wins, slots, value = summary[(name, 5)]
            print(f"    {name:<36}{wins:8.1f}{slots:6.0f}{v.money(value):>14}")
        ref_value = summary[(REFERENCES[0], 5)][2]
        rule_value = summary[(RULE, 5)][2]
        verdict = "GANHA de" if rule_value > ref_value else "PERDE para"
        print(f"    regra A {verdict} 'ordenar por valor': {rule_value / ref_value - 1:+.1%} de valor ganho")
        group_lines(stats)
    return results


def m2(deals, last_day, confirm_stats):
    print("\n== M2. Nenhum negocio contado duas vezes ==")
    print("os grupos em cada um dos doze cortes (um mesmo negocio aparece em varios cortes):")
    final = {d["id"]: d["stage"] for d in deals}
    ever = {g: set() for g in GROUPS}
    ever_confirm = {g: set() for g in GROUPS}
    placements = dict.fromkeys(GROUPS, 0)
    revived = set()
    for cut in sorted(SHAPING_CUTS + CONFIRM_CUTS):
        stats = confirm_stats.get(cut) or quiet_cut(deals, cut, last_day)[2]
        role = "so testou" if cut in CONFIRM_CUTS else "moldou"
        print(f"\n  corte {cut} ({role} a regra)")
        group_lines(stats)
        groups = membership(deals, cut)
        for g in GROUPS:
            ids = {i for i, grp in groups.items() if grp == g}
            assert len(ids) == stats[g]["n"]  # same groups as validate.run_cut
            placements[g] += len(ids)
            if g != "deixar ir":
                revived |= ids & ever["deixar ir"]
            ever[g] |= ids
            if cut in CONFIRM_CUTS:
                ever_confirm[g] |= ids

    def distinct(label, sets):
        print(f"\n  {label}")
        print(f"    {'grupo':<18}{'negocios distintos':>19}{'ganhos depois':>15}{'perdidos depois':>17}"
              f"{'abertos no fim dos dados':>26}")
        for g in GROUPS:
            ids = sets[g]
            won = sum(final[i] == "Won" for i in ids)
            lost = sum(final[i] == "Lost" for i in ids)
            print(f"    {g:<18}{len(ids):19d}{won:15d}{lost:17d}{len(ids) - won - lost:26d}")

    distinct("em negocios DISTINTOS, nos doze cortes (o desfecho e o de qualquer momento ate o fim dos dados):",
             ever)
    distinct("em negocios DISTINTOS, so nos tres cortes de confirmacao:", ever_confirm)
    print(f"\n  colocacoes somadas nos doze cortes: " + ", ".join(f"{g}={placements[g]}" for g in GROUPS)
          + " (e a soma que conta o mesmo negocio varias vezes)")
    print("  um negocio pode ter passado por mais de um grupo em cortes diferentes, por isso as linhas"
          " nao somam o total de negocios")
    print(f"  negocios postos em 'deixar ir' num corte e depois vistos num grupo vivo: {len(revived)}")
    dropped = ever["deixar ir"]
    won = sum(final[i] == "Won" for i in dropped)
    print(f"  SEGURANCA DE 'DEIXAR IR', em negocios distintos: {won} ganhos em {len(dropped)}")


def time_table(deals, day):
    """Who reached each age still open, and what happened to them, as known on `day`."""
    world = v.world_at(deals, day)
    rules = v.fit_rules(world, day)
    longest = rules["longest_win"]
    cohort = [w for w in world if w["engage"] >= rules["first_close"]]
    dead = {k["id"]: v.is_dead(rules, k) for k in v.open_at(world, day)}
    settled_until = day - dt.timedelta(days=longest + 1)
    settled = [w for w in cohort if w["engage"] <= settled_until]
    print(f"\n  como se sabia em {day}: {len(cohort)} negocios engajados desde {rules['first_close']}"
          f" (ficam fora os {len(world) - len(cohort)} engajados antes do 1o fechamento registrado);"
          f" ganho mais demorado visto ate ai: {longest} dias")

    def rows(pool, split_open):
        for age in AGES + (longest + 1,):
            reached = [w for w in pool if w["engage"] + dt.timedelta(days=age) <= day
                       and (w["close"] is None or (w["close"] - w["engage"]).days > age)]
            won = sum(1 for w in reached if w["close"] and w["won"])
            lost = sum(1 for w in reached if w["close"] and not w["won"])
            still = [w for w in reached if w["close"] is None]
            label = f"{age} dias" if age <= longest else f"mais de {longest}"
            line = f"    {label:>12}{len(reached):10d}{won:8d}{lost:10d}"
            if split_open:
                past = sum(1 for w in still if dead[w["id"]])
                line += f"{past:24d}{len(still) - past:24d}"
            else:
                per100 = f"{100 * won / len(reached):.0f}" if reached else "-"
                line += f"{len(still):14d}{per100:>20}"
            print(line)

    print("    (a) todos os que chegaram abertos a idade; os abertos separados entre os que ja passaram da"
          " janela (regra: prazo vencido ou mais velhos que o ganho mais demorado) e os que ainda tinham tempo")
    print(f"    {'chegou a':>12}{'negocios':>10}{'ganhos':>8}{'perdidos':>10}{'abertos fora da janela':>24}"
          f"{'abertos ainda c/ tempo':>24}")
    rows(cohort, True)
    print(f"    (b) so os que ja tiveram tempo de fechar: engajados ate {settled_until}"
          f" ({len(settled)} negocios; {len(cohort) - len(settled)} ficam fora por serem novos demais)")
    if not settled:
        print("        nenhum negocio engajado desde o 1o fechamento tinha tido tempo nessa data: a tabela nao existe")
        return
    print(f"    {'chegou a':>12}{'negocios':>10}{'ganhos':>8}{'perdidos':>10}{'nunca fechou':>14}"
          f"{'ganhos em cada 100':>20}")
    rows(settled, False)


def m3(deals, last_day):
    print("\n== M3. O sinal do tempo nas palavras do vendedor ==")
    print("leitura: 'de cada 100 negocios que chegaram abertos aos N dias, X foram ganhos depois'.")
    print("tratamento dos que nao tiveram tempo de fechar: a tabela (a) os mostra a parte ('abertos ainda"
          " c/ tempo'); a tabela (b), que e a que a tela usa, so conta negocios engajados ha mais dias que"
          " o ganho mais demorado, escolhidos pela data de engajamento e nunca pelo desfecho.")
    for day in [last_day] + v.CUTS:
        time_table(deals, day)


def m4(deals, last_day):
    """Not asked by the prompt: the order the new screen proposes, measured as it is."""
    print("\n== M4. A ordem que a nova tela propoe: vivos por valor, 'limpar' por ultimo ==")
    print("a regra A ordena os vivos por chance x valor; a nova forma ordena os vivos so por valor."
          " Esta secao mede essa ordem, que nenhum corte tinha medido. Nada na regra muda.")
    print("valor ganho no top 5 de cada vendedor, 90 dias; dias restantes = o que falta para o negocio sair"
          " da janela (ganho mais demorado ou prazo, o que vier antes)")
    names = ["ref: ordenar por valor", "regra A (chance x valor)", "vivos por valor (empates divididos)",
             "vivos por valor, menos dias restantes 1o", "vivos por valor, mais dias restantes 1o"]
    print(f"  {'corte':<12}{'papel':<11}" + "".join(f"{n[:21]:>23}" for n in names))
    beats_ref, beats_rule = dict.fromkeys(names[2:], 0), dict.fromkeys(names[2:], 0)
    cuts = sorted(SHAPING_CUTS + CONFIRM_CUTS)
    for cut in cuts:
        summary = quiet_cut(deals, cut, last_day)[0]
        by_id = {d["id"]: d for d in deals}
        world = v.world_at(deals, cut)
        rules = v.fit_rules(world, cut)
        lists = {}
        for k in v.open_at(world, cut):
            deal = by_id[k["id"]]
            won = v.outcome(deal, cut) == "ganho"
            left = min(rules["longest_win"] - k["age"], (v.deadline(k["engage"]) - cut).days)
            dead = v.is_dead(rules, k)
            scores = (-1.0 if dead else k["price"],
                      -1.0 if dead else k["price"] * 1000 + (500 - left),
                      -1.0 if dead else k["price"] * 1000 + left)
            lists.setdefault(k["seller"], []).append((scores, won, float(deal["close_value"]) if won else 0.0))
        values = [summary[("ref: ordenar por valor", 5)][2], summary[(RULE, 5)][2]]
        for i in range(3):
            values.append(sum(v.top_k([(sc[i], won, val) for sc, won, val in items], 5)[1]
                              for items in lists.values()))
        for n, value in zip(names[2:], values[2:]):
            beats_ref[n] += value > values[0]
            beats_rule[n] += value > values[1]
        role = "so testou" if cut in CONFIRM_CUTS else "moldou"
        print(f"  {str(cut):<12}{role:<11}" + "".join(f"{v.money(x):>23}" for x in values))
    for n in names[2:]:
        print(f"  {n}: ganha de 'ordenar por valor' em {beats_ref[n]} de {len(cuts)} cortes;"
              f" ganha da regra A em {beats_rule[n]} de {len(cuts)}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    deals = v.load()
    last_day = max(d[k] for d in deals for k in ("engage", "close") if d[k])
    print(f"data de referencia: {last_day}; regra importada de validate.py, sem alteracao\n")
    confirm_stats = m1(deals, last_day)
    m2(deals, last_day, confirm_stats)
    m3(deals, last_day)
    m4(deals, last_day)


if __name__ == "__main__":
    main()
