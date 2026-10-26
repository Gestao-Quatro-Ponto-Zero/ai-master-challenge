"""Explicação em linguagem de vendedor: frases curtas por deal e as 5 linhas de "Como funciona o score".

Todo número vem do modelo do corte (`ScoreModel`) e da linha do deal, formatado por `fmt.py`.
Sem jargão: "chance" (não probabilidade), nada de logit ou coeficiente.

A frase principal dos deals pontuados (Foque, Reative e Limpe) é comparativa: quanto os deals da mesma idade
fecharam no histórico e quanto os novos fecharam ("Deals com 81 dias fecharam 7% das vezes; os novos, 50%.").
"""

from __future__ import annotations

from . import config, fmt
from .score import ScoreModel

NO_ACCOUNT_SENTENCE = "Conta não informada no CRM — preencha; isso não muda o score."
NO_ACCOUNT_SENTENCE_QUALIFIQUE = "Conta não informada no CRM — preencha; isso não muda a ordem da lista."
PHASE_NAMES = {1: "1º mês do trimestre", 2: "2º mês do trimestre", 3: "último mês do trimestre"}


def _days(n) -> str:
    """'1 dia', '12 dias'."""
    n = int(n)
    return f"{fmt.fmt_int(n)} {'dia' if n == 1 else 'dias'}"


def _pct(p: float) -> str:
    """Porcentagem inteira da chance; 'menos de 1%' quando arredonda para zero."""
    value = int(fmt.round_half_up(100 * p))
    return "menos de 1%" if value == 0 else f"{value}%"


def _remaining(left: int) -> str:
    """'falta 1 dia' / 'faltam 12 dias'."""
    return f"{'falta' if left == 1 else 'faltam'} {_days(left)}"


def _min_chance() -> str:
    return fmt.fmt_pct(config.LIMPE_MIN_CHANCE, 0)


def _compare(row, model: ScoreModel) -> str:
    """Frase principal: o que os deals da mesma idade fecharam no histórico, contra os novos."""
    mine, fresh = _pct(row["p_win"]), _pct(model.p_fresh)
    age = _days(row["age_days"])
    if mine == fresh:
        return f"Deals com {age} fecharam {mine} das vezes, o mesmo que os novos."
    return f"Deals com {age} fecharam {mine} das vezes; os novos, {fresh}."


def _value_sentence(row) -> str:
    return (
        f"{row['product']}: valor de tabela {fmt.fmt_usd(row['sales_price'])}; "
        f"valor esperado {fmt.fmt_usd(row['expected_value'])}."
    )


def _foque(row, model: ScoreModel) -> list[str]:
    left = int(row["days_to_knot"])
    window = (
        f"Hoje é o último dia no Foque: depois disso a chance fica abaixo da metade da de um deal novo."
        if left <= 0
        else f"{_remaining(left).capitalize()} para a chance cair à metade da de um deal novo e o deal sair do Foque."
    )
    return [_compare(row, model), _value_sentence(row), window]


def _reative(row, model: ScoreModel) -> list[str]:
    left = int(row["days_to_limpe"])
    if model.limpe_rule == "chance":
        reason = f"a chance de ganho cai abaixo de {_min_chance()}"
    else:
        reason = "nenhum deal foi ganho"
    if left > 0:
        deadline = (
            f"Depois de {_days(model.limpe_after_days)} aberto {reason} — {_remaining(left)}. "
            "Fale com o cliente esta semana."
        )
    else:
        deadline = (
            f"Hoje é o último dia: depois de {_days(model.limpe_after_days)} aberto {reason}. "
            "Fale com o cliente hoje."
        )
    return [_compare(row, model), _value_sentence(row), deadline]


def _limpe_reason(row, model: ScoreModel) -> str:
    cycle = model.max_won_cycle_days
    if cycle is not None and row["age_days"] > cycle:
        return f"nenhum deal foi ganho com mais de {_days(cycle)}"
    return f"a chance cai abaixo de {_min_chance()} depois de {_days(model.limpe_after_days)}"


def _limpe(row, model: ScoreModel) -> list[str]:
    return [
        _compare(row, model),
        "Pergunte ao cliente se ainda quer comprar: se não, marque Lost no CRM; "
        "se sim, atualize o deal e mova para Reative ou Foque.",
        f"São {fmt.fmt_usd(row['sales_price'])} inflando o pipeline ({_limpe_reason(row, model)}).",
    ]


def _qualifique(row, model: ScoreModel) -> list[str]:
    return [
        "Ainda em Prospecting, sem data de engajamento: o histórico não permite estimar a chance.",
        f"{row['product']}: valor de tabela {fmt.fmt_usd(row['sales_price'])}. "
        "Qualifique (marque a primeira conversa) ou descarte.",
    ]


_BUILDERS = {"Foque": _foque, "Reative": _reative, "Limpe": _limpe, "Qualifique": _qualifique}


def explain_deal(row, model: ScoreModel) -> list[str]:
    """De 2 a 4 frases curtas sobre o deal, na ordem em que devem ser lidas.

    `row` é uma linha de `score.score_deals` (Series ou dict). A conta ausente nunca muda o score,
    mas gera um aviso de higiene de CRM.
    """
    category = row["category"]
    sentences = _BUILDERS[category](row, model)
    if not bool(row["has_account"]):
        sentences.append(NO_ACCOUNT_SENTENCE_QUALIFIQUE if category == "Qualifique" else NO_ACCOUNT_SENTENCE)
    return sentences


