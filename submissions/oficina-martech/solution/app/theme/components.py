"""Componentes HTML do tema Foco — cards, pills, breakdown, brief, funil.

Funções puras (string-in / HTML-out, sem I/O nem Streamlit). Os estilos vêm
das classes CSS injetadas por `styles.inject_css`; aqui só montamos a marcação.
"""
from __future__ import annotations

from html import escape

import pandas as pd

from app.theme.tokens import COLORS, TIER_STYLE, SIGNAL_STYLE


def tier_pill(tier: str) -> str:
    s = TIER_STYLE[tier]
    return (f"<span class='tier-pill' style='background:{s['bg']};color:{s['fg']}'>"
            f"{s['icon']} {tier}</span>")


def _money(v: float) -> str:
    try:
        return f"R$ {v:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _reason_line(r: pd.Series) -> str:
    """Motivo em 1 linha, linguagem de vendedor: prob · valor esperado · urgência."""
    partes = []
    p = r.get("P")
    if p is not None and p == p:  # not NaN
        partes.append(f"Fecha <b>{p:.0%}</b>")
    ev = r.get("expected_value")
    if ev is not None and ev == ev:
        partes.append(f"<b>{_money(ev)}</b> esperado")
    days = r.get("days_open")
    sev = r.get("severity", "na")
    if days is not None and days == days:
        if sev in ("alerta", "critico"):
            partes.append(f"{int(days)}d · esfriando")
        else:
            partes.append(f"{int(days)}d aberto")
    return " · ".join(partes)


def _acc_html(r: pd.Series) -> str:
    """Retorna o nome da conta ou badge de alerta de higiene."""
    if r.get("account"):
        return r["account"]
    c_warn = COLORS["warning"]
    c_soft = COLORS["warning_soft"]
    return (f"<span style='color:{c_warn};font-size:11px;font-weight:700;"
            f"background:{c_soft};padding:1px 6px;border-radius:6px;"
            f"border:1px solid #E5C98E'>⚠ sem conta</span>")


def deal_card_html(r: pd.Series, done: bool = False) -> str:
    """Card do deal: score grande + barra fina, motivo em 1 linha, ação, chip de tier."""
    s = TIER_STYLE[r["tier"]]
    acc = _acc_html(r)
    width = max(4, min(100, int(r["score"])))
    done_cls = " is-done" if done else ""
    if done:
        foot = "<div class='foco-done-tag'>✓ Contatado hoje</div>"
    else:
        foot = f"<div class='foco-action'>▸ {r['action']}</div>"
    return f"""
    <div class='foco-card{done_cls}'>
      <div class='foco-scorewrap'>
        <div class='foco-score' style='color:{s["fg"]}'>{r['score']}</div>
        <div class='foco-bar'><i style='width:{width}%;background:{s["fg"]}'></i></div>
      </div>
      <div class='foco-body'>
        <div class='foco-title'>{r['product']} · {acc}</div>
        <div class='foco-reason'>{_reason_line(r)}</div>
        {foot}
      </div>
      <div>{tier_pill(r['tier'])}</div>
    </div>
    """


def deal_card_compact_html(r: pd.Series, done: bool = False) -> str:
    """Card compacto para o Kanban: score + chip no topo, título, motivo, ação."""
    s = TIER_STYLE[r["tier"]]
    acc = _acc_html(r)
    width = max(4, min(100, int(r["score"])))
    done_cls = " is-done" if done else ""
    if done:
        foot = "<div class='foco-done-tag'>✓ Contatado hoje</div>"
    else:
        foot = f"<div class='foco-action'>▸ {r['action']}</div>"
    return f"""
    <div class='foco-card compact{done_cls}'>
      <div class='kc-top'>
        <div class='foco-score' style='color:{s["fg"]}'>{r['score']}</div>
        {tier_pill(r['tier'])}
      </div>
      <div class='foco-bar'><i style='width:{width}%;background:{s["fg"]}'></i></div>
      <div class='kc-title'>{r['product']} · {acc}</div>
      <div class='foco-reason'>{_reason_line(r)}</div>
      {foot}
    </div>
    """


def kanban_head_html(tier: str, n: int) -> str:
    s = TIER_STYLE[tier]
    return (f"<div class='kanban-head' style='background:{s['bg']};color:{s['fg']}'>"
            f"{s['icon']} {tier}<span class='count'>{n}</span></div>")


