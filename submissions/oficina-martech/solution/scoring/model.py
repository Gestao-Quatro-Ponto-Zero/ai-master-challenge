"""Modelo de scoring — orquestra features em score 0-100 + breakdown explicável.

score_open_deals() devolve um DataFrame com score, tier, ação e breakdown por deal.
O breakdown é a explainability: cada fator com valor, peso, pontos (contribuição) e porquê.
A soma dos pontos do breakdown == score (auditável).

Decisões de modelagem (ver ../decisoes.md):
- Componente de VALOR usa o tamanho do deal puro (sales_price), NÃO P×valor:
  a probabilidade já tem componente próprio — usá-la também no valor faria P
  contar duas vezes e distorceria os pesos declarados no config.
- expected_value (P × sales_price) continua calculado como coluna INFORMATIVA
  (monetização de risco nas views Time/Saúde), mas fora do score.
- Urgência é uma curva SINO ancorada no ciclo dos Won (features.aging_subscore):
  pico na janela ideal (~57–88d) e decaimento após. Deals "stale"
  (days_open > 138d = Won mais velho da história; nenhum fechou além disso) são
  sinalizados com is_stale, rebaixados para "Baixa Prioridade" por construção
  (tier efetivo) e saem do "Foco Agora": deal morto no topo da lista destrói a
  confiança do vendedor e inflava a contagem de prioridades.
"""
from __future__ import annotations
import pandas as pd

from .config import (
    WEIGHTS_ENGAGING, WEIGHTS_PROSPECTING, TIERS, GLOBAL_WIN_RATE, STALE_DAYS,
)
from .features import smoothed_winrate, aging_subscore, percentile_rank
from . import data as data_layer


def _tier(score: float) -> str:
    for name, cfg in TIERS.items():
        if score >= cfg["min"]:
            return name
    return "Baixa Prioridade"


def _money(v):
    return f"R$ {v:,.0f}".replace(",", ".")


def _top_pct(subscore) -> str:
    """Converte percentil (0-100) em ' · top N%' — torna legível o rank que gera os pontos."""
    if subscore is None or subscore != subscore:  # None/NaN
        return ""
    top = max(1, round(100 - float(subscore)))
    return f" · top {top}%"


def _action(tier: str, severity: str, is_stale: bool) -> str:
    if is_stale:
        return "Revisar com o cliente ou descartar — além de qualquer fechamento histórico."
    if severity == "alerta":
        return "Agir hoje — a janela de fechamento está fechando."
    if tier == "Foco Agora":
        return "Priorizar contato hoje — na janela ideal de fechamento."
    if tier == "Trabalhar":
        return "Manter no radar e nutrir nesta semana."
    return "Baixa prioridade — desqualificar se não evoluir."


def score_open_deals(open_deals: pd.DataFrame | None = None,
                     agent_wr: pd.DataFrame | None = None) -> pd.DataFrame:
    """Calcula o score de todos os deals abertos. Lê do banco se não receber os DataFrames."""
    df = data_layer.load_open_deals() if open_deals is None else open_deals.copy()
    wr = data_layer.load_agent_winrate() if agent_wr is None else agent_wr.copy()
    if df.empty:
        return df

    # 1) probabilidade suavizada por vendedor
    wr["P"] = wr.apply(lambda r: smoothed_winrate(r["wins"], r["closed"]), axis=1)
    df = df.merge(wr[["sales_agent", "P", "wins", "closed"]], on="sales_agent", how="left")
    df["P"] = df["P"].fillna(GLOBAL_WIN_RATE)

    # 2) valor esperado — INFORMATIVO (monetização de risco), fora do score
    df["expected_value"] = df["P"] * df["sales_price"]

    # 3) sub-scores normalizados pela população (percentil = spread robusto)
    #    valor = tamanho do deal puro; probabilidade tem componente próprio
    df["prob_sub"] = percentile_rank(df["P"])
    df["value_sub"] = percentile_rank(df["sales_price"])

    # teto da urgência vem do ciclo dos Won (constantes em config), NÃO da
    # distribuição dos abertos — usar o p90 dos abertos (319d) era a fonte do
    # viés de sobrevivência: marcava tudo como "ainda não crítico".
    aging = df.apply(lambda r: aging_subscore(r["days_open"], r["deal_stage"]), axis=1)
    df["urgency_sub"] = [a[0] if a else None for a in aging]
    df["urgency_label"] = [a[1] if a else "ainda não engajado" for a in aging]
    df["severity"] = [a[2] if a else "na" for a in aging]

    # deal provavelmente morto: mais velho que QUALQUER fechamento histórico
    # (138d = Won mais velho; NaN > x é False, então Prospecting fica fora).
    df["is_stale"] = df["days_open"].gt(STALE_DAYS)

    # 4) score = soma das parcelas arredondadas (mesmas do breakdown) ->
    #    a invariante "soma do breakdown == score" vale por construção
    def _score_row(r):
        return round(sum(_parcelas(r)))

    df["score"] = df.apply(_score_row, axis=1).astype(int)
    df["tier"] = df["score"].apply(_tier)
    # tier EFETIVO: stale nunca é "Foco Agora"/"Trabalhar" por construção, para
    # que a contagem de prioridades bata com a lista exibida (sem stale) e o
    # rep não veja "52 foco agora" quando só 18 aparecem. Stale -> Revisar.
    df.loc[df["is_stale"], "tier"] = "Baixa Prioridade"
    df["action"] = [_action(t, s, st) for t, s, st in
                    zip(df["tier"], df["severity"], df["is_stale"])]
    df["breakdown"] = df.apply(_breakdown, axis=1)

    return df.sort_values("score", ascending=False).reset_index(drop=True)