def _snapshots_line(model: ScoreModel) -> str:
    curve = model.curve
    first, last = curve.train_snapshots[0], curve.train_snapshots[-1]
    n = len(curve.train_snapshots)
    span = f"de {fmt.fmt_date(first)} a {fmt.fmt_date(last)}" if n > 1 else f"de {fmt.fmt_date(first)}"
    photos = f"{fmt.fmt_int(n)} {'foto mensal' if n == 1 else 'fotos mensais'}"
    if model.version == "v2":
        if curve.fallback:
            where = "como não há foto do mesmo ponto do trimestre, usei todas as fotos"
        else:
            where = f"todas do mesmo ponto do trimestre que {fmt.fmt_date(model.as_of_date)} ({PHASE_NAMES[curve.phase]})"
        scope = f"{photos} do pipeline, {span}, {where}"
    else:
        scope = f"{photos} do pipeline, {span}"
    return (
        f"A chance vem do histórico: {scope}, com {fmt.fmt_int(curve.train_rows)} casos de deal "
        f"aberto e o que aconteceu com cada um nos {model.horizon_days} dias seguintes."
    )


def _plateau_line(model: ScoreModel) -> str:
    """Linha 2 da curva v1 (platô + queda), mantida para comparação."""
    curve = model.curve
    start = f"Um deal novo tem {_pct(model.p_fresh)} de chance de ser ganho nos próximos {model.horizon_days} dias"
    half = curve.halving_days
    if half is None:
        return f"{start}, e a chance não muda com a idade."
    if model.knot_days == 0:
        return f"{start}; a chance cai desde o primeiro dia e chega à metade em {_days(round(half))}."
    return (
        f"{start}, e essa chance se mantém até {_days(model.knot_days)} de idade. "
        f"Depois disso ela cai e, {_days(round(half))} depois, vale metade."
    )


def _curve_line(model: ScoreModel) -> str:
    """Linha 2 da curva v2: a chance por idade, que cai desde o primeiro dia."""
    points = "; ".join(
        f"com {_days(age)}, {_pct(model.curve.p_win(age))}" for age in config.EXPLAIN_CURVE_AGES
    )
    return (
        f"A chance cai com a idade desde o primeiro dia: um deal novo tem {_pct(model.p_fresh)} de chance de ser "
        f"ganho nos próximos {model.horizon_days} dias; {points}."
    )


def _result_line(headline_metrics: dict | None) -> str:
    suffix = "Vendedor não entra no score."
    if not headline_metrics:
        return f"O teste no passado ainda não foi rodado. {suffix}"
    return (
        f"Testado no passado em {fmt.fmt_int(headline_metrics['n_cortes'])} datas: o top {fmt.fmt_pct(config.TOP_FRAC, 0)} do score capturou "
        f"{fmt.fmt_pct(headline_metrics['receita_score'], 0)} da receita ganha depois, contra "
        f"{fmt.fmt_pct(headline_metrics['receita_valor'], 0)} ordenando por valor e "
        f"{fmt.fmt_pct(headline_metrics['receita_recencia'], 0)} pelos mais recentes. {suffix}"
    )


def _lists_line(model: ScoreModel) -> str:
    qualifique = "Qualifique: Prospecting, que não tem data nem score."
    if model.limpe_after_days > model.knot_days:
        reative = f"Reative: de {_days(model.knot_days + 1)} a {_days(model.limpe_after_days)}."
    else:
        reative = "Reative: nenhum."
    if model.version == "v1":
        return (
            f"Foque: até {_days(model.knot_days)} de idade. {reative} "
            f"Limpe: acima de {_days(model.limpe_after_days)}, mais do que qualquer deal já ganho. {qualifique}"
        )
    cycle = model.max_won_cycle_days
    if model.limpe_rule == "chance":
        limpe = (
            f"Limpe: acima de {_days(model.limpe_after_days)}, quando a chance cai abaixo de {_min_chance()} "
            f"(ou passa do maior ciclo já ganho, {_days(cycle)})."
        )
    else:
        limpe = f"Limpe: acima de {_days(model.limpe_after_days)}, mais do que qualquer deal já ganho."
    foque = f"Foque: até {_days(model.knot_days)} de idade, enquanto a chance é pelo menos metade da de um deal novo."
    return f"{foque} {reative} {limpe} {qualifique}"


def how_it_works(model: ScoreModel, headline_metrics: dict | None = None) -> list[str]:
    """As 5 linhas de "Como funciona o score".

    `headline_metrics` (preenchido pelo backtest): `n_cortes`, `receita_score`, `receita_valor` e
    `receita_recencia`, todos em fração (média dos cortes). Sem ele, a linha 5 avisa que o teste não rodou.
    """
    ratio = model.price_max / model.price_min
    return [
        _snapshots_line(model),
        _curve_line(model) if model.version == "v2" else _plateau_line(model),
        "Valor esperado = chance × preço de tabela. O score (0 a 100) coloca esse valor numa escala de log: "
        f"100 é um deal novo do produto mais caro, que custa {fmt.fmt_int(ratio)} vezes o mais barato.",
        _lists_line(model),
        _result_line(headline_metrics),
    ]
