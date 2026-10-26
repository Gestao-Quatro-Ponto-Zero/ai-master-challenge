"""Chance de ganho por idade, valor esperado, score de 0 a 100 e categorias das listas.

Duas curvas de chance (o score e as listas usam a v2; a v1 fica para comparação no backtest):

- **v2 (produto)**: faixas de idade de 15 dias, regressão isotônica não crescente (PAVA) e interpolação linear
  entre os pontos médios. A chance é monotonicamente não crescente **desde o dia 0**. Cada corte T treina só com
  as fotos mensais da **mesma fase do trimestre** que T (mês 1, 2 ou 3), todas com S + H <= T. Se a fase não tem
  nenhuma foto elegível, cai para todas as fotos elegíveis e marca `fallback` na curva.
- **v1 ("platô + queda")**: logit P(idade) = b0 + b1 * max(0, idade - k) / 30, com b1 <= 0. Constante antes do
  joelho k, o que contradiz a taxa observada (50%, 34%, 7% e 0% por faixa de idade no corte de 30/09/2017).

Limiares das listas, a partir da curva (v2): Foque até a idade em que a chance ainda é pelo menos metade da de
um deal novo; Limpe quando a chance cai abaixo de `config.LIMPE_MIN_CHANCE` ou a idade passa do maior ciclo já
ganho até T; Reative é o que fica entre os dois.

Tudo (curva, limiares, escala do score) é ajustado por corte, só com `features.as_of(T)`.
O vendedor não entra em nenhuma função deste módulo.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

from . import config, features

__all__ = [
    "AgeCurve", "BinnedCurve", "FitConfig", "LogisticFit", "PhaseCurve", "ScoreModel", "age_design",
    "fit_age_curve", "fit_binned_curve", "fit_logistic", "fit_model", "limpe_limit", "order_for_list",
    "pava_nonincreasing", "score_deals", "score_from_ev",
]

CATEGORY_ORDER = config.CATEGORIES
AGE_SCALE_DAYS = 30  # a inclinação b1 da v1 é "por 30 dias depois do joelho"
TIE_TOLERANCE = 1e-6  # diferença de NLL abaixo da qual dois joelhos empatam (vence o menor)
NULLABLE_INT_COLUMNS = ("age_days", "score", "days_to_knot", "days_to_limpe")  # inteiros com nulo (Qualifique)
CURVE_V1, CURVE_V2 = "v1", "v2"


@dataclass(frozen=True)
class FitConfig:
    """Parâmetros de desenho do ajuste (valores padrão: `config.py`)."""

    horizon_days: int = config.HORIZON_DAYS
    first_snapshot: str = config.FIRST_SNAPSHOT
    knot_grid: tuple[int, ...] = tuple(config.KNOT_GRID)
    curve: str = CURVE_V2  # "v2" (produto) ou "v1" (platô, para comparação)
    bin_days: int = config.ADJUST_BIN_DAYS
    pseudo_count: float = config.V2_PSEUDO_COUNT
    phase: int | None = None  # só auditoria: força a fase do trimestre (padrão: a de T)


@dataclass(frozen=True)
class LogisticFit:
    """Resultado de `fit_logistic`: coeficientes (o primeiro é o intercepto) e NLL final."""

    coef: tuple[float, ...]
    nll: float


# --- Curva v1: platô + queda ------------------------------------------------------------------------


@dataclass(frozen=True)
class AgeCurve:
    """Curva v1 ("platô + queda") ajustada, mais o que ela viu no treino."""

    knot_days: int
    intercept: float
    slope_per_30d: float
    base_rate: float  # taxa média de ganho no treino (referência do Brier)
    train_rows: int
    train_snapshots: tuple[str, ...]  # fotos mensais usadas (datas ISO)

    def p_win(self, age):
        """Chance de ganho nos próximos H dias para um deal com essa idade (escalar ou array)."""
        age_arr = np.asarray(age, dtype="float64")
        logit = self.intercept + self.slope_per_30d * np.maximum(0.0, age_arr - self.knot_days) / AGE_SCALE_DAYS
        p = expit(logit)
        return float(p) if p.ndim == 0 else p

    @property
    def p_fresh(self) -> float:
        """Chance de um deal novo (platô)."""
        return float(expit(self.intercept))

    @property
    def halving_days(self) -> float | None:
        """Dias depois do joelho até a chance cair à metade do platô (None se a curva é plana)."""
        if self.slope_per_30d == 0:
            return None
        half = self.p_fresh / 2
        return AGE_SCALE_DAYS * (math.log(half / (1 - half)) - self.intercept) / self.slope_per_30d


# --- Curva v2: faixas isotônicas --------------------------------------------------------------------


def pava_nonincreasing(values, weights) -> np.ndarray:
    """Regressão isotônica não crescente por PAVA (blocos adjacentes que sobem são fundidos pela média ponderada)."""
    blocks: list[list[float]] = []  # [média, peso, quantos]
    for value, weight in zip(values, weights):
        blocks.append([float(value), float(weight), 1])
        while len(blocks) > 1 and blocks[-2][0] < blocks[-1][0]:
            m2, w2, c2 = blocks.pop()
            m1, w1, c1 = blocks.pop()
            blocks.append([(m1 * w1 + m2 * w2) / (w1 + w2), w1 + w2, c1 + c2])
    out: list[float] = []
    for mean, _, count in blocks:
        out += [mean] * int(count)
    return np.asarray(out)


@dataclass(frozen=True)
class BinnedCurve:
    """Chance por idade em faixas, interpolada linearmente entre os pontos médios das faixas."""

    midpoints: tuple[float, ...]
    rates: tuple[float, ...]  # não crescente (PAVA); com `alpha` > 0, também suavizada rumo à taxa base
    counts: tuple[int, ...]
    base_rate: float

    def p_win(self, age):
        age_arr = np.asarray(age, dtype="float64")
        p = np.interp(age_arr, self.midpoints, self.rates)
        return float(p) if p.ndim == 0 else p


def fit_binned_curve(
    age, y, width: int = config.ADJUST_BIN_DAYS, alpha: float = config.ADJUST_PSEUDO_COUNT
) -> BinnedCurve:
    """Faixas de `width` dias; taxa = (ganhos + alpha*base)/(n + alpha); PAVA com pesos n + alpha.

    Com alpha = 0 é a regressão isotônica pura (taxa observada, pesos n). Faixas sem nenhum caso são descartadas
    (a interpolação passa por cima delas).
    """
    age = np.asarray(age, dtype="float64")
    y = np.asarray(y, dtype="float64")
    base = float(y.mean())
    idx = (age // width).astype(int)
    size = int(idx.max()) + 1
    n = np.bincount(idx, minlength=size)
    wins = np.bincount(idx, weights=y, minlength=size)
    keep = n > 0
    rate = (wins[keep] + alpha * base) / (n[keep] + alpha)
    iso = pava_nonincreasing(rate, n[keep] + alpha)
    mids = (np.arange(size) * width + width / 2)[keep]
    return BinnedCurve(tuple(float(m) for m in mids), tuple(float(r) for r in iso), tuple(int(c) for c in n[keep]), base)


def last_age_at_or_above(p_win, level: float, max_age: int = config.AGE_SCAN_MAX_DAYS) -> int:
    """Maior idade inteira (0 a `max_age`) em que a chance ainda é >= `level`; -1 se nem a idade 0 chega lá.

    A curva é não crescente, então todas as idades até essa também estão acima de `level`.
    """
    ages = np.arange(0, max_age + 1)
    ok = np.asarray(p_win(ages)) >= level
    return int(ages[ok].max()) if ok.any() else -1


@dataclass(frozen=True)
class PhaseCurve:
    """Curva v2: faixas isotônicas treinadas com as fotos de uma fase do trimestre."""

    binned: BinnedCurve
    phase: int  # mês do trimestre das fotos de treino (1, 2 ou 3)
    knot_days: int  # última idade em que a chance ainda é >= metade da de um deal novo (fim do Foque)
    train_rows: int
    train_snapshots: tuple[str, ...]
    fallback: bool = False  # True: a fase não tinha foto elegível e o ajuste usou todas as fotos

    def p_win(self, age):
        return self.binned.p_win(age)

    @property
    def p_fresh(self) -> float:
        """Chance de um deal novo (idade 0)."""
        return float(self.binned.p_win(0))

    @property
    def base_rate(self) -> float:
        return self.binned.base_rate

    @property
    def halving_days(self) -> None:
        return None


@dataclass(frozen=True)
class ScoreModel:
    """Tudo o que `score_deals` e `explain` precisam, ajustado com dados até `as_of_date`."""

    curve: AgeCurve | PhaseCurve
    limpe_after_days: int  # fim do Reative: depois disso o deal é Limpe (nunca menor que o fim do Foque)
    price_min: float  # menor preço de tabela do catálogo
    price_max: float  # maior preço de tabela do catálogo
    as_of_date: str
    horizon_days: int = config.HORIZON_DAYS
    max_won_cycle_days: int | None = None  # maior ciclo já ganho até a data do modelo

    @property
    def version(self) -> str:
        return CURVE_V1 if isinstance(self.curve, AgeCurve) else CURVE_V2

    @property
    def knot_days(self) -> int:
        """Último dia do Foque: v2, chance >= metade da de um deal novo; v1, joelho do platô."""
        return self.curve.knot_days

    @property
    def p_fresh(self) -> float:
        return self.curve.p_fresh

    @property
    def limpe_rule(self) -> str:
        """'chance' se o Limpe começa porque a chance cai abaixo do mínimo; 'ciclo' se pelo maior ciclo já ganho."""
        if self.max_won_cycle_days is None or self.limpe_after_days >= self.max_won_cycle_days:
            return "ciclo"
        return "chance"

    @property
    def ev_min(self) -> float:
        """Valor esperado de um deal novo do produto mais barato (piso da escala do score)."""
        return self.p_fresh * self.price_min

    @property
    def ev_max(self) -> float:
        """Valor esperado de um deal novo do produto mais caro (teto da escala do score)."""
        return self.p_fresh * self.price_max


# --- Logística com gradiente analítico (v1) -------------------------------------------------------


def fit_logistic(X, y, l2: float = 0.0, bounds=None) -> LogisticFit:
    """Regressão logística por L-BFGS-B. A 1ª coluna de X é o intercepto (não penalizado).

    NLL = soma(logaddexp(0, Xb)) - y.Xb + l2/2 * ||b[1:]||^2.  `bounds`: lista de (min, max) por coeficiente.
    """
    X = np.asarray(X, dtype="float64")
    y = np.asarray(y, dtype="float64")
    penalized = np.ones(X.shape[1])
    penalized[0] = 0.0

    def nll_and_grad(b):
        z = X @ b
        nll = np.logaddexp(0.0, z).sum() - y @ z + 0.5 * l2 * np.sum((b * penalized) ** 2)
        grad = X.T @ (expit(z) - y) + l2 * b * penalized
        return nll, grad

    start = np.zeros(X.shape[1])
    base = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
    start[0] = math.log(base / (1 - base))
    result = minimize(
        nll_and_grad, start, jac=True, method="L-BFGS-B", bounds=bounds,
        options={"ftol": 1e-13, "gtol": 1e-9, "maxiter": 1000},
    )
    return LogisticFit(coef=tuple(float(c) for c in result.x), nll=float(result.fun))


def age_design(age: np.ndarray, knot: int) -> np.ndarray:
    """Matriz de desenho da v1: coluna de 1 (intercepto) e max(0, idade - joelho) / 30."""
    return np.column_stack([np.ones(len(age)), np.maximum(0.0, age - knot) / AGE_SCALE_DAYS])


def fit_age_curve(age, y, knot_grid=config.KNOT_GRID) -> tuple[int, LogisticFit]:
    """Para cada joelho da grade ajusta (b0, b1 <= 0); devolve o de menor NLL (empate: o menor joelho)."""
    age = np.asarray(age, dtype="float64")
    best_knot, best_fit = None, None
    for knot in sorted(knot_grid):
        fit = fit_logistic(age_design(age, knot), y, bounds=[(None, None), (None, 0.0)])
        if best_fit is None or fit.nll < best_fit.nll - TIE_TOLERANCE:
            best_knot, best_fit = int(knot), fit
    return best_knot, best_fit


# --- Ajuste por corte -----------------------------------------------------------------------------


def limpe_limit(won_cycles: pd.Series, knot: int) -> int:
    """Dias de idade a partir dos quais o deal é Limpe (v1): o maior ciclo já ganho, nunca menor que o joelho."""
    return max(int(won_cycles.max()), knot)


def limpe_limit_v2(chance_limit: int, max_won_cycle: int, knot: int) -> int:
    """Último dia do Reative (v2): o primeiro limite que chegar (chance abaixo do mínimo ou maior ciclo ganho), nunca antes do Foque."""
    return max(min(chance_limit, max_won_cycle), knot)


def _fit_v1(train: pd.DataFrame, cfg: FitConfig) -> AgeCurve:
    knot, fit = fit_age_curve(train["age_days"], train["y"], cfg.knot_grid)
    return AgeCurve(
        knot_days=knot,
        intercept=fit.coef[0],
        slope_per_30d=fit.coef[1],
        base_rate=float(train["y"].mean()),
        train_rows=len(train),
        train_snapshots=tuple(sorted({d.strftime("%Y-%m-%d") for d in train["snapshot_date"]})),
    )


def _fit_v2(train: pd.DataFrame, T: pd.Timestamp, cfg: FitConfig) -> PhaseCurve:
    """Faixas isotônicas com as fotos da mesma fase do trimestre que T; sem foto da fase, usa todas (`fallback`)."""
    phase = cfg.phase or features.quarter_phase(T)
    same = features.same_phase(train, phase)
    fallback = same.empty
    used = train if fallback else same
    binned = fit_binned_curve(used["age_days"], used["y"], cfg.bin_days, cfg.pseudo_count)
    knot = last_age_at_or_above(binned.p_win, config.FOQUE_HALF_FRACTION * float(binned.p_win(0)))
    return PhaseCurve(
        binned=binned,
        phase=phase,
        knot_days=knot,
        train_rows=len(used),
        train_snapshots=tuple(sorted({d.strftime("%Y-%m-%d") for d in used["snapshot_date"]})),
        fallback=bool(fallback),
    )


def fit_model(deals: pd.DataFrame, T, cfg: FitConfig | None = None) -> ScoreModel:
    """Modelo do corte T: só enxerga `features.as_of(deals, T)`."""
    cfg = cfg or FitConfig()
    T = pd.Timestamp(T)
    view = features.as_of(deals, T)
    train = features.training_set(view, T, cfg.horizon_days, cfg.first_snapshot)
    if train.empty:
        raise ValueError(f"sem fotos de treino para T={T.date()} (horizonte {cfg.horizon_days} dias)")

    won_cycles = view.loc[view["deal_stage"] == "Won", "cycle_days"]  # só ganhos fechados até T
    max_cycle = int(won_cycles.max())
    if cfg.curve == CURVE_V1:
        curve = _fit_v1(train, cfg)
        limpe = limpe_limit(won_cycles, curve.knot_days)
    elif cfg.curve == CURVE_V2:
        curve = _fit_v2(train, T, cfg)
        chance_limit = last_age_at_or_above(curve.p_win, config.LIMPE_MIN_CHANCE)
        limpe = limpe_limit_v2(chance_limit, max_cycle, curve.knot_days)
    else:
        raise ValueError(f"curva desconhecida: {cfg.curve}")
    return ScoreModel(
        curve=curve,
        limpe_after_days=limpe,
        price_min=float(deals["sales_price"].min()),
        price_max=float(deals["sales_price"].max()),
        as_of_date=T.strftime("%Y-%m-%d"),
        horizon_days=cfg.horizon_days,
        max_won_cycle_days=max_cycle,
    )


# --- Score ----------------------------------------------------------------------------------------


def score_from_ev(ev, model: ScoreModel):
    """Score de 0 a 100: 100 * ln(1 + EV/EV_min) / ln(1 + EV_max/EV_min), arredondado e limitado."""
    ev = np.asarray(ev, dtype="float64")
    raw = 100.0 * np.log1p(ev / model.ev_min) / math.log1p(model.ev_max / model.ev_min)
    return np.clip(np.floor(raw + 0.5), 0, 100).astype("int64")


def _categorize(age: np.ndarray, model: ScoreModel) -> np.ndarray:
    return np.where(age <= model.knot_days, "Foque", np.where(age <= model.limpe_after_days, "Reative", "Limpe"))


def _score_engaging(opened: pd.DataFrame, model: ScoreModel) -> pd.DataFrame:
    age = opened["age_days"].to_numpy(dtype="float64")
    p = model.curve.p_win(age)
    ev = p * opened["sales_price"].to_numpy(dtype="float64")
    cat = _categorize(age, model)
    to_knot = pd.array(np.where(cat == "Foque", model.knot_days - age, np.nan), dtype="Float64").round().astype("Int64")
    to_limpe = pd.array(
        np.where(np.isin(cat, ["Foque", "Reative"]), model.limpe_after_days - age, np.nan), dtype="Float64"
    ).round().astype("Int64")
    return opened.assign(
        p_win=p, expected_value=ev, score=pd.array(score_from_ev(ev, model), dtype="Int64"),
        category=cat, days_to_knot=to_knot, days_to_limpe=to_limpe,
    )


def _qualifique(deals: pd.DataFrame) -> pd.DataFrame:
    prospecting = deals.loc[deals["deal_stage"] == "Prospecting"].drop(columns=features.STALE_COLUMNS, errors="ignore")
    nulls = {
        "age_days": np.nan, "p_win": np.nan, "expected_value": np.nan, "score": pd.NA,
        "days_to_knot": pd.NA, "days_to_limpe": pd.NA,
    }
    return prospecting.assign(category="Qualifique", is_open=True, **nulls)


def score_deals(deals: pd.DataFrame, T, model: ScoreModel, include_prospecting: bool = False) -> pd.DataFrame:
    """Pontua os Engaging abertos em T com o modelo do corte.

    Colunas novas: p_win, expected_value, score (0-100), category (Foque/Reative/Limpe), days_to_knot
    (só Foque), days_to_limpe (Foque e Reative). Com `include_prospecting` (só na data de referência, fim dos
    dados), os Prospecting entram como Qualifique, com p_win, expected_value e score nulos.
    """
    T = pd.Timestamp(T)
    assert pd.Timestamp(model.as_of_date) <= T, "o modelo foi ajustado com dados depois de T"
    opened = features.open_at(features.as_of(deals, T), T)
    scored = _score_engaging(opened, model)
    if include_prospecting:
        last_event = deals[["engage_date", "close_date"]].max().max()
        assert T >= last_event, "Prospecting só é pontuado na data de referência (fim dos dados)"
        scored = pd.concat([scored, _qualifique(deals)], ignore_index=True)
    return scored.astype(dict.fromkeys(NULLABLE_INT_COLUMNS, "Int64")).reset_index(drop=True)


def main(argv=None) -> int:
    """`python -m scorer.score`: parâmetros do modelo em cada corte (v2 e v1) e contagem das listas na data de referência."""
    from . import clean, fmt  # só a linha de comando precisa deles

    sys.stdout.reconfigure(encoding="utf-8")
    deals = clean.load_deals()
    cuts = [*config.BACKTEST_CUTS, config.DEFAULT_REFERENCE_DATE]
    print("curva v2 (faixas isotônicas, fotos da mesma fase do trimestre)")
    print("corte       fase  chance nova  fim do Foque  fim do Reative  regra     fotos  linhas  taxa base")
    for T in cuts:
        model = fit_model(deals, T)
        curve = model.curve
        print(
            f"{T}  {curve.phase:>4}  {fmt.fmt_pct(model.p_fresh, 1):>11}  {model.knot_days:>12}  "
            f"{model.limpe_after_days:>14}  {model.limpe_rule:<8}  {len(curve.train_snapshots):>5}  "
            f"{fmt.fmt_int(curve.train_rows):>6}  {fmt.fmt_pct(curve.base_rate, 1):>9}"
        )
    print("\ncurva v1 (platô + queda, todas as fotos)")
    print("corte       joelho  chance nova  inclinação/30d  meia-vida  limpe  fotos  linhas  taxa base")
    for T in cuts:
        model = fit_model(deals, T, FitConfig(curve=CURVE_V1))
        curve = model.curve
        print(
            f"{T}  {model.knot_days:>6}  {fmt.fmt_pct(model.p_fresh, 1):>11}  {fmt.fmt_dec(curve.slope_per_30d, 2):>14}  "
            f"{fmt.fmt_dec(curve.halving_days, 1):>9}  {model.limpe_after_days:>5}  {len(curve.train_snapshots):>5}  "
            f"{fmt.fmt_int(curve.train_rows):>6}  {fmt.fmt_pct(curve.base_rate, 1):>9}"
        )
    today = config.DEFAULT_REFERENCE_DATE
    for label, cfg in (("v2", FitConfig()), ("v1", FitConfig(curve=CURVE_V1))):
        scored = score_deals(deals, today, fit_model(deals, today, cfg), include_prospecting=True)
        print(f"\nlistas em {fmt.fmt_date(today)} ({label}):")
        for category in CATEGORY_ORDER:
            part = scored[scored["category"] == category]
            print(f"  {category:<11}{fmt.fmt_int(len(part)):>6}  tabela {fmt.fmt_usd(part['sales_price'].sum())}")
    return 0


def order_for_list(scored: pd.DataFrame) -> pd.DataFrame:
    """Ordem de exibição (só UI e briefs; as métricas usam o valor esperado).

    Foque e Reative: valor esperado desc, menos dias até o próximo limiar, id. Limpe: preço desc, idade desc.
    Qualifique: preço desc.
    """
    rules = {
        "Foque": (["expected_value", "days_to_knot", "opportunity_id"], [False, True, True]),
        "Reative": (["expected_value", "days_to_limpe", "opportunity_id"], [False, True, True]),
        "Limpe": (["sales_price", "age_days", "opportunity_id"], [False, False, True]),
        "Qualifique": (["sales_price", "opportunity_id"], [False, True]),
    }
    parts = []
    for category in CATEGORY_ORDER:
        subset = scored.loc[scored["category"] == category]
        by, ascending = rules[category]
        parts.append(subset.sort_values(by, ascending=ascending, kind="mergesort"))
    return pd.concat(parts, ignore_index=True)


if __name__ == "__main__":
    raise SystemExit(main())