def _parcelas(r) -> list[float]:
    """Pontos de cada fator, arredondados a 1 casa — fonte única para score e breakdown."""
    engaging = r["deal_stage"] == "Engaging" and pd.notna(r["urgency_sub"])
    if engaging:
        w = WEIGHTS_ENGAGING
        return [round(w["probability"] * r["prob_sub"], 1),
                round(w["value"] * r["value_sub"], 1),
                round(w["urgency"] * r["urgency_sub"], 1)]
    w = WEIGHTS_PROSPECTING
    return [round(w["probability"] * r["prob_sub"], 1),
            round(w["value"] * r["value_sub"], 1),
            0.0]


def _breakdown(r) -> list[dict]:
    """Fatores que compõem o score, em linguagem de vendedor. Soma dos pontos == score."""
    engaging = r["deal_stage"] == "Engaging" and pd.notna(r["urgency_sub"])
    w = WEIGHTS_ENGAGING if engaging else WEIGHTS_PROSPECTING
    p = _parcelas(r)
    # os pontos derivam do PERCENTIL de P/valor na população (rank robusto), não
    # do % ou R$ absoluto. Mostrar o percentil ao lado faz display == mecanismo:
    # o vendedor entende por que "fecha 70%" rende X pontos (é o rank, não o 70%).
    prob_top = _top_pct(r.get("prob_sub"))
    value_top = _top_pct(r.get("value_sub"))
    items = [
        {
            "feature": "Histórico do vendedor",
            "valor": f"fecha {r['P']:.0%} ({int(r['closed'])} deals){prob_top}",
            "peso": w["probability"],
            "pontos": p[0],
            "sinal": "positivo",
            "porque": "win-rate suavizado, ranqueado vs o time — seu maior preditor neste deal",
        },
        {
            "feature": "Tamanho do deal",
            "valor": f"{_money(r['sales_price'])} (esperado {_money(r['expected_value'])}){value_top}",
            "peso": w["value"],
            "pontos": p[1],
            "sinal": "positivo",
            "porque": "tamanho ranqueado vs o pipeline — prioriza onde há mais a ganhar",
        },
    ]
    if engaging:
        sev = r["severity"]
        items.append({
            "feature": "Urgência",
            "valor": r["urgency_label"],
            "peso": WEIGHTS_ENGAGING["urgency"],
            "pontos": p[2],
            "sinal": "alerta" if sev in ("alerta", "critico") else "neutro",
            "porque": "janela ideal de fechamento ~57–88d (mediana→p75 dos Won); "
                      "a chance cai forte após ~88d e é zero além de 138d",
        })
    else:
        items.append({
            "feature": "Urgência",
            "valor": "ainda não engajado (Prospecting)",
            "peso": 0.0, "pontos": 0.0, "sinal": "neutro",
            "porque": "sem data de engajamento — pesos renormalizados sem este fator",
        })
    return items


def _urgencia_frase(r) -> str | None:
    """Frase de urgência a partir do rótulo real do deal (ou None se não aplicável)."""
    label = r.get("urgency_label")
    days = r.get("days_open")
    if (r.get("deal_stage") != "Engaging" or not pd.notna(r.get("urgency_sub"))
            or not label or "não engajado" in str(label) or not pd.notna(days)):
        return None
    d = int(days)
    if str(label).startswith("janela ideal"):
        return f"está na janela ideal de fechamento ({d}d)"
    if str(label).startswith("esquentando"):
        return f"ainda está esquentando ({d}d)"
    if str(label).startswith("janela fechando"):
        return f"a janela está fechando ({d}d)"
    return None


