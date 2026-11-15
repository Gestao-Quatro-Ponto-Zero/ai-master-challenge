"""Qualidade dos dados e fontes. Também reexporta meta e login (engine.access).

Qualidade e fontes descrevem a base inteira (inclusive desfechos depois da data), e os textos dizem isso.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, Dict, List

from engine import fmt
from engine.access import login, meta  # noqa: F401  (reexportados: a API importa tudo de engine.quality)
from engine.core import (COUNTRY_FIXES, HORIZON_DAYS, PRODUCT_FIXES, REGION_LABELS, SECTOR_FIXES, TRAIN_FIRST,
                         Dataset, snapshot, summarize)
from engine.facts import (DATASET_LICENSE, DATASET_NAME, base_facts, base_period_label, months_between,
                          share_or_none)
from engine.shapes import date_dict

SMALL_NUMBERS = ("Zero", "Um", "Dois", "Três", "Quatro", "Cinco", "Seis", "Sete", "Oito", "Nove", "Dez")
CRMS = (
    ("Salesforce", "SF", "Oportunidades, contas e histórico de fase"),
    ("HubSpot", "HS", "Negócios, empresas e atividades"),
    ("Pipedrive", "PD", "Negócios, organizações e atividades"),
    ("RD Station CRM", "RD", "Negociações, empresas e tarefas"),
    ("Zoho CRM", "ZH", "Negócios, contas e atividades"),
    ("Microsoft Dynamics 365", "DY", "Oportunidades, contas e atividades"),
)


# ---------------------------------------------------------------- qualidade dos dados

def data_quality(ds: Dataset, d: date) -> Dict[str, Any]:
    """Página "Qualidade dos dados": cobertura, as 5 particularidades, campos vazios, regionais e consertos."""
    b = base_facts(ds)
    st = b["stages"]
    accounts_closed = b["accounts_with_closed"]
    with_deals = len(b["sellers_with_deals"])
    span_first, span_last = b["first_engage"], max(b["last_engage"], b["last_close"])
    months = months_between(span_first, span_last)
    coverage = [
        {"value": fmt.plural(len(ds.deals), "deal"),
         "detail": "%s · %s · %s em negociação · %s em prospecção" % (
             fmt.plural(st["Won"], "ganho"), fmt.plural(st["Lost"], "perdido"),
             fmt.number(st["Engaging"]), fmt.number(st["Prospecting"]))},
        {"value": fmt.plural(len(ds.accounts), "cliente"),
         "detail": "todos com pelo menos um deal fechado" if accounts_closed == len(ds.accounts) else
         "%s com pelo menos um deal fechado" % fmt.number(accounts_closed)},
        {"value": fmt.plural(len(ds.sellers), "vendedor", "vendedores"),
         "detail": "%s com deals e %s só no cadastro" % (fmt.number(with_deals),
                                                        fmt.number(len(ds.sellers) - with_deals))},
        {"value": fmt.plural(months, "mês", "meses"),
         "detail": "de %s a %s" % (fmt.date_label(span_first), fmt.date_label(span_last))},
    ]
    return {
        "date": date_dict(d),
        "coverage": coverage,
        "items": [_item_truncation(ds), _item_account(ds), _item_account_leak(ds, d), _item_quarter(ds),
                  _item_max_cycle(ds, d)],
        "fields": _fields(ds),
        "regions": _regions(ds, d),
        "fixes": _fixes(),
    }


def _item(key: str, number: str, title: str, body: str, action: str, scope: str) -> Dict[str, Any]:
    return {"key": key, "number": number, "title": title, "body": body, "action": action, "scope": scope}


def _item_truncation(ds: Dataset) -> Dict[str, Any]:
    b = base_facts(ds)
    return _item(
        "early_engage", fmt.plural(len(b["early"]), "deal"),
        "A base não registra fechamento antes de %s" % fmt.date_label(b["first_close"]),
        "Esses deals entraram antes dessa data. Só aparecem os que demoraram a fechar ou nunca fecharam, "
        "o que infla o tempo de ciclo.",
        "O score só aprende com retratos tirados a partir de %s, quando o corte já não distorce."
        % fmt.date_label(TRAIN_FIRST), "base inteira")


def _item_account(ds: Dataset) -> Dict[str, Any]:
    b = base_facts(ds)
    missing = share_or_none(b["open_no_account"], len(b["unfinished"]))
    open_match = share_or_none(b["open_home"], b["open_with_account"])
    closed_match = share_or_none(b["closed_home"], b["closed_with_account"])
    return _item(
        "open_account", fmt.pct(missing), "O cliente dos deals abertos não é confiável",
        "No fim da base, %s dos deals abertos não têm cliente. Nos que têm, a regional do vendedor bate com a do cliente em "
        "%s dos casos. Nos fechados, em %s." % (fmt.pct(missing), fmt.pct(open_match), fmt.pct(closed_match)),
        "Cliente, porte e histórico de compras ficam fora do score.", "base inteira")


def _item_account_leak(ds: Dataset, d: date) -> Dict[str, Any]:
    live = snapshot(ds, d).live
    without = [s.deal for s in live if s.deal.account is None]
    with_acc = [s.deal for s in live if s.deal.account is not None]
    without_closed = sum(1 for x in without if x.close_date is not None)
    with_won = sum(1 for x in with_acc if x.won)
    closed_total = len(ds.closed)
    closed_with = base_facts(ds)["closed_with_account"]
    first = ("Todo deal fechado tem cliente." if closed_with == closed_total else
             "%s dos %s deals fechados têm cliente." % (fmt.number(closed_with), fmt.number(closed_total)))
    when = fmt.date_label(d)
    if not without:
        second = "Em %s, todos os deals vivos tinham cliente." % when
    elif without_closed == 0:
        second = "Em %s, nenhum dos %s vivos sem cliente fechou até o fim da base." % (
            when, fmt.plural(len(without), "deal"))
    else:
        second = "Em %s, só %s dos %s vivos sem cliente %s até o fim da base." % (
            when, fmt.number(without_closed), fmt.plural(len(without), "deal"),
            "fechou" if without_closed == 1 else "fecharam")
    third = "Dos %s com cliente, %s %s venda." % (
        fmt.number(len(with_acc)), fmt.number(with_won), "virou" if with_won == 1 else "viraram")
    return _item(
        "account_leak", "%s de %s" % (fmt.number(without_closed), fmt.number(len(without))),
        "Numa data simulada, ter cliente adianta quem vai fechar", " ".join((first, second, third)),
        "O score e a prova ignoram o campo. O filtro Com cliente serve para navegar, não para priorizar.",
        "na data")


def _item_quarter(ds: Dataset) -> Dict[str, Any]:
    b = base_facts(ds)
    old = sum(r[1] for r in b["quarter_rows"])
    closed = sum(r[2] for r in b["quarter_rows"])
    m = b["by_month"]
    last_rate = share_or_none(m[2][0], m[2][1])
    other_rate = share_or_none(m[0][0] + m[1][0], m[0][1] + m[1][1])
    rows = b["quarter_rows"]
    if len(rows) == 1:
        count = "No dia %s, havia %s abertos com mais de %s." % (
            fmt.date_label(rows[0][0]), fmt.plural(old, "deal"), fmt.days(HORIZON_DAYS))
    else:
        count = ("Nos dias %s, havia %s deals abertos com mais de %s (%s somando os dias; o mesmo deal pode "
                 "contar mais de uma vez)." % (
                     fmt.join([fmt.date_label(r[0]) for r in rows]), fmt.join([fmt.number(r[1]) for r in rows]),
                     fmt.days(HORIZON_DAYS), fmt.number(old)))
    if closed == 0:
        first = "%s Nenhum deles fechou naquele mês." % count
    else:
        first = "%s Só %s %s naquele mês." % (count, fmt.number(closed), "fechou" if closed == 1 else "fecharam")
    return _item(
        "quarter_rhythm", "%s de %s" % (fmt.number(closed), fmt.number(old)),
        "O trimestre dita o ritmo dos fechamentos",
        "%s No último mês do trimestre, %s dos fechamentos são venda. Nos outros meses, %s." % (
            first, fmt.pct(last_rate), fmt.pct(other_rate)),
        "A chance muda conforme a semana do trimestre, e não só com a idade do deal.", "base inteira")


def _item_max_cycle(ds: Dataset, d: date) -> Dict[str, Any]:
    b = base_facts(ds)
    snap = snapshot(ds, d)
    total = summarize(snap.deals)
    stale, opened = total["stale"], total["open"]
    limit = "disso" if snap.max_cycle == b["max_cycle"] else "de %s, o maior ciclo conhecido nessa data" % (
        fmt.days(snap.max_cycle))
    if stale == 0:
        second = "Em %s, nenhum dos %s abertos tinha passado %s." % (
            fmt.date_label(d), fmt.plural(opened, "deal"), limit)
    else:
        second = "Em %s, %s %s %s abertos (%s) já %s passado %s." % (
            fmt.date_label(d), fmt.number(stale), "do" if opened == 1 else "dos", fmt.plural(opened, "deal"),
            fmt.pct(share_or_none(stale, opened)), "tinha" if stale == 1 else "tinham", limit)
    return _item(
        "max_cycle", fmt.days(b["max_cycle"]), "Nenhum deal fechou depois de %s" % fmt.days(b["max_cycle"]),
        "É o maior ciclo da base, ganho ou perdido. " + second,
        "Esses deals viram Sem desfecho e saem da fila. Num CRM real, o limite teria de ser recalibrado.",
        "na data")


def _fields(ds: Dataset) -> List[Dict[str, str]]:
    b = base_facts(ds)
    st = b["stages"]
    no_account = b["no_account"]
    all_open = all(x.close_date is None for x in no_account)
    unfinished = len(b["unfinished"])
    return [
        {"field": "Cliente", "text": "Vazio em %s dos %s deals%s." % (
            fmt.number(len(no_account)), fmt.number(len(ds.deals)), ", todos abertos" if all_open else "")},
        {"field": "Data de entrada", "text": "Vazia nos %s em prospecção. Sem ela não há idade, e o deal é "
                                             "ordenado só pelo valor." % fmt.plural(b["no_engage"], "deal")},
        {"field": "Data de fechamento", "text": "Vazia nos %s abertos, como esperado." % fmt.plural(
            unfinished, "deal")},
        {"field": "Valor fechado", "text": "Só nas %s. Deal perdido vem com zero. Em deal aberto, o app usa o "
                                           "preço de tabela." % fmt.plural(st["Won"], "venda")},
    ]


def _regions(ds: Dataset, d: date) -> Dict[str, Any]:
    snap = snapshot(ds, d)
    rows = []
    for code, label in REGION_LABELS.items():
        summary = summarize(s for s in snap.deals if s.deal.region == code)
        rows.append({"region": code, "region_label": label, "open_count": summary["open"],
                     "stale_count": summary["stale"]})
    prospecting = Counter(x.region for x in ds.prospecting)
    return {"date_label": fmt.date_label(d), "rows": rows, "sentence": _regions_sentence(rows, prospecting)}


def _regions_sentence(rows: List[Dict[str, Any]], prospecting: Counter) -> str:
    total_prospecting = sum(prospecting.values())
    clean = [r for r in rows if r["open_count"] and r["stale_count"] == 0]
    only = next(iter(prospecting)) if len(prospecting) == 1 else None
    tail = "o app não compara vendedores de regionais diferentes pelo volume de deals sem desfecho."
    if only is not None and len(clean) == 1 and clean[0]["region"] == only:
        name = REGION_LABELS[only]
        return "A %s só tem deals abertos recentes, e os %s em prospecção são todos dela. Por isso %s" % (
            name, fmt.number(total_prospecting), tail)
    shares = sorted(((share_or_none(r["stale_count"], r["open_count"]) or 0.0, r["region_label"]) for r in rows),
                    key=lambda t: (t[0], t[1]))
    low, high = shares[0], shares[-1]
    first = "A parte dos abertos que está sem desfecho vai de %s (%s) a %s (%s)." % (
        fmt.pct(low[0]), low[1], fmt.pct(high[0]), high[1])
    if only is not None:
        second = " Os %s em prospecção são todos da %s." % (fmt.number(total_prospecting), REGION_LABELS[only])
    elif total_prospecting:
        second = " Os %s em prospecção: %s." % (fmt.number(total_prospecting), ", ".join(
            "%s na %s" % (fmt.number(n), REGION_LABELS[r]) for r, n in sorted(prospecting.items())))
    else:
        second = ""
    # sem uma regional "limpa", a diferença entre as partes não explica a regra: ela vem sem "Por isso"
    return "%s%s %s" % (first, second, tail[0].upper() + tail[1:])


def _fixes() -> Dict[str, str]:
    names = list(PRODUCT_FIXES) + list(SECTOR_FIXES) + list(COUNTRY_FIXES)
    joined = fmt.join(names)
    count = SMALL_NUMBERS[len(names)] if len(names) < len(SMALL_NUMBERS) else fmt.number(len(names))
    return {"title": "Consertos feitos na leitura",
            "text": "%s %s com grafia errada e %s corrigidos: %s." % (
                count, "nome vinha" if len(names) == 1 else "nomes vinham",
                "foi" if len(names) == 1 else "foram", joined)}


# ---------------------------------------------------------------- fontes de dados

def sources(ds: Dataset) -> Dict[str, Any]:
    """Tela "Fontes de dados": a base em uso, CRMs de referência e o que uma integração real precisa trazer."""
    b = base_facts(ds)
    missing = fmt.pct(share_or_none(b["open_no_account"], len(b["unfinished"])))
    return {
        # Texto pedido pelo autor da entrega: manter a redação.
        "alert": "Tela apenas para referência, os dados vêm da base fornecida para o desafio e não de alguma "
                 "integração.",
        "active": {
            "title": "Base do desafio",
            "detail": "%s · licença %s · 4 arquivos CSV lidos quando o app inicia" % (DATASET_NAME, DATASET_LICENSE),
            "status": "Em uso",
            "files": [{"name": name, "description": text, "count_label": count} for name, text, count in (
                ("sales_pipeline.csv", "Oportunidades, %s" % base_period_label(ds), fmt.plural(len(ds.deals), "deal")),
                ("accounts.csv", "Cadastro dos clientes", fmt.plural(len(ds.accounts), "cliente")),
                ("products.csv", "Produtos e preço de tabela", fmt.plural(len(ds.products), "produto")),
                ("sales_teams.csv", "Vendedores, com gestor e regional",
                 fmt.plural(len(ds.sellers), "vendedor", "vendedores")))],
        },
        "crms": {
            "title": "Integrações de CRM",
            "status": "Nenhuma conectada · lista de referência",
            "items": [{"name": n, "initials": i, "brings": t} for n, i, t in CRMS],
        },
        "requirements": {
            "label": "PARA SAIR DA BASE DE TESTE",
            "title": "O que uma integração real precisa trazer",
            "items": [{"title": title, "text": text} for title, text in (
                ("Data de entrada em cada fase",
                 "É a base do score. Hoje só existe a data de entrada em negociação."),
                ("Cliente em todo deal aberto", "Falta em %s dos deals abertos no fim desta base. Sem isso, porte e histórico do "
                                                "cliente não podem entrar no score." % missing),
                ("Histórico da data prevista de fechamento",
                 "Mostra o deal que só tem a data empurrada para a frente."),
                ("Atividades com data e tipo", "Separa contato de verdade de atividade registrada só para constar."),
                ("Valor negociado do deal aberto", "A base só traz o valor de quem fechou. Nos abertos o app usa o "
                                                   "preço de tabela."))],
            "note": "Os itens 3 e 4 vêm da prática de CRM: empurrar a data e registrar atividade são as formas "
                    "mais comuns de manter um deal parado com cara de ativo.",
        },
    }
