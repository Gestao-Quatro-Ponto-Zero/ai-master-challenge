"""Documentação com números gerados.

1. Blocos `<!-- AUTO:nome -->...<!-- /AUTO:nome -->` dos .md são reescritos a partir de `facts.json`
   (e, a partir do bloco 3, de `backtest_metrics.json`): `python -m scorer.docs`.
   `python -m scorer.docs --check` só confere (exit 1 se algum documento estiver desatualizado).
2. Conferência dos números da prosa (fora dos blocos AUTO): `unmatched_numbers` devolve os números do
   texto que não saem de nenhum fato; `tests/test_docs_numbers.py` exige que a lista seja vazia.

Para criar um bloco novo, registre um renderizador com `@block("nome")`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from . import config
from .facts import load_facts
from .fmt import fmt_date, fmt_dec, fmt_int, fmt_month, fmt_pct, fmt_pp, fmt_quarter, fmt_usd, round_half_up

# =============================================================================================
# Blocos AUTO
# =============================================================================================
AUTO_RE = re.compile(r"<!-- AUTO:(?P<name>[\w-]+) -->\n(?P<body>.*?)\n?<!-- /AUTO:(?P=name) -->", re.S)
AUTO_OPEN_RE = re.compile(r"<!-- AUTO:([\w-]+) -->")

BLOCKS: dict[str, Callable[[dict], str]] = {}


def block(name: str):
    """Registra o renderizador de um bloco AUTO. Ele recebe `sources` ({'facts': ..., 'backtest': ...})."""

    def register(func):
        BLOCKS[name] = func
        return func

    return register


def load_sources() -> dict:
    """Carrega as fontes de números: facts.json e, se já existir, backtest_metrics.json."""
    backtest = None
    if config.BACKTEST_JSON.exists():
        with open(config.BACKTEST_JSON, encoding="utf-8") as handle:
            backtest = json.load(handle)
    return {"facts": load_facts(), "backtest": backtest}


def render_blocks(sources: dict | None = None) -> dict[str, str]:
    """Renderiza todos os blocos registrados: nome -> markdown."""
    sources = sources or load_sources()
    return {name: func(sources).strip("\n") for name, func in BLOCKS.items()}


def render_text(text: str, blocks: dict[str, str]) -> str:
    """Troca o conteúdo de cada bloco AUTO do texto; erro se o marcador não tem renderizador."""
    opened = AUTO_OPEN_RE.findall(text)
    if len(opened) != len(AUTO_RE.findall(text)):
        raise ValueError("marcador AUTO sem fechamento (ou com nome diferente no fechamento)")
    unknown = sorted(set(opened) - set(blocks))
    if unknown:
        raise KeyError(f"marcador AUTO sem renderizador: {unknown}")

    def replace(match: re.Match) -> str:
        name = match.group("name")
        return f"<!-- AUTO:{name} -->\n{blocks[name]}\n<!-- /AUTO:{name} -->"

    return AUTO_RE.sub(replace, text)


def read_doc(path) -> str:
    return Path(path).read_text(encoding="utf-8")  # a leitura em modo texto já normaliza CRLF para LF


def inject(path, blocks: dict[str, str] | None = None, write: bool = True) -> bool:
    """Atualiza os blocos AUTO de um documento. Devolve True se o texto mudou."""
    blocks = blocks if blocks is not None else render_blocks()
    old = read_doc(path)
    new = render_text(old, blocks)
    if new != old and write:
        Path(path).write_text(new, encoding="utf-8", newline="\n")
    return new != old


# ---------------------------------------------------------------------------------------------
# Formatação das tabelas
# ---------------------------------------------------------------------------------------------
def md_table(headers: list[str], rows: list[list], align: str | None = None) -> str:
    """Tabela markdown. `align` tem uma letra por coluna ('l' ou 'r'); o padrão é texto + números."""
    align = align or "l" + "r" * (len(headers) - 1)
    rule = ["---:" if a == "r" else ":---" for a in align]
    lines = [f"| {' | '.join(headers)} |", f"| {' | '.join(rule)} |"]
    lines += [f"| {' | '.join(str(cell) for cell in row)} |" for row in rows]
    return "\n".join(lines)


def _yes(flag: bool) -> str:
    return "sim" if flag else "não"


def _num(x) -> str:
    """Inteiro sem casas; com meio dia, uma casa."""
    return fmt_int(x) if float(x).is_integer() else fmt_dec(x, 1)


# ---------------------------------------------------------------------------------------------
# Renderizadores do DATA_QUALITY.md (investigações 2a, 2b e 2c)
# ---------------------------------------------------------------------------------------------
@block("dq-meses")
def _dq_meses(src: dict) -> str:
    rows = [
        [fmt_month(r["mes"]), fmt_int(r["n"]), fmt_pct(r["win_rate"]), _num(r["ciclo_mediano"]), fmt_pct(r["pct_ciclo_rapido"], 0)]
        for r in src["facts"]["evidencia_2a_q1"]["por_mes_de_fechamento"]
    ]
    fast = src["facts"]["ciclos"]["ciclo_rapido_dias"]
    headers = ["Mês de fechamento", "Fechados", "Win rate", "Ciclo mediano (dias)", f"% com ciclo de até {fast} dias"]
    return md_table(headers, rows)


@block("dq-trimestres")
def _dq_trimestres(src: dict) -> str:
    ev = src["facts"]["evidencia_2a_q1"]
    rows = [
        [fmt_quarter(r["trimestre"]), fmt_int(r["n"]), fmt_pct(r["win_rate"]), _num(r["ciclo_mediano"])]
        for r in ev["por_trimestre_de_fechamento"]
    ]
    after = [r for r in ev["por_trimestre_de_fechamento"] if r["trimestre"] != ev["primeiro_trimestre"]]
    rows.append(
        [f"Depois de {fmt_quarter(ev['primeiro_trimestre'])}", fmt_int(sum(r["n"] for r in after)),
         fmt_pct(ev["win_rate_depois_do_primeiro_trimestre"]), "—"]
    )
    return md_table(["Trimestre de fechamento", "Fechados", "Win rate", "Ciclo mediano (dias)"], rows)


@block("dq-coortes")
def _dq_coortes(src: dict) -> str:
    fast = src["facts"]["ciclos"]["ciclo_rapido_dias"]
    rows = []
    for r in src["facts"]["evidencia_2a_q1"]["por_coorte_de_engajamento"]:
        floor, gap = r["piso_do_recorte_dias"], r["folga_dias"]
        rows.append(
            [fmt_month(r["mes"]), fmt_int(r["n_fechados"]), fmt_pct(r["win_rate"]), fmt_int(r["ciclo_min"]),
             "—" if floor is None else fmt_int(floor), "—" if gap is None else fmt_int(gap),
             fmt_pct(r["pct_ciclo_rapido"], 0)]
        )
    headers = ["Coorte (mês de engajamento)", "Fechados", "Win rate", "Ciclo mínimo (dias)",
               "Piso do recorte (dias)", "Folga (dias)", f"% com ciclo de até {fast} dias"]
    return md_table(headers, rows)


@block("dq-cruzamento")
def _dq_cruzamento(src: dict) -> str:
    ev = src["facts"]["evidencia_2a_q1"]
    table = ev["cruzamento_trimestre_engajamento_x_fechamento"]
    columns = sorted({col for row in table.values() for col in row})
    rows = [[fmt_quarter(eng)] + [fmt_int(table[eng][c]) if c in table[eng] else "—" for c in columns] for eng in table]
    text = md_table(["Engajado em \\ fechado em"] + [fmt_quarter(c) for c in columns], rows)
    return (
        f"{text}\n\nFechados no mesmo trimestre do engajamento: {fmt_int(ev['fechados_no_mesmo_trimestre'])}; "
        f"no trimestre seguinte: {fmt_int(ev['fechados_no_trimestre_seguinte'])}; "
        f"fora da regra: {fmt_int(ev['fechados_fora_da_regra_q_q1'])}."
    )


@block("dq-posicao-trimestre")
def _dq_posicao(src: dict) -> str:
    fast = src["facts"]["ciclos"]["ciclo_rapido_dias"]
    names = {1: "1º mês (jan, abr, jul, out)", 2: "2º mês (fev, mai, ago, nov)", 3: "3º mês (mar, jun, set, dez)"}
    rows = [
        [names[r["mes_do_trimestre"]], fmt_int(r["n"]), fmt_pct(r["win_rate"]), _num(r["ciclo_mediano"]),
         fmt_pct(r["pct_ciclo_rapido"], 0)]
        for r in src["facts"]["evidencia_2a_q1"]["por_mes_dentro_do_trimestre"]
    ]
    headers = ["Mês dentro do trimestre", "Fechados", "Win rate", "Ciclo mediano (dias)", f"% com ciclo de até {fast} dias"]
    return md_table(headers, rows)


@block("dq-criterio-2a")
def _dq_criterio_2a(src: dict) -> str:
    ev = src["facts"]["evidencia_2a_q1"]
    crit = ev["criterio"]
    first_month = fmt_month(ev["primeiro_mes_com_fechamento"])
    months = ", ".join(fmt_month(m)[:3] for m in crit["c2_meses_de_fim_de_trimestre"])
    rows = [
        [f"(i) o {fmt_quarter(ev['primeiro_trimestre'])} só tem fechamentos em {first_month}",
         f"{fmt_int(crit['c1_fechamentos_do_1o_trimestre_fora_do_1o_mes'])} fechamentos fora de {first_month}",
         "0", _yes(crit["c1_vale"])],
        [f"(ii) win rate de {first_month} perto dos meses de fim de trimestre ({months})",
         f"{fmt_pct(crit['c2_win_rate_do_1o_mes'])} contra {fmt_pct(crit['c2_media_dos_meses_de_fim_de_trimestre'])} "
         f"({fmt_pp(crit['c2_diferenca_pp'] / 100)})",
         f"±{fmt_int(crit['c2_tolerancia_pp'])} pp", _yes(crit["c2_vale"])],
        [f"(iii) coortes engajadas antes de {fmt_date(ev['primeiro_fechamento'])} sem ciclos curtos (truncamento)",
         f"maior folga entre o ciclo mínimo e o piso do recorte: {fmt_int(crit['c3_maior_folga_dias'])} dias "
         f"({fmt_int(crit['c3_coortes_avaliadas'])} coortes)",
         f"{fmt_int(crit['c3_tolerancia_dias'])} dias", _yes(crit["c3_vale"])],
    ]
    table = md_table(["Condição", "Medido", "Limite", "Vale?"], rows, "lllr")
    verdict = (
        "**Resultado: artefato de recorte confirmado (as três condições valem).**"
        if crit["artefato_de_recorte"]
        else "**Resultado: artefato de recorte NÃO confirmado (alguma condição falhou).**"
    )
    support = (
        f"Reforço sem tolerância: nas coortes com piso de {fmt_int(src['facts']['ciclos']['ciclo_rapido_dias'])} "
        f"dias ou mais, {fmt_pct(crit['c3_pct_ciclo_rapido_coortes_com_piso_alto'], 0)} dos fechamentos são rápidos; "
        f"nas coortes sem recorte, no mínimo {fmt_pct(crit['c3_pct_ciclo_rapido_coortes_sem_recorte_minimo'], 0)}."
    )
    return f"{table}\n\n{verdict}\n\n{support}"


@block("dq-razao-preco")
def _dq_razao(src: dict) -> str:
    ev = src["facts"]["evidencia_2c_close_value"]

    def row(label: str, s: dict) -> list:
        return [label, fmt_int(s["n"])] + [fmt_dec(s[k], 3) for k in ("media", "mediana", "p5", "p95", "min", "max")]

    rows = [row("Todos os ganhos", ev["geral"])]
    rows += [row(f"Produto: {name}", s) for name, s in ev["por_produto"].items()]
    rows += [row(f"Fechamento em {fmt_quarter(q)}", s) for q, s in ev["por_trimestre_de_fechamento"].items()]
    table = md_table(["Recorte", "Ganhos", "Média", "Mediana", "p5", "p95", "Mín", "Máx"], rows)
    crit = ev["criterio"]
    lines = [
        f"- Média por produto: de {fmt_dec(crit['media_por_produto_minima'], 3)} a "
        f"{fmt_dec(crit['media_por_produto_maxima'], 3)} (faixa aceita: {fmt_dec(crit['faixa_aceita_min'], 2)} a "
        f"{fmt_dec(crit['faixa_aceita_max'], 2)}): {_yes(crit['faixa_vale'])}.",
        f"- Variação da média entre trimestres: {fmt_dec(crit['variacao_entre_trimestres_pp'], 1)} pp "
        f"(limite: {fmt_int(crit['variacao_aceita_pp'])} pp): {_yes(crit['variacao_vale'])}.",
        f"- Perdidos com `close_value` = 0: {fmt_int(ev['perdidos_com_close_value_zero'])} de {fmt_int(ev['perdidos_n'])}; "
        f"ganhos com `close_value` = 0: {fmt_int(ev['ganhos_com_close_value_zero'])}.",
    ]
    return table + "\n\n" + "\n".join(lines)


@block("dq-vendedores")
def _dq_vendedores(src: dict) -> str:
    ev = src["facts"]["evidencia_2b_vendedores"]

    def people(items: list[dict]) -> list[list]:
        return [[r["sales_agent"], r["manager"], r["regional_office"]] for r in items]

    headers = ["Vendedor", "Manager", "Região"]
    summary = (
        f"Cadastro: {fmt_int(ev['vendedores_cadastro'])} vendedores; com algum deal: {fmt_int(ev['vendedores_com_deals'])}; "
        f"com deal aberto na data de referência: {fmt_int(ev['vendedores_com_deals_abertos'])}; "
        f"sem nenhum deal: {fmt_int(ev['vendedores_sem_deals'])}; só com deals fechados: {fmt_int(ev['vendedores_so_com_fechados'])}."
    )
    return "\n\n".join(
        [
            summary,
            "**Sem nenhum deal no CRM**\n\n" + md_table(headers, people(ev["sem_deals"]), "lll"),
            "**Só com deals fechados (nenhum aberto)**\n\n" + md_table(headers, people(ev["so_com_fechados"]), "lll"),
            "Times sem nenhum vendedor fora do pipeline: " + ", ".join(ev["managers_sem_vendedor_sem_deals"]) + ".",
        ]
    )


# =============================================================================================
# Renderizadores do SCORING.md (backtest_metrics.json)
# =============================================================================================
_PENDING_BACKTEST = "_Backtest ainda não rodado: execute `python -m scorer.validate`._"
_METHOD_ORDER = ("score", "score_v1", "valor", "recencia", "aleatorio", "p_only")
_BEST_OF = ("score", "score_v1", "valor", "recencia", "aleatorio")  # o diagnóstico `p_only` não disputa o melhor
_LISTS = ("Foque", "Reative", "Limpe")
_PHASE_LABELS = {"1": "1º mês do trimestre (jan, abr, jul, out)", "2": "2º mês (fev, mai, ago, nov)", "3": "3º mês (mar, jun, set, dez)"}


def _scoring_block(name: str):
    """Como `block`, mas devolve um aviso quando o JSON do backtest ainda não existe."""

    def register(func):
        def render(src: dict) -> str:
            bt = src.get("backtest")
            return _PENDING_BACKTEST if bt is None else func(bt)

        render.__name__ = func.__name__
        BLOCKS[name] = render
        return func

    return register


def _labels(bt: dict) -> dict:
    return bt["config"]["method_labels"]


def _usd(x) -> str:
    return "—" if x is None else fmt_usd(x)


def _pct0(x) -> str:
    return "—" if x is None else fmt_pct(x, 1)


def _pp(x) -> str:
    return "—" if x is None else fmt_pp(x)


def _v1_of(bt: dict, cut: str) -> dict:
    return next(c for c in bt["cuts_v1"] if c["cut"] == cut)


def _rule_label(model: dict) -> str:
    """Quem decide o começo do Limpe: a chance mínima ou o maior ciclo já ganho."""
    return f"chance abaixo de {fmt_pct(config.LIMPE_MIN_CHANCE, 0)}" if model["limpe_rule"] == "chance" else "maior ciclo já ganho"


@_scoring_block("scoring-diagnostico")
def _sc_diagnostico(bt: dict) -> str:
    diag = bt["diagnostico_fases"]
    groups = diag["grupos"]
    names = {"fim_de_trimestre": "Fotos de fim de trimestre", "meio_de_trimestre": "Fotos de meio de trimestre", "todas": "Todas juntas"}
    order = ("fim_de_trimestre", "meio_de_trimestre", "todas")

    def cell(row):
        return f"{_pct0(row['taxa_ganho_90d'])} ({fmt_int(row['n'])})"

    rows = []
    for i, band in enumerate(groups["todas"]["por_faixa"]):
        rows.append([band["faixa"]] + [cell(groups[g]["por_faixa"][i]) for g in order])
    t1 = md_table(["Idade do deal na foto"] + [names[g] for g in order], rows, "lrrr")
    rows = []
    for i, band in enumerate(groups["todas"]["por_faixa"]):
        rows.append([band["faixa"]] + [cell(diag["fases"][p]["por_faixa"][i]) for p in ("1", "2", "3")])
    t2 = md_table(["Idade do deal na foto"] + [_PHASE_LABELS[p] for p in ("1", "2", "3")], rows, "lrrr")
    end = _list_pt([fmt_date(d) for d in groups["fim_de_trimestre"]["fotos"]])
    mid = _list_pt([fmt_date(d) for d in groups["meio_de_trimestre"]["fotos"]])
    return (
        f"Taxa de ganho em {fmt_int(bt['config']['horizon_days'])} dias por idade do deal na foto, com o número de casos entre parênteses. "
        f"Fotos de treino de hoje ({fmt_date(diag['as_of'])}): fim de trimestre = {end}; meio de trimestre = {mid}.\n\n{t1}\n\n"
        f"Mesmas fotos, uma coluna por mês do trimestre:\n\n{t2}"
    )


@_scoring_block("scoring-criterio")
def _sc_criterio(bt: dict) -> str:
    crit = bt["criterion"]
    rows = []
    for r in crit["per_cut"]:
        others = [r["valor"], r["recencia"], r["aleatorio_media"], r["aleatorio_p95"]]
        margin = r["score"] - max(others)
        rows.append([
            fmt_date(r["cut"]), _pct0(r["score"]), _pct0(r["valor"]), _pct0(r["recencia"]), _pct0(r["aleatorio_media"]),
            _pct0(r["aleatorio_p95"]), fmt_pp(margin), _yes(r["passa"]),
        ])
    table = md_table(
        ["Corte", "Score v2", "Valor", "Recência", "Aleatório (média)", "Aleatório (p95)", "Margem sobre o melhor baseline", "Vence os 4?"],
        rows,
    )
    verdict = "**PASSOU**" if crit["passed"] else "**FALHOU**"
    lines = [table, "", f"Receita capturada no top 20%, curva v2. Empate é diferença de até {fmt_dec(crit['tie_tol'], 2)} e não vence. Resultado: {verdict}."]
    names = {"v1": "curva v1 (platô + queda, todas as fotos)", "v2": "curva v2 (faixas isotônicas, fotos da mesma fase do trimestre)"}
    for kind, run in crit["runs"].items():
        lines.append(f"- {names[kind]}: {'passou' if run['passed'] else 'falhou'}; receita média do score nos cortes: {_pct0(run['media_receita_top20_score'])}.")
    return "\n".join(lines)


@_scoring_block("scoring-backtest")
def _sc_backtest(bt: dict) -> str:
    labels = _labels(bt)
    rows = []
    for cut, old in zip(bt["cuts"], bt["cuts_v1"]):
        metodos = {**cut["metodos"], "score_v1": old["metodos"]["score"]}
        best = {k: max(metodos[m][k] for m in _BEST_OF) for k in ("auc", "ganhos_top20", "receita_top20")}
        for method in _METHOD_ORDER:
            m = metodos[method]
            cells = []
            for key, fmt in (("auc", lambda v: fmt_dec(v, 2)), ("ganhos_top20", _pct0), ("receita_top20", _pct0)):
                text = fmt(m[key])
                if method == "aleatorio":
                    text += f" ({fmt(m['p5'][key])} a {fmt(m['p95'][key])})"
                if method in _BEST_OF and m[key] == best[key]:
                    text = f"**{text}**"
                cells.append(text)
            rows.append([fmt_date(cut["cut"]), labels[method], *cells])
    table = md_table(["Corte", "Método", "AUC", "Ganhos capturados no top 20%", "Receita capturada no top 20%"], rows, "llrrr")
    return table + "\n\nEm negrito, o melhor entre score v2, score v1, valor, recência e aleatório. No aleatório, entre parênteses, o intervalo de p5 a p95 de 200 sorteios."


@_scoring_block("scoring-media")
def _sc_media(bt: dict) -> str:
    labels = _labels(bt)
    media = {**bt["media_cortes"]["metodos"], "score_v1": bt["media_cortes_v1"]["metodos"]["score"]}
    rows = [
        [labels[m], fmt_dec(media[m]["auc"], 2), _pct0(media[m]["ganhos_top20"]), _pct0(media[m]["receita_top20"])]
        for m in _METHOD_ORDER
    ]
    table = md_table(["Método", "AUC", "Ganhos capturados no top 20%", "Receita capturada no top 20%"], rows)
    brier, old = bt["media_cortes"]["brier"], bt["media_cortes_v1"]["brier"]
    note = (
        f"Média simples dos {fmt_int(bt['headline']['n_cortes'])} cortes. Brier da chance v2: {fmt_dec(brier['modelo'], 3)} (v1: {fmt_dec(old['modelo'], 3)}) contra "
        f"{fmt_dec(brier['constante'], 3)} da taxa média de treino (log-loss {fmt_dec(brier['log_loss_modelo'], 3)}, v1: {fmt_dec(old['log_loss_modelo'], 3)}, "
        f"contra {fmt_dec(brier['log_loss_constante'], 3)}), sobre ganhos em 90 dias."
    )
    return table + "\n\n" + note


@_scoring_block("scoring-foque-ordem")
def _sc_foque_ordem(bt: dict) -> str:
    intra = bt["intra_foque"]
    labels = intra["labels"]
    methods = ("score_v2", "score_v1", "valor", "recencia", "aleatorio")
    contest = methods[:4]

    def table(key: str, fmt) -> str:
        rows = []
        for c in intra["por_corte"]:
            best = max(c["metodos"][m][key] for m in contest)
            cells = [f"**{fmt(c['metodos'][m][key])}**" if m in contest and c["metodos"][m][key] == best else fmt(c["metodos"][m][key]) for m in methods]
            rows.append([fmt_date(c["cut"]), fmt_int(c["n"]), *cells])
        best = max(intra["media"][m][key] for m in contest)
        cells = [f"**{fmt(intra['media'][m][key])}**" if m in contest and intra["media"][m][key] == best else fmt(intra["media"][m][key]) for m in methods]
        rows.append([f"**Média dos {fmt_int(len(intra['por_corte']))} cortes**", "—", *cells])
        return md_table(["Corte", "Deals"] + [labels[m] for m in methods], rows, "lr" + "r" * len(methods))

    brows = []
    for c in intra["por_corte"]:
        b = c["bootstrap"]
        cell = lambda d: f"{fmt_pp(d['diff'])} (IC {fmt_pp(d['ci_low'])} a {fmt_pp(d['ci_high'])})"  # noqa: E731
        brows.append([fmt_date(c["cut"]), cell(b["v2_menos_v1"]), cell(b["v2_menos_valor"])])
    t3 = md_table(["Corte", "Score v2 menos score v1", "Score v2 menos valor"], brows, "lrr")
    return (
        f"População: {intra['regra'][0].lower() + intra['regra'][1:]} Desfecho: ganho até 31/12/2017.\n\n"
        f"**AUC**\n\n{table('auc', lambda v: fmt_dec(v, 2))}\n\n"
        f"**Receita ganha capturada pelo top 20%**\n\n{table('receita_top20', _pct0)}\n\n"
        f"**Diferença na receita capturada, com IC por bootstrap (pp)**\n\n{t3}\n\n"
        "Em negrito, o melhor entre score v2, score v1, valor e recência (o aleatório é só referência)."
    )


@_scoring_block("scoring-categorias")
def _sc_categorias(bt: dict) -> str:
    rows = []
    for cut in bt["cuts"]:
        for cat in _LISTS:
            c = cut["categorias"][cat]
            rows.append([
                fmt_date(cut["cut"]), cat, fmt_int(c["n"]), _pct0(c["pct_ganhos"]), _usd(c["receita_ganha"]),
                _pct0(c["pct_receita"]), _usd(c["valor_tabela"]), _usd(c["valor_esperado"]),
            ])
    return md_table(
        ["Corte", "Lista", "Deals", "Ganhos até 31/12/2017", "Receita ganha", "% da receita", "Valor de tabela", "Valor esperado"],
        rows, "llrrrrrr",
    )


@_scoring_block("scoring-calibracao")
def _sc_calibracao(bt: dict) -> str:
    brows = [
        [fmt_date(c["cut"]), fmt_int(c["brier"]["n"]), fmt_dec(c["brier"]["modelo"], 3), fmt_dec(old["brier"]["modelo"], 3),
         fmt_dec(c["brier"]["constante"], 3), fmt_dec(c["brier"]["log_loss_modelo"], 3), fmt_dec(old["brier"]["log_loss_modelo"], 3),
         fmt_dec(c["brier"]["log_loss_constante"], 3)]
        for c, old in zip(bt["cuts"], bt["cuts_v1"])
    ]
    t1 = md_table(
        ["Corte", "Deals", "Brier da v2", "Brier da v1", "Brier da constante", "Log-loss da v2", "Log-loss da v1", "Log-loss da constante"],
        brows,
    )
    crows = []
    for c, old in zip(bt["cuts"], bt["cuts_v1"]):
        for band, band_old in zip(c["calibracao"], old["calibracao"]):
            if band["n"]:
                crows.append([
                    fmt_date(c["cut"]), band["faixa"], fmt_int(band["n"]), _pct0(band["p_modelo"]), _pct0(band_old["p_modelo"]),
                    _pct0(band["taxa_observada_90d"]),
                ])
    t2 = md_table(["Corte", "Idade", "Deals", "Chance média da v2", "Chance média da v1", "Ganhos em 90 dias (observado)"], crows, "llrrrr")
    return t1 + "\n\n" + t2


@_scoring_block("scoring-bootstrap")
def _sc_bootstrap(bt: dict) -> str:
    def cell(d):
        return f"{fmt_pp(d['diff'])} (IC {fmt_pp(d['ci_low'])} a {fmt_pp(d['ci_high'])})"

    rows = [
        [fmt_date(c["cut"]), cell(c["bootstrap"]["score_menos_valor"]), cell(c["bootstrap"]["score_menos_recencia"])]
        for c in bt["cuts"]
    ]
    n = fmt_int(bt["config"]["bootstrap_reps"])
    return md_table(["Corte", "Score v2 menos valor", "Score v2 menos recência"], rows, "lrr") + (
        f"\n\nDiferença na receita capturada no top 20%, em pontos percentuais; IC de 2,5% a 97,5% por {n} reamostragens dos deals do corte (semente 0)."
    )


@_scoring_block("scoring-foque-idade")
def _sc_foque_idade(bt: dict) -> str:
    rows = []
    for c in bt["cuts"]:
        for band in c["foque_por_idade"]["faixas"]:
            rows.append([
                fmt_date(c["cut"]), band["faixa"], fmt_int(band["n"]), _pct0(band["p_modelo"]),
                _pct0(band["taxa_ganho_90d"]),
            ])
    t1 = md_table(["Corte", "Idade (dentro do Foque do corte)", "Deals", "Chance do modelo (v2)", "Ganhos em 90 dias (observado)"], rows, "llrrr")
    hoje = bt["hoje"]["foque_por_idade"]
    total = bt["hoje"]["categorias"]["Foque"]["n"]
    parts = ", ".join(f"{b['faixa']}: {fmt_int(b['n'])}" for b in hoje)
    return f"{t1}\n\nFoque de hoje ({fmt_int(total)} deals) por idade: {parts}."


@_scoring_block("scoring-correcao")
def _sc_correcao(bt: dict) -> str:
    """Antes e depois da correção, em números (curva v1 contra v2)."""
    v1, v2 = bt["hoje_v1"], bt["hoje"]
    m1, m2 = v1["modelo"], v2["modelo"]
    p2 = {pt["idade"]: pt["p"] for pt in m2["curva_pontos"]}
    ages = config.EXPLAIN_CURVE_AGES
    ages_txt = ", ".join(f"{fmt_pct(p2[a], 0)} com {fmt_int(a)} dias" for a in ages)
    media1, media2 = bt["media_cortes_v1"]["metodos"]["score"], bt["media_cortes"]["metodos"]["score"]
    intra = bt["intra_foque"]["media"]
    lines = [
        f"- **Chance de hoje.** v1: {fmt_pct(m1['p_fresh'], 0)} de 0 a {fmt_int(m1['knot_days'])} dias, igual para todos (o platô). "
        f"v2: {fmt_pct(m2['p_fresh'], 0)} para um deal novo e {ages_txt}.",
        f"- **Listas de hoje.** Foque: {fmt_int(v1['categorias']['Foque']['n'])} → {fmt_int(v2['categorias']['Foque']['n'])} deals. "
        f"Reative: {fmt_int(v1['categorias']['Reative']['n'])} → {fmt_int(v2['categorias']['Reative']['n'])}. "
        f"Limpe: {fmt_int(v1['categorias']['Limpe']['n'])} → {fmt_int(v2['categorias']['Limpe']['n'])} "
        f"({fmt_usd(v1['categorias']['Limpe']['valor_tabela'])} → {fmt_usd(v2['categorias']['Limpe']['valor_tabela'])} de tabela).",
        f"- **Backtest principal (receita no top 20%, média dos cortes).** v1: {_pct0(media1['receita_top20'])}; v2: {_pct0(media2['receita_top20'])}. "
        f"AUC: {fmt_dec(media1['auc'], 2)} → {fmt_dec(media2['auc'], 2)}.",
        f"- **Ordem dentro do Foque (deals de até {fmt_int(bt['intra_foque']['idade_max'])} dias).** Receita no top 20%: v1 {_pct0(intra['score_v1']['receita_top20'])}, "
        f"v2 {_pct0(intra['score_v2']['receita_top20'])}, valor {_pct0(intra['valor']['receita_top20'])}; AUC: v1 {fmt_dec(intra['score_v1']['auc'], 2)}, "
        f"v2 {fmt_dec(intra['score_v2']['auc'], 2)}, valor {fmt_dec(intra['valor']['auc'], 2)}.",
    ]
    return "\n".join(lines)


def _delta_cell(r: dict) -> str:
    return f"{fmt_pp(r['diff'])}"


@_scoring_block("scoring-sensibilidade")
def _sc_sensibilidade(bt: dict) -> str:
    sens = bt["sensibilidade_2017-02-28"]
    rows = []
    for r, main in zip(sens["por_corte"], bt["cuts"]):
        rows.append([
            fmt_date(r["cut"]), fmt_int(r["modelo"]["knot_days"]), fmt_int(main["modelo"]["knot_days"]),
            fmt_int(r["modelo"]["train_rows"]), fmt_dec(r["score"]["auc"], 2), _pct0(r["score"]["ganhos_top20"]),
            _pct0(r["score"]["receita_top20"]), fmt_pp(r["delta_receita_top20_vs_principal"]),
        ])
    t1 = md_table(
        ["Corte", "Fim do Foque (foto de 28/02)", "Fim do Foque (principal)", "Linhas de treino", "AUC", "Ganhos no top 20%", "Receita no top 20%", "Receita vs. principal"],
        rows,
    )
    crit = sens["criterio"]
    t1 += f"\n\nCom a primeira foto em 28/02/2017 o critério {'passaria' if crit['passed'] else 'falharia'}; receita média do score v2: {_pct0(sens['media']['receita_top20'])}."
    pseudo = bt["sensibilidade_pseudo_contagem"]
    prows = []
    for r, main in zip(pseudo["por_corte"], bt["cuts"]):
        prows.append([
            fmt_date(r["cut"]), fmt_int(r["modelo"]["knot_days"]), fmt_int(main["modelo"]["knot_days"]),
            _pct0(r["modelo"]["p_cauda"]), _pct0(main["modelo"]["p_cauda"]), fmt_dec(r["score"]["auc"], 2), fmt_dec(main["metodos"]["score"]["auc"], 2),
            _pct0(r["score"]["receita_top20"]), fmt_pp(r["delta_receita_top20_vs_principal"]),
        ])
    t1b = md_table(
        ["Corte", "Fim do Foque (com pseudo-contagem)", "Fim do Foque (principal)", "Chance aos 730 dias (com pseudo-contagem)",
         "Chance aos 730 dias (principal)", "AUC (com pseudo-contagem)", "AUC (principal)", "Receita no top 20% (com pseudo-contagem)", "Receita vs. principal"],
        prows,
    )
    t1b += (
        f"\n\nCom {fmt_int(pseudo['pseudo_count'])} deals de pseudo-contagem por faixa o critério {'passaria' if pseudo['criterio']['passed'] else 'falharia'}; "
        f"receita média do score v2: {_pct0(pseudo['media']['receita_top20'])}."
    )
    rrows = []
    for c in bt["cuts"]:
        r = c["resolvidos"]
        m = r["metodos"]
        rrows.append([
            fmt_date(c["cut"]), fmt_int(r["n_abertos_em_t"]), fmt_int(r["n_resolvidos"]), fmt_int(r["n_abertos_em_31_12"]),
            fmt_int(r["n_abertos_em_31_12_que_ainda_podem_fechar"]),
            f"{_pct0(m['score']['receita_top20'])} / {_pct0(m['valor']['receita_top20'])} / {_pct0(m['recencia']['receita_top20'])} / {_pct0(m['aleatorio']['receita_top20'])}",
            f"{fmt_dec(m['score']['auc'], 2)} / {fmt_dec(m['valor']['auc'], 2)} / {fmt_dec(m['recencia']['auc'], 2)}",
        ])
    t2 = md_table(
        ["Corte", "Abertos no corte", "Resolvidos até 31/12", "Ainda abertos em 31/12", "Desses, com idade em 31/12 dentro do maior ciclo ganho até o corte",
         "Receita no top 20%: score v2 / valor / recência / aleatório", "AUC: score v2 / valor / recência"],
        rrows,
    )
    return (
        f"**Primeira foto de treino em 28/02/2017**\n\n{t1}\n\n**Pseudo-contagem do ajuste único na curva v2**\n\n{t1b}\n\n"
        f"**Só deals resolvidos (fechados até 31/12/2017)**\n\n{t2}"
    )


@_scoring_block("scoring-auditoria")
def _sc_auditoria(bt: dict) -> str:
    aud = bt["auditoria"]
    vrows = [
        [fmt_date(v["cut"]), "VAZADO", fmt_int(v["knot_days"]), fmt_dec(v["score_vazado"]["auc"], 2), _pct0(v["score_vazado"]["receita_top20"]),
         fmt_dec(v["score_honesto"]["auc"], 2), _pct0(v["score_honesto"]["receita_top20"]), fmt_pp(v["delta_receita_top20"])]
        for v in aud["vazado"]
    ]
    t1 = md_table(
        ["Corte", "Rótulo", "Fim do Foque do modelo vazado", "AUC vazado", "Receita vazada", "AUC honesto", "Receita honesta", "Receita: vazado menos honesto"],
        vrows, "llrrrrrr",
    )
    crows = [
        [fmt_date(a["cut"]), fmt_int(a["n_com_conta"]), fmt_int(a["n_sem_conta"]), fmt_dec(a["auc_has_account"], 2),
         _pct0(a["taxa_ganho_com_conta"]), _pct0(a["taxa_ganho_sem_conta"]), fmt_int(a["ganhos_sem_conta"])]
        for a in aud["has_account"]
    ]
    t2 = md_table(
        ["Corte", "Com conta", "Sem conta", "AUC de `has_account` sozinho", "Ganhos depois (com conta)", "Ganhos depois (sem conta)", "Ganhos entre os sem conta"],
        crows,
    )
    return (
        "**Modelo ajustado com o futuro (VAZADO; nunca é resultado)**\n\n" + t1 +
        "\n\n**`has_account` sozinho (proibido como variável)**\n\n" + t2
    )


@_scoring_block("scoring-atributos")
def _sc_atributos(bt: dict) -> str:
    cuts = [fmt_date(c["cut"]) for c in bt["cuts"]]
    rows_ll, rows_rev = [], []
    for a in bt["atributos"]:
        first = a["por_corte"][0]
        head = [a["atributo"], a["subconjunto"], fmt_int(first["n_niveis"])]
        rows_ll.append(head + [fmt_dec(r["delta_log_loss"], 4) for r in a["por_corte"]] + [_yes(a["melhora_log_loss_em_todos"])])
        rows_rev.append(head + [fmt_pp(r["delta_receita_top20"]) for r in a["por_corte"]] + [_yes(a["nao_piora_receita_em_nenhum"]), _yes(a["entra"])])
    t1 = md_table(["Atributo", "Subconjunto", "Níveis"] + [f"Δ log-loss {c}" for c in cuts] + ["Melhora em todos?"], rows_ll, "llr" + "r" * (len(cuts) + 1))
    t2 = md_table(["Atributo", "Subconjunto", "Níveis"] + [f"Δ receita top 20% {c}" for c in cuts] + ["Não piora em nenhum?", "Entra?"], rows_rev, "llr" + "r" * (len(cuts) + 2))
    rows_tr = [
        [a["atributo"], a["subconjunto"]] + [fmt_dec(r["delta_log_loss_treino"], 4) for r in a["por_corte"]]
        for a in bt["atributos"]
    ]
    t3 = md_table(["Atributo", "Subconjunto"] + [f"Δ log-loss no treino {c}" for c in cuts], rows_tr, "ll" + "r" * len(cuts))
    return (
        "Δ log-loss negativo é melhora (log-loss de 90 dias, contra a curva só de idade no mesmo subconjunto). Teste feito sobre a curva v1 (joelho fixo), antes da correção.\n\n"
        + t1 + "\n\n" + t2
        + "\n\nDiagnóstico, que não decide: o mesmo Δ log-loss medido dentro da amostra de treino.\n\n" + t3
    )


@_scoring_block("scoring-modelos")
def _sc_modelos(bt: dict) -> str:
    def row(label, m):
        return [
            label, fmt_int(m["fase"]), _pct0(m["p_fresh"]), fmt_int(m["knot_days"]), fmt_int(m["limpe_after_days"]), _rule_label(m),
            fmt_int(m["n_snapshots"]), fmt_int(m["train_rows"]), _pct0(m["base_rate"]),
        ]

    rows = [row(fmt_date(c["cut"]), c["modelo"]) for c in bt["cuts"]]
    rows.append(row(f"{fmt_date(bt['hoje']['as_of'])} (hoje)", bt["hoje"]["modelo"]))
    table = md_table(
        ["Modelo ajustado até", "Mês do trimestre", "Chance de deal novo", "Fim do Foque (dias)", "Fim do Reative (dias)", "O Limpe começa por",
         "Fotos", "Linhas de treino", "Taxa base de treino"],
        rows, "lrrrrlrrr",
    )
    fallbacks = sum(1 for c in bt["cuts"] if c["modelo"]["fallback"]) + int(bt["hoje"]["modelo"]["fallback"])
    note = (
        f"Fim do Foque = última idade em que a chance ainda é pelo menos {fmt_pct(config.FOQUE_HALF_FRACTION, 0)} da de um deal novo. "
        f"Fim do Reative = o que chegar primeiro: chance abaixo de {fmt_pct(config.LIMPE_MIN_CHANCE, 0)} ou idade acima do maior ciclo já ganho até a data do modelo "
        f"({', '.join(fmt_int(c['modelo']['max_won_cycle_days']) for c in bt['cuts'])} dias nos quatro cortes e {fmt_int(bt['hoje']['modelo']['max_won_cycle_days'])} hoje). "
        f"Casos em que a fase do trimestre não tinha foto elegível e o ajuste usou todas as fotos: {fmt_int(fallbacks)}."
    )
    return table + "\n\n" + note


@_scoring_block("scoring-curva")
def _sc_curva(bt: dict) -> str:
    ages = config.CURVE_TABLE_AGES

    def row(label, m):
        by_age = {pt["idade"]: pt["p"] for pt in m["curva_pontos"]}
        return [label] + [_pct0(by_age[a]) for a in ages]

    rows = [row(fmt_date(c["cut"]), c["modelo"]) for c in bt["cuts"]]
    rows.append(row(f"{fmt_date(bt['hoje']['as_of'])} (hoje)", bt["hoje"]["modelo"]))
    return md_table(["Modelo ajustado até"] + [f"{fmt_int(a)} dias" for a in ages], rows)


@_scoring_block("scoring-modelos-v1")
def _sc_modelos_v1(bt: dict) -> str:
    def row(label, m):
        return [
            label, fmt_int(m["knot_days"]), _pct0(m["p_fresh"]), fmt_dec(m["slope_per_30d"], 2), fmt_dec(m["halving_days"], 1),
            fmt_int(m["limpe_after_days"]), fmt_int(m["n_snapshots"]), fmt_int(m["train_rows"]), _pct0(m["base_rate"]),
        ]

    rows = [row(fmt_date(c["cut"]), c["modelo"]) for c in bt["cuts_v1"]]
    rows.append(row(f"{fmt_date(bt['hoje_v1']['as_of'])} (hoje)", bt["hoje_v1"]["modelo"]))
    return md_table(
        ["Modelo ajustado até", "Joelho (dias)", "Chance de deal novo", "Inclinação por 30 dias", "Meia-vida depois do joelho (dias)",
         "Limite de Limpe (dias)", "Fotos", "Linhas de treino", "Taxa base de treino"],
        rows,
    )


def _today_rules(m: dict) -> dict:
    return {
        "Foque": f"idade até {fmt_int(m['knot_days'])} dias",
        "Reative": f"{fmt_int(m['knot_days'] + 1)} a {fmt_int(m['limpe_after_days'])} dias",
        "Limpe": f"mais de {fmt_int(m['limpe_after_days'])} dias",
        "Qualifique": "Prospecting (sem data)",
    }


@_scoring_block("scoring-hoje")
def _sc_hoje(bt: dict) -> str:
    hoje = bt["hoje"]
    m = hoje["modelo"]
    desc = _today_rules(m)
    rows = [
        [cat, desc[cat], fmt_int(hoje["categorias"][cat]["n"]), _usd(hoje["categorias"][cat]["valor_tabela"]), _usd(hoje["categorias"][cat]["valor_esperado"])]
        for cat in config.CATEGORIES
    ]
    t1 = md_table(["Lista", "Regra", "Deals", "Valor de tabela", "Valor esperado"], rows, "llrrr")
    d = hoje["limpe_detalhe"]
    t2 = md_table(
        ["Limpe de hoje", "Deals", "Valor de tabela"],
        [
            [f"Acima do maior ciclo já ganho ({fmt_int(m['max_won_cycle_days'])} dias)", fmt_int(d["acima_do_maior_ciclo"]["n"]), _usd(d["acima_do_maior_ciclo"]["valor_tabela"])],
            ["Só pela chance (idade até o maior ciclo, chance abaixo do mínimo)", fmt_int(d["so_pela_chance"]["n"]), _usd(d["so_pela_chance"]["valor_tabela"])],
        ],
        "lrr",
    )
    f = hoje["faixas_fixas_do_briefing"]
    t3 = md_table(
        ["Lista", "Faixas fixas do briefing (90 e 138 dias)", "Limiares aprendidos pela curva v2"],
        [
            ["Foque", fmt_int(f["ate_90"]), fmt_int(hoje["categorias"]["Foque"]["n"])],
            ["Reative", fmt_int(f["de_91_a_138"]), fmt_int(hoje["categorias"]["Reative"]["n"])],
            ["Limpe", fmt_int(f["acima_de_138"]), fmt_int(hoje["categorias"]["Limpe"]["n"])],
        ],
    )
    return t1 + "\n\n" + t2 + "\n\n" + t3


@_scoring_block("scoring-hoje-antes-depois")
def _sc_hoje_antes_depois(bt: dict) -> str:
    v1, v2 = bt["hoje_v1"], bt["hoje"]
    r1, r2 = _today_rules(v1["modelo"]), _today_rules(v2["modelo"])
    rows = []
    for cat in config.CATEGORIES:
        a, b = v1["categorias"][cat], v2["categorias"][cat]
        rows.append([cat, r1[cat], fmt_int(a["n"]), _usd(a["valor_tabela"]), r2[cat], fmt_int(b["n"]), _usd(b["valor_tabela"])])
    return md_table(
        ["Lista", "Regra v1", "Deals (v1)", "Valor de tabela (v1)", "Regra v2", "Deals (v2)", "Valor de tabela (v2)"], rows, "llrrlrr",
    )


# =============================================================================================
# Renderizadores do MODEL_CARD.md e do README.md (bloco 5)
# =============================================================================================
def _short_date(iso: str) -> str:
    """'2017-06-30' -> '30/06'."""
    return fmt_date(iso)[:5]


def _list_pt(items: list[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b e c'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " e " + items[-1]


def _worst_cut(bt: dict) -> dict:
    """O corte de menor margem do score sobre o melhor baseline (o 'pior corte' do critério)."""
    def margin(r: dict) -> float:
        return r["score"] - max(r["valor"], r["recencia"], r["aleatorio_media"], r["aleatorio_p95"])

    worst = min(bt["criterion"]["per_cut"], key=margin)
    return next(c for c in bt["cuts"] if c["cut"] == worst["cut"])


def _perf_row(label: str, metodos: dict, v1_score: dict) -> list:
    return [
        label, _pct0(metodos["score"]["receita_top20"]), _pct0(v1_score["receita_top20"]), _pct0(metodos["valor"]["receita_top20"]),
        _pct0(metodos["recencia"]["receita_top20"]), _pct0(metodos["aleatorio"]["receita_top20"]),
        fmt_dec(metodos["score"]["auc"], 2), fmt_dec(metodos["recencia"]["auc"], 2),
    ]


_PERF_HEADERS = ["", "Receita no top 20%: score v2", "score v1", "valor", "recência", "aleatório", "AUC do score v2", "AUC da recência"]


@_scoring_block("mc-desempenho")
def _mc_desempenho(bt: dict) -> str:
    worst = _worst_cut(bt)
    rows = [
        _perf_row(f"Média dos {fmt_int(bt['headline']['n_cortes'])} cortes", bt["media_cortes"]["metodos"], bt["media_cortes_v1"]["metodos"]["score"]),
        _perf_row(f"Pior corte ({fmt_date(worst['cut'])})", worst["metodos"], _v1_of(bt, worst["cut"])["metodos"]["score"]),
    ]
    crit = bt["criterion"]
    verdict = "PASSOU" if crit["passed"] else "FALHOU"
    old = "PASSOU" if crit["v1_passed"] else "FALHOU"
    note = (
        f"Pior corte = o de menor margem do score v2 sobre o melhor baseline. Critério pré-registrado: **{verdict}** para a v2 e **{old}** para a v1. "
        "A v2 é uma mudança pós-backtest, pedida pelo Rafael depois de revisar a ferramenta."
    )
    return md_table(_PERF_HEADERS, rows) + "\n\n" + note


@_scoring_block("mc-ordem-foque")
def _mc_ordem_foque(bt: dict) -> str:
    intra = bt["intra_foque"]
    media = intra["media"]
    labels = intra["labels"]
    methods = ("score_v2", "score_v1", "valor", "recencia", "aleatorio")
    rows = [[labels[m], fmt_dec(media[m]["auc"], 2), _pct0(media[m]["receita_top20"])] for m in methods]
    return md_table(["Método (deals de até 90 dias, média dos cortes)", "AUC", "Receita no top 20%"], rows)


@_scoring_block("mc-recalibracao")
def _mc_recalibracao(bt: dict) -> str:
    x = config.RECALIBRATION_SHIFT_PP
    total = alarms = 0
    for cut in bt["cuts"]:
        for band in cut["calibracao"]:
            if band["n"] >= config.RECALIBRATION_MIN_BAND_N:
                total += 1
                alarms += abs(band["p_modelo"] - band["taxa_observada_90d"]) * 100 > x
    return (
        f"X = {fmt_int(x)} pp (`config.RECALIBRATION_SHIFT_PP`). Teste de bom senso no backtest: entre as "
        f"{fmt_int(total)} faixas de idade com pelo menos {fmt_int(config.RECALIBRATION_MIN_BAND_N)} deals "
        f"(corte x faixa), {fmt_int(alarms)} teriam acendido o alerta, isto é, a chance do modelo ficou a mais de "
        f"{fmt_int(x)} pp da taxa de ganho em 90 dias observada."
    )


@_scoring_block("readme-backtest")
def _readme_backtest(bt: dict) -> str:
    rows = [_perf_row(f"**Média dos {fmt_int(bt['headline']['n_cortes'])} cortes**", bt["media_cortes"]["metodos"], bt["media_cortes_v1"]["metodos"]["score"])]
    rows += [_perf_row(fmt_date(c["cut"]), c["metodos"], old["metodos"]["score"]) for c, old in zip(bt["cuts"], bt["cuts_v1"])]
    headers = ["Corte"] + _PERF_HEADERS[1:]
    note = (
        "Receita capturada pelos 20% de deals no topo da ordenação, como fração da receita que foi de fato ganha depois. "
        "Aleatório = média de 200 sorteios. Cada corte usa só o que o CRM sabia naquele dia."
    )
    return md_table(headers, rows) + "\n\n" + note


@_scoring_block("readme-hoje")
def _readme_hoje(bt: dict) -> str:
    hoje = bt["hoje"]
    rule = _today_rules(hoje["modelo"])
    action = {"Foque": "avançar", "Reative": "retomar o contato", "Limpe": "confirmar e encerrar ou atualizar", "Qualifique": "qualificar"}
    rows = [
        [cat, rule[cat].replace("idade até", "até").replace("mais de", "mais de"), action[cat], fmt_int(hoje["categorias"][cat]["n"]), _usd(hoje["categorias"][cat]["valor_tabela"])]
        for cat in config.CATEGORIES
    ]
    return md_table(["Lista", "Idade do deal", "Ação", "Deals", "Valor de tabela"], rows, "lllrr")


@_scoring_block("readme-achados")
def _readme_achados(bt: dict) -> str:
    crit = bt["criterion"]
    head = bt["headline"]
    cuts = bt["cuts"]
    media2, media1 = bt["media_cortes"]["metodos"], bt["media_cortes_v1"]["metodos"]
    hoje, antes = bt["hoje"], bt["hoje_v1"]
    p2 = {pt["idade"]: pt["p"] for pt in hoje["modelo"]["curva_pontos"]}
    intra = bt["intra_foque"]["media"]
    lines = []
    lines.append(
        "- **Critério pré-registrado: {v} para a curva v2 e {o} para a v1.** O score v2 vence valor, recência e o sorteio nos {n} cortes. "
        "A v2 é uma mudança pós-backtest, pedida por mim depois de usar a ferramenta como vendedor."
        .format(v="PASSOU" if crit["passed"] else "FALHOU", o="PASSOU" if crit["v1_passed"] else "FALHOU", n=fmt_int(head["n_cortes"]))
    )
    lines.append(
        f"- **Receita média no top 20%:** score v2 {_pct0(head['receita_score'])}, score v1 {_pct0(media1['score']['receita_top20'])}, valor {_pct0(head['receita_valor'])}, "
        f"recência {_pct0(head['receita_recencia'])}, aleatório {_pct0(media2['aleatorio']['receita_top20'])}."
    )
    lines.append(
        f"- **A curva v1 era plana de 0 a {fmt_int(antes['modelo']['knot_days'])} dias; a v2 cai desde o primeiro dia.** Hoje, a chance de um deal novo é "
        f"{_pct0(p2[0])}, com 30 dias {_pct0(p2[30])}, com 60 dias {_pct0(p2[60])} e com 90 dias {_pct0(p2[90])}. O Foque de hoje passou de "
        f"{fmt_int(antes['categorias']['Foque']['n'])} para {fmt_int(hoje['categorias']['Foque']['n'])} deals."
    )
    lines.append(
        f"- **Dentro do Foque (deals de até {fmt_int(bt['intra_foque']['idade_max'])} dias) a ordem melhorou pouco:** receita no top 20% de {_pct0(intra['score_v2']['receita_top20'])} "
        f"(v1 {_pct0(intra['score_v1']['receita_top20'])}, valor {_pct0(intra['valor']['receita_top20'])}) e AUC de {fmt_dec(intra['score_v2']['auc'], 2)}, perto de um sorteio. "
        "O ganho está no corte de fim de trimestre."
    )
    rec_wins = [c["cut"] for c in cuts if c["metodos"]["recencia"]["auc"] > c["metodos"]["score"]["auc"]]
    best = max(cuts, key=lambda c: c["metodos"]["recencia"]["auc"] - c["metodos"]["score"]["auc"])
    lines.append(
        f"- **A recência ganha em AUC** em {fmt_int(len(rec_wins))} dos {fmt_int(head['n_cortes'])} cortes "
        f"({_list_pt([_short_date(d) for d in rec_wins])}); a maior folga é em {fmt_date(best['cut'])}, com "
        f"{fmt_dec(best['metodos']['recencia']['auc'], 2)} contra {fmt_dec(best['metodos']['score']['auc'], 2)} do score v2."
    )
    res = [(c["resolvidos"]["metodos"]["score"]["receita_top20"], c["resolvidos"]["metodos"]["valor"]["receita_top20"]) for c in cuts]
    mean_s = sum(r[0] for r in res) / len(res)
    mean_v = sum(r[1] for r in res) / len(res)
    gap = max(abs(r[0] - r[1]) for r in res)
    lines.append(
        f"- **Entre os deals já resolvidos o score empata com o valor:** receita média no top 20% de {_pct0(mean_s)} "
        f"contra {_pct0(mean_v)}, e a maior diferença em um corte é de {fmt_dec(gap * 100, 1)} pp. A vantagem do backtest completo "
        f"vem de tirar do topo os deals parados."
    )
    return "\n".join(lines)


# =============================================================================================
# Conferência dos números da prosa
# =============================================================================================
_NUM = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"  # número PT-BR: 1.291 | 3,2 | 1.234,5 | 138
_TOKEN_RE = re.compile(
    rf"(?P<usd>US\$\s?(?P<usd_num>{_NUM})(?:\s?(?P<unit>mil|mi)\b)?)"
    rf"|(?P<pp>(?<![\w.,])(?P<pp_num>{_NUM})\s?(?:pp\b|pontos percentuais\b))"
    rf"|(?P<pct>(?<![\w.,])(?P<pct_num>{_NUM})\s?%)"
    rf"|(?P<dec>(?<![\w.,])(?:\d{{1,3}}(?:\.\d{{3}})+,\d+|\d+,\d+)(?!\w))"
    rf"|(?P<int>(?<![\w.,])(?:\d{{1,3}}(?:\.\d{{3}})+|\d{{3,}})(?!\w))"
)
_UNIT_SCALE = {None: 1.0, "mil": 1e3, "mi": 1e6}
_MONTH_ABBR = "jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez"
_STRIP_PATTERNS = [  # (padrão, flags): trechos que não são "números do texto"
    (r"```.*?```", re.S),  # blocos de código
    (r"<!--.*?-->", re.S),  # comentários HTML
    (r"`[^`\n]*`", 0),  # código inline
    (r"\]\([^)\n]*\)", 0),  # destino de link
    (r"https?://\S+", 0),  # URL solta
    (r"\b\d{1,2}/\d{1,2}/\d{4}\b", 0),  # dd/mm/aaaa
    (r"\b\d{4}-\d{2}-\d{2}\b", 0),  # aaaa-mm-dd
    (rf"\b(?:{_MONTH_ABBR})/\d{{4}}\b", re.I),  # mmm/aaaa
    (r"\b\d{1,2}/\d{4}\b", 0),  # mm/aaaa
    (r"(?<![\d.,])20(?:1[6-9]|2[0-6])(?!\d)", 0),  # anos 2016 a 2026
]
_LINE_PREFIX_RE = re.compile(r"^(?P<lead>\s*(?:#{1,6}\s+)?)(?P<num>\d+(?:\.\d+)*[.)])(?=\s)", re.M)


@dataclass(frozen=True)
class NumberToken:
    text: str  # como está no documento
    kind: str  # 'usd' | 'pct' | 'dec' | 'int'
    value: float  # valor exibido
    decimals: int  # casas decimais exibidas
    scale: float  # 1, 1e3 ('mil') ou 1e6 ('mi'), só para US$
    line: int


def _blank(match: re.Match) -> str:
    """Troca o trecho por espaços, mantendo as quebras de linha (os números de linha não mudam)."""
    return re.sub(r"[^\n]", " ", match.group(0))


def names_with_digits() -> list[str]:
    """Nomes de produto e conta que contêm dígitos (ex.: 'GTK 500'), que não são números do texto."""
    names = []
    for file, column in [("products.csv", "product"), ("accounts.csv", "account")]:
        names += pd.read_csv(config.RAW_DIR / file, encoding="utf-8")[column].dropna().tolist()
    return sorted({n for n in names if any(ch.isdigit() for ch in n)}, key=len, reverse=True)


def prose_text(text: str, ignore_terms=()) -> str:
    """Texto sem o que não conta como número da prosa: blocos AUTO, código, links, datas, anos,
    numeração de títulos e listas e nomes com dígitos. Mantém o número de linhas."""
    text = AUTO_RE.sub(_blank, text)
    for pattern, flags in _STRIP_PATTERNS:
        text = re.sub(pattern, _blank, text, flags=flags)
    for term in ignore_terms:
        text = re.sub(re.escape(term), _blank, text, flags=re.I)
    return _LINE_PREFIX_RE.sub(lambda m: m.group("lead") + " " * len(m.group("num")), text)


def _parse_pt(number: str) -> tuple[float, int]:
    decimals = len(number.split(",")[1]) if "," in number else 0
    return float(number.replace(".", "").replace(",", ".")), decimals


def extract_number_tokens(text: str) -> list[NumberToken]:
    """Números a conferir: US$, porcentagens, decimais com vírgula e inteiros >= 100 ou com ponto de milhar."""
    tokens = []
    for match in _TOKEN_RE.finditer(text):
        kind = match.lastgroup  # grupo mais externo que casou: usd, pp, pct, dec ou int
        number = match.group(f"{kind}_num") if kind in ("usd", "pp", "pct") else match.group(kind)
        value, decimals = _parse_pt(number)
        scale = _UNIT_SCALE[match.group("unit")] if kind == "usd" else 1.0
        line = text.count("\n", 0, match.start()) + 1
        tokens.append(NumberToken(match.group(0), kind, value, decimals, scale, line))
    return tokens


def _numeric_leaves(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _numeric_leaves(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _numeric_leaves(value)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield abs(float(obj))


def number_pool(sources: dict) -> list[float]:
    """Todos os valores numéricos dos JSONs de fatos mais as constantes estruturais permitidas."""
    values = {abs(float(c)) for c in config.ALLOWED_CONSTANTS}
    for source in sources.values():
        if source is not None:
            values.update(_numeric_leaves(source))
    return sorted(values)


def _close(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


def token_matches(token: NumberToken, pool: list[float]) -> bool:
    """O valor exibido, com a precisão exibida, bate com algum valor do pool?

    US$: o valor é dividido pela unidade exibida (mi, mil). Porcentagem: vale a fração (x100) ou o valor
    já em pontos percentuais. "pp" e "pontos percentuais": a fração x100. Decimal e inteiro: comparação direta.
    O sinal é ignorado.
    """
    d = token.decimals
    for v in pool:
        if token.kind == "usd":
            hit = _close(round_half_up(v / token.scale, d), token.value)
        elif token.kind == "pct":
            hit = _close(round_half_up(v * 100, d), token.value) or _close(round_half_up(v, d), token.value)
        elif token.kind == "pp":  # pontos percentuais: a diferença está guardada como fração
            hit = _close(round_half_up(v * 100, d), token.value)
        else:  # 'dec' e 'int'
            hit = _close(round_half_up(v, d), token.value)
        if hit:
            return True
    return False


def unmatched_numbers(text: str, pool: list[float], ignore_terms=()) -> list[NumberToken]:
    """Números da prosa que não saem de nenhum fato."""
    tokens = extract_number_tokens(prose_text(text, ignore_terms))
    return [t for t in tokens if not token_matches(t, pool)]


# =============================================================================================
# CLI
# =============================================================================================
def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Reescreve os blocos AUTO dos documentos a partir dos JSONs de fatos.")
    parser.add_argument("--check", action="store_true", help="não escreve; exit 1 se algum documento estiver desatualizado")
    args = parser.parse_args(argv)

    blocks = render_blocks()
    stale = []
    for path in config.COVERED_DOCS:
        changed = inject(path, blocks, write=not args.check)
        if changed:
            stale.append(path)
        status = "desatualizado" if (changed and args.check) else ("atualizado" if changed else "sem mudanças")
        print(f"{Path(path).name}: {status}")
    if args.check and stale:
        print("Rode `python -m scorer.docs` para atualizar.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