def _brief_motivo_parts(r, is_top_ticket: bool) -> tuple[str, str]:
    """(motivo, ação) do deal — motivo lidera pelo driver que MAIS pesa nele.

    Os números saem do deal real (win-rate, ticket, janela) — nunca inventados.
    Se um driver não tem dado, ele simplesmente não é mencionado. Devolve o motivo
    e a ação separados para o painel poder estilizá-los como linhas distintas; o
    .txt apenas concatena `{motivo}. {ação}`.
    """
    P = r.get("P")
    price = r.get("sales_price")
    sev = r.get("severity", "na")

    prob_ph = (f"você fecha {P:.0%} dos seus deals neste perfil"
               if P is not None and P == P else None)
    if price is not None and price == price:
        val_ph = (f"{_money(price)}, o maior ticket da sua lista" if is_top_ticket
                  else f"ticket de {_money(price)}")
    else:
        val_ph = None
    urg_ph = _urgencia_frase(r)

    pts = {b["feature"]: b["pontos"] for b in r["breakdown"]}
    prob_pts = pts.get("Histórico do vendedor", 0.0)
    val_pts = pts.get("Tamanho do deal", 0.0)

    # lead = driver dominante. Urgência sob pressão (janela fechando) lidera por
    # ser o sinal mais time-sensitive; senão, o maior contribuidor de pontos.
    if sev in ("alerta", "critico") and urg_ph:
        lead, used = urg_ph, "urg"
    elif prob_pts >= val_pts and prob_ph:
        lead, used = prob_ph, "prob"
    elif val_ph:
        lead, used = val_ph, "val"
    else:
        lead, used = prob_ph, "prob"

    # secundário: reforça com outro driver real, no tom de conselho de gestor
    if used == "urg":
        secondary = prob_ph or val_ph
    elif used == "prob":
        secondary = urg_ph if (urg_ph and sev == "ok") else val_ph
    else:  # used == "val"
        secondary = prob_ph or (urg_ph if sev == "ok" else None)

    action = "Aja hoje." if sev in ("alerta", "critico") else "Ligue hoje."
    motivo = lead if lead else f"score {r['score']}"
    if secondary and secondary != lead:
        motivo = f"{motivo} e {secondary}"
    return motivo, action


def _brief_deals(df: pd.DataFrame, agent: str, n: int,
                 exclude: set | None) -> pd.DataFrame:
    """Top-N deals do vendedor elegíveis para o brief — fonte do filtro.

    Exclui stale (vão para revisão), sem conta (ação impossível sem saber quem é
    o cliente) e os já tratados hoje (`exclude`).
    """
    d = df[(df["sales_agent"] == agent) & (~df["is_stale"])]
    if "account" in df.columns:
        d = d[d["account"].notna() & (d["account"] != "")]
    if exclude:
        d = d[~d["opportunity_id"].isin(exclude)]
    return d.head(n)


def brief_must_acts(df: pd.DataFrame, agent: str, n: int = 5,
                    exclude: set | None = None) -> dict:
    """FONTE ÚNICA dos must-acts do dia — consumida tanto pelo brief .txt quanto
    pelo painel visual, para que NUNCA divirjam.

    Devolve `{"first", "count", "items"}` onde cada item carrega o deal e o motivo
    opinativo já resolvido (driver dominante + ação). O .txt renderiza isso como
    texto; `brief_panel_html` estiliza o mesmo conteúdo em HTML. Lista vazia =>
    count 0 (o renderizador decide a mensagem de "pipeline limpo").
    """
    d = _brief_deals(df, agent, n, exclude)
    first = agent.split()[0] if agent and agent.split() else agent
    if d.empty:
        return {"first": first, "count": 0, "items": []}

    count = len(d)
    # só UM deal carrega o selo "maior ticket" (o de maior preço; 1ª ocorrência em empate)
    top_id = d.loc[d["sales_price"].idxmax(), "opportunity_id"] if count > 1 else None

    items = []
    for i, (_, r) in enumerate(d.iterrows(), start=1):
        is_top = r["opportunity_id"] == top_id
        motivo, action = _brief_motivo_parts(r, is_top)
        items.append({
            "rank": i,
            "product": r["product"],
            "account": r["account"],
            "tier": r["tier"],
            "score": int(r["score"]),
            "motivo": motivo,
            "action": action,
        })
    return {"first": first, "count": count, "items": items}


def brief_do_dia(df: pd.DataFrame, agent: str, n: int = 5,
                 exclude: set | None = None) -> str:
    """Brief do dia humano e opinativo (texto) — must-acts numerados, cada um com
    o MOTIVO específico daquele deal ser prioridade hoje (driver real do score).

    Renderização .txt da MESMA fonte (`brief_must_acts`) que alimenta o painel
    visual. Usável fora do app (download .txt / Slack / email).
    """
    ma = brief_must_acts(df, agent, n, exclude)
    if ma["count"] == 0:
        return "Sem deals priorizados hoje — pipeline limpo. Revise os deals em 'Revisar/Descartar'."

    plural = "deals quentes" if ma["count"] != 1 else "deal quente"
    linhas = [f"Bom dia, {ma['first']}. Você tem {ma['count']} {plural} "
              "pra atacar hoje — comece por estes:"]
    for it in ma["items"]:
        linhas.append(f"{it['rank']}. {it['product']} · {it['account']} — "
                      f"{it['motivo']}. {it['action']}")
    return "\n".join(linhas)
