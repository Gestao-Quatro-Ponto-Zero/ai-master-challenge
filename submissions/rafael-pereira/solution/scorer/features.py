"""Estado do pipeline numa data passada e conjunto de treino sem vazamento.

Regra de ouro: para um corte T, só vale o que um CRM já teria registrado até o fim do dia T.
- `as_of(deals, T)` reconstrói esse estado a partir das datas (não do estágio final).
- `open_at(view, S)` lista os deals abertos numa foto S <= T.
- `training_set(view, T, H, primeira_foto)` usa só fotos S com S + H <= T, então todo rótulo já é conhecido em T.

Todas as funções são puras: devolvem um DataFrame novo e nunca alteram a entrada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

AS_OF_ATTR = "as_of"  # em DataFrame.attrs: a data T da visão, para `open_at` recusar fotos depois dela
STALE_COLUMNS = ["age_days", "cycle_days", "is_open"]  # derivadas com a data de referência: carregam o futuro
TRAINING_COLUMNS = [
    "snapshot_date", "opportunity_id", "age_days", "product", "sales_price", "regional_office",
    "sector", "employees", "has_account", "y",
]  # sem vendedor nem manager (CLAUDE.md, decisão 4); `has_account` é só diagnóstico (nunca entra no modelo)


def month_ends(start, end) -> pd.DatetimeIndex:
    """Fins de mês entre `start` e `end` (inclusive)."""
    return pd.date_range(start, end, freq="ME")


def as_of(deals: pd.DataFrame, T) -> pd.DataFrame:
    """O pipeline como estava no fim do dia T.

    - Só deals com `engage_date` e engajados até T (Prospecting não tem data, então fica de fora).
    - Quem não fechou até T (sem `close_date` ou com `close_date` > T) volta a ser `Engaging`, sem data e
      sem valor de fechamento: o desfecho posterior a T não existe nesta visão.
    - `age_days`, `cycle_days` e `is_open` são recalculadas em T (as do arquivo usam a data de referência).
    """
    T = pd.Timestamp(T)
    view = deals.loc[deals["engage_date"].notna() & (deals["engage_date"] <= T)].drop(
        columns=STALE_COLUMNS, errors="ignore"
    )
    closed = view["close_date"].notna() & (view["close_date"] <= T)
    view = view.assign(
        deal_stage=view["deal_stage"].where(closed, "Engaging"),
        close_date=view["close_date"].where(closed, pd.NaT),
        close_value=view["close_value"].where(closed, np.nan),
        is_open=~closed,
    )
    age = (T - view["engage_date"]).dt.days.astype("float64")
    cycle = (view["close_date"] - view["engage_date"]).dt.days.astype("float64")
    view = view.assign(age_days=age.where(~closed), cycle_days=cycle.where(closed))
    view.attrs[AS_OF_ATTR] = T
    return view


def open_at(view: pd.DataFrame, S) -> pd.DataFrame:
    """Deals abertos no fim do dia S: engajados até S e (sem fechamento ou fechados depois de S).

    Acrescenta `age_days` = dias entre `engage_date` e S (inteiro). Se `view` veio de `as_of(T)`, exige S <= T.
    """
    S = pd.Timestamp(S)
    limit = view.attrs.get(AS_OF_ATTR)
    if limit is not None:
        assert S <= limit, f"foto {S.date()} é posterior à data da visão ({pd.Timestamp(limit).date()})"
    is_open = (view["engage_date"] <= S) & (view["close_date"].isna() | (view["close_date"] > S))
    out = view.loc[is_open].copy()
    out["age_days"] = (S - out["engage_date"]).dt.days.astype("int64")
    return out


def quarter_phase(date) -> int:
    """Mês dentro do trimestre: 1 (jan, abr, jul, out), 2 (fev, mai, ago, nov) ou 3 (mar, jun, set, dez)."""
    return (pd.Timestamp(date).month - 1) % 3 + 1


def quarter_phase_series(dates) -> np.ndarray:
    """`quarter_phase` de cada data (vetor de inteiros 1, 2 ou 3)."""
    return ((pd.DatetimeIndex(dates).month.to_numpy() - 1) % 3 + 1).astype("int64")


def same_phase(train: pd.DataFrame, phase: int) -> pd.DataFrame:
    """Linhas do treino cuja foto (`snapshot_date`) cai no mesmo mês do trimestre que `phase`."""
    return train.loc[quarter_phase_series(train["snapshot_date"]) == phase]


def snapshot_dates(T, horizon_days: int, first_snapshot) -> pd.DatetimeIndex:
    """Fotos mensais de treino: fins de mês de `first_snapshot` até T, só as que fecham o horizonte até T."""
    T = pd.Timestamp(T)
    dates = month_ends(first_snapshot, T)
    return dates[dates + pd.Timedelta(days=horizon_days) <= T]


def training_set(
    view: pd.DataFrame,
    T,
    horizon_days: int = config.HORIZON_DAYS,
    first_snapshot=config.FIRST_SNAPSHOT,
) -> pd.DataFrame:
    """Uma linha por (foto mensal S, deal aberto em S).

    `y` = 1 se o deal foi ganho até S + horizonte. Como S + horizonte <= T, o rótulo já é conhecido em T.
    """
    T = pd.Timestamp(T)
    horizon = pd.Timedelta(days=horizon_days)
    snaps = snapshot_dates(T, horizon_days, first_snapshot)
    frames = []
    for S in snaps:
        assert S + horizon <= T, "foto cujo horizonte passa de T: vazamento"
        opened = open_at(view, S)
        won_in_window = (opened["deal_stage"] == "Won") & (opened["close_date"] <= S + horizon)
        frames.append(opened.assign(snapshot_date=S, y=won_in_window.astype("int64")))
    if not frames:
        return pd.DataFrame({c: pd.Series(dtype="float64") for c in TRAINING_COLUMNS})
    train = pd.concat(frames, ignore_index=True)[TRAINING_COLUMNS]
    assert train["snapshot_date"].max() + horizon <= T
    return train