def brief_panel_html(must_acts: dict, show_header: bool = True) -> str:
    """Brief visual do dia — renderização HTML da MESMA fonte (`brief_must_acts`)
    que gera o brief .txt. Cada item lidera pelo MOTIVO opinativo (driver
    dominante do deal), não por chips mecânicos; o tier vira badge visual.
    """
    items = (must_acts or {}).get("items", [])
    total = (must_acts or {}).get("count", 0)
    first = (must_acts or {}).get("first", "")

    if not items:
        body = (
            "<div class='brief-empty'>Sem contato prioritário agora. "
            "Use a lista abaixo para trabalhar próximos deals ou revisar descartes.</div>"
        )
    else:
        plural = "deals quentes" if total != 1 else "deal quente"
        greet = (f"<div class='brief-greeting'>Bom dia, {escape(str(first))}. "
                 f"Você tem <b>{total} {plural}</b> pra atacar hoje — comece por estes:</div>")
        rows = []
        for it in items:
            s = TIER_STYLE[it["tier"]]
            rows.append(
                "<div class='brief-item'>"
                f"<div class='brief-rank'>{it['rank']}</div>"
                "<div class='brief-main'>"
                f"<div class='brief-deal'>{escape(str(it['product']))} · {escape(str(it['account']))}</div>"
                f"<div class='brief-motivo'>{escape(str(it['motivo']))}.</div>"
                f"<div class='brief-action'>▸ {escape(str(it['action']))}</div>"
                "</div>"
                f"<div class='brief-aside'>"
                f"<span class='brief-tier' style='background:{s['bg']};color:{s['fg']}'>{s['icon']}</span>"
                f"<span class='brief-score' style='color:{s['fg']}'>{it['score']}<small>score</small></span>"
                "</div>"
                "</div>"
            )
        body = f"{greet}<div class='brief-list'>{''.join(rows)}</div>"

    plural_h = "contatos" if total != 1 else "contato"
    if show_header:
        head = (
            "<div class='brief-head'>"
            "<div class='brief-icon'>📋</div>"
            "<div>"
            "<div class='brief-title'>Brief do dia</div>"
            f"<div class='brief-sub'>{total} {plural_h} priorizados para orientar a primeira rodada de atendimento.</div>"
            "</div>"
            "</div>"
        )
        cls = "brief-panel"
    else:
        head = ""
        cls = "brief-panel is-compact"
    return f"<div class='{cls}'>{head}{body}</div>"


def funnel_html(rows: list) -> str:
    """Barras horizontais do funil: rows = [(label, value_int, pct_float, color)]."""
    parts = []
    for label, val, pct, color in rows:
        parts.append(
            f"<div class='funnel-row'>"
            f"<span class='funnel-label'>{label}</span>"
            f"<div class='funnel-bar-bg'>"
            f"<div class='funnel-bar' style='width:{pct:.1f}%;background:{color}'></div>"
            f"</div>"
            f"<span class='funnel-val'>{val:,} ({pct:.0f}%)</span>".replace(",", ".")
            + "</div>"
        )
    return f"<div class='funnel'>{''.join(parts)}</div>"


def breakdown_html(r: pd.Series) -> str:
    """Renderiza o 'porquê' do score como linhas de fator (substitui a tabela crua)."""
    rows = []
    for b in r["breakdown"]:
        sig = SIGNAL_STYLE.get(b["sinal"], SIGNAL_STYLE["neutro"])
        sign = "+" if b["pontos"] >= 0 else "−"
        rows.append(f"""
          <div class='bd-row'>
            <div class='bd-ico'>{sig['icon']}</div>
            <div class='bd-main'>
              <div class='bd-feature'>{b['feature']}</div>
              <div class='bd-value'>{b['valor']} — {b['porque']}</div>
            </div>
            <div class='bd-weight'>peso {b['peso']:.0%}</div>
            <div class='bd-points' style='color:{sig['fg']}'>{sign}{abs(b['pontos']):.0f}</div>
          </div>""")
    body = "".join(rows)
    return f"""
    <div class='bd-wrap'>{body}</div>
    <div class='bd-foot'>
      Soma dos fatores = <b>score {r['score']}</b> &nbsp;·&nbsp; Ação recomendada: <b>{r['action']}</b>
    </div>
    """


def rep_card_html(rep: dict) -> str:
    """Card de vendedor para a Visão Time — onde o manager age primeiro."""
    foco = rep["foco_agora"]
    foco_color = COLORS["focus"] if foco > 0 else COLORS["slate_2"]
    risk_cls = " risk" if rep["em_risco"] > 0 else ""
    sub = (f"{rep['revisar']} deal{'s' if rep['revisar'] != 1 else ''} a revisar / descartar"
           if rep["revisar"] else "pipeline limpo")
    return f"""
    <div class='rep-card'>
      <div class='rep-foco'>
        <div class='n' style='color:{foco_color}'>🔥 {foco}</div>
        <div class='l'>foco agora</div>
      </div>
      <div class='rep-body'>
        <div class='rep-name'>{rep['agent']}</div>
        <div class='rep-sub'>{sub}</div>
      </div>
      <div class='rep-metrics'>
        <div class='rep-metric'>
          <div class='v'>{_money(rep['pipeline'])}</div>
          <div class='k'>pipeline esperado</div>
        </div>
        <div class='rep-metric'>
          <div class='v{risk_cls}'>{_money(rep['em_risco'])}</div>
          <div class='k'>em risco (&gt;57d)</div>
        </div>
      </div>
    </div>
    """
