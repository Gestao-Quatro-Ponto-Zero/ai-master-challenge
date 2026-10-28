"""Lógica de priorização.

Resumo (detalhes e evidências em solution/README.md e process-log/):

    score (0-100) = pontos de VALOR (0-60) + pontos de MOMENTO (0-40)

    VALOR   = preço do produto em escala log. O catálogo vai de US$55 a US$26.768
              (486x), então escala linear faria o GTK 500 engolir todo o resto.
    MOMENTO = P(fechar GANHO nos próximos 30 dias | deal aberto há X dias),
              estimada no histórico. Conta como "em risco" tanto os deals que
              fecharam quanto os que seguem abertos (correção de censura): sem
              isso a curva ignora os deals que empacam e superestima a chance
              dos deals velhos. É o único sinal que se sustentou em backtest;
              vendedor, conta, setor, região e produto não separam Won de Lost
              (AUC ~0.5).

Deals mais velhos que o maior ciclo já observado não têm precedente histórico:
vão para a fila "Revisar ou encerrar" em vez de competir no foco da semana.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

VALUE_POINTS = 60
TIMING_POINTS = 40
HORIZON_DAYS = 30          # "o que fecha no próximo mês"
MIN_SAMPLE = 30            # mínimo de deals históricos para confiar numa taxa
EARLY_PHASE_DAYS = 14      # mediana de duração dos deals perdidos: decisão rápida
LAST_WINDOW_DAYS = 20      # alerta quando faltam <= 20 dias para o maior ciclo histórico
CLOSING_WINDOW_SHARE = 0.75   # "janela de fechamento" = momento >= 75% do pico da curva

LANE_FOCUS = "foco"
LANE_PROSPECT = "prospectar"
LANE_REVIEW = "revisar"


@dataclass
class CycleCurves:
    """Curvas empíricas por idade do deal (em dias desde engage)."""
    ripeness: np.ndarray      # P(won em até HORIZON_DAYS | aberto com idade x)
    p_win: np.ndarray         # P(won algum dia | aberto com idade x)
    sample: np.ndarray        # deals (fechados + abertos) que chegaram vivos à idade x
    max_cycle: int            # maior duração engage->close já observada
    base_win_rate: float

    def at(self, age):
        i = int(np.clip(age, 0, self.max_cycle))
        return self.ripeness[i], self.p_win[i], int(self.sample[i])

    @property
    def peak_ripeness(self):
        return float(self.ripeness.max()) or 1.0

    @property
    def peak_age(self):
        return int(self.ripeness.argmax())


def split_at(deals, as_of):
    """Separa o que se sabia em `as_of`: histórico fechado vs pipeline aberto.

    Permite rodar o mesmo scorer em datas passadas (backtest) sem vazar o futuro.
    """
    as_of = pd.Timestamp(as_of)
    closed = deals[deals["close_date"].notna() & (deals["close_date"] <= as_of)].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)
    closed["cycle_days"] = (closed["close_date"] - closed["engage_date"]).dt.days

    engaged_open = deals["engage_date"].notna() & (deals["engage_date"] <= as_of) & (
        deals["close_date"].isna() | (deals["close_date"] > as_of)
    )
    prospecting = deals["engage_date"].isna()
    open_ = deals[engaged_open | prospecting].copy()
    open_["stage"] = np.where(open_["engage_date"].isna(), "Prospecting", "Engaging")
    open_["age_days"] = (as_of - open_["engage_date"]).dt.days
    return closed, open_


def build_curves(closed, open_ages=()):
    """Curvas por idade. `open_ages`: idade dos deals ainda em Engaging na data de corte.

    Um deal aberto com idade A conta como "vivo e sem fechar" em todas as idades
    x com x + HORIZON_DAYS <= A (sabemos que ele não fechou na janela). Deals
    abertos mais novos que isso ficam de fora daquela idade (desfecho ainda
    desconhecido). É o raciocínio do Kaplan-Meier, aplicado a uma janela fixa.
    """
    if closed.empty:
        raise ValueError("Sem histórico de deals fechados para calibrar o score.")
    days = closed["cycle_days"].to_numpy()
    won = closed["won"].to_numpy().astype(bool)
    open_ages = np.asarray(open_ages, dtype=float)
    max_cycle = int(days.max())
    base = float(won.mean())

    ripeness = np.zeros(max_cycle + 1)
    p_win = np.zeros(max_cycle + 1)
    sample = np.zeros(max_cycle + 1, dtype=int)
    last_r, last_p = base, base
    for x in range(max_cycle + 1):
        alive = days > x
        n_closed = int(alive.sum())
        n_window = n_closed + int((open_ages >= x + HORIZON_DAYS).sum())
        n_ever = n_closed + int((open_ages > x).sum())
        sample[x] = n_ever
        if n_window >= MIN_SAMPLE:
            last_r = float((won & alive & (days <= x + HORIZON_DAYS)).sum() / n_window)
            last_p = float((won & alive).sum() / n_ever)
        # com amostra pequena (cauda da curva) reaproveita a última taxa confiável
        ripeness[x], p_win[x] = last_r, last_p
    return CycleCurves(ripeness, p_win, sample, max_cycle, base)


def value_points(price, min_price, max_price):
    scaled = np.log(np.asarray(price, dtype=float) / min_price) / np.log(max_price / min_price)
    return VALUE_POINTS * np.clip(scaled, 0, 1)


def score_pipeline(deals, as_of, catalog_prices=None):
    """Retorna (pipeline aberto com score e explicação, curvas usadas)."""
    as_of = pd.Timestamp(as_of)
    closed, open_ = split_at(deals, as_of)
    curves = build_curves(closed, open_.loc[open_["stage"] == "Engaging", "age_days"])
    prices = catalog_prices if catalog_prices is not None else deals["sales_price"]
    min_price, max_price = float(prices.min()), float(prices.max())

    open_["value_pts"] = value_points(open_["sales_price"], min_price, max_price)

    rows = []
    for deal in open_.itertuples(index=False):
        rows.append(_classify(deal, curves))
    open_ = pd.concat([open_.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    open_["score"] = (open_["value_pts"] + open_["timing_pts"]).round().astype(int)
    open_["expected_30d"] = open_["ripeness"] * open_["sales_price"]
    open_["reasons"] = [_reasons(d, curves) for d in open_.itertuples(index=False)]
    open_ = open_.sort_values(["score", "sales_price"], ascending=False).reset_index(drop=True)
    return open_, curves


def _classify(deal, curves):
    if deal.stage == "Prospecting":
        return dict(lane=LANE_PROSPECT, phase="Prospecção", ripeness=0.0, p_win=np.nan, sample=0,
                    timing_pts=0.0, deadline=None,
                    action="Fazer o primeiro contato e qualificar")
    age = int(deal.age_days)
    if age > curves.max_cycle:
        return dict(lane=LANE_REVIEW, phase="Sem precedente", ripeness=0.0, p_win=np.nan, sample=0,
                    timing_pts=0.0, deadline=None,
                    action="Confirmar se ainda existe; se não, encerrar como Lost")
    ripeness, p_win, sample = curves.at(age)
    deadline = (deal.engage_date + pd.Timedelta(days=curves.max_cycle)).date().isoformat()
    days_left = curves.max_cycle - age
    if days_left <= LAST_WINDOW_DAYS:
        phase, action = "Última janela", f"Forçar decisão até {_br_date(deadline)} (prazo máximo histórico)"
    elif age <= EARLY_PHASE_DAYS:
        phase, action = "Início", "Qualificar rápido: boa parte dos deals se decide nas 2 primeiras semanas"
    elif ripeness >= CLOSING_WINDOW_SHARE * curves.peak_ripeness:
        phase, action = "Janela de fechamento", "Empurrar para o fechamento esta semana"
    elif age < curves.peak_age:
        phase, action = "Aquecendo", "Manter cadência: poucos deals fecham nessa fase, a janela vem depois"
    else:
        phase, action = "Esfriando", "Pedir decisão: a chance cai a cada semana a partir daqui"
    return dict(lane=LANE_FOCUS, phase=phase, ripeness=ripeness, p_win=p_win, sample=sample,
                timing_pts=TIMING_POINTS * ripeness / curves.peak_ripeness, deadline=deadline, action=action)


def _reasons(deal, curves):
    """Frases curtas, em linguagem de vendedor, explicando o score."""
    reasons = []
    tier = "alto" if deal.value_pts >= 40 else "médio" if deal.value_pts >= 20 else "baixo"
    reasons.append(f"Valor {tier}: {deal.product} a {_usd(deal.sales_price)} "
                   f"(+{deal.value_pts:.0f} de {VALUE_POINTS} pts)")
    if deal.lane == LANE_FOCUS:
        reasons.append(
            f"{int(deal.age_days)} dias em negociação: deals nessa fase fecharam ganhos no mês seguinte "
            f"em {deal.ripeness:.0%} dos casos (base: {deal.sample:,} deals) "
            f"(+{deal.timing_pts:.0f} de {TIMING_POINTS} pts)".replace(",", ".")
        )
        if deal.phase == "Última janela":
            reasons.append(f"Nenhum deal do histórico levou mais de {curves.max_cycle} dias. "
                           f"Prazo: {_br_date(deal.deadline)}.")
    elif deal.lane == LANE_REVIEW:
        reasons.append(f"{int(deal.age_days)} dias em Engaging, e nenhum deal da história levou mais de "
                       f"{curves.max_cycle} dias para fechar. Provavelmente morto ou esquecido no CRM.")
    else:
        reasons.append("Ainda em Prospecting: sem engajamento, não há histórico para estimar quando fecha.")
    if pd.isna(deal.account):
        reasons.append("Conta não preenchida no CRM: preencha para não perder o contexto do cliente.")
    return reasons


def agent_summary(scored):
    review = scored["lane"] == LANE_REVIEW
    flags = pd.DataFrame({
        "sales_agent": scored["sales_agent"],
        "manager": scored["manager"],
        "regional_office": scored["regional_office"],
        "focus_deals": scored["lane"] == LANE_FOCUS,
        "closing_window": scored["phase"].isin(["Janela de fechamento", "Última janela"]),
        "expected_30d": scored["expected_30d"],
        "review_deals": review,
        "review_value": scored["sales_price"].where(review, 0),
        "prospects": scored["lane"] == LANE_PROSPECT,
        "missing_account": scored["account"].isna(),
    })
    summary = flags.groupby(["sales_agent", "manager", "regional_office"]).sum().reset_index()
    return summary.sort_values("expected_30d", ascending=False)


def _usd(v):
    return f"US$ {v:,.0f}".replace(",", ".")


def _br_date(iso):
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"
