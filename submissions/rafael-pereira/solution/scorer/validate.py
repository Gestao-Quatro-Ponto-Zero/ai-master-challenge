"""Validação do Lead Scorer: métricas, backtest temporal e relatório.

Duas camadas no mesmo módulo:

1. Primitivas de métrica (funções puras, numpy/scipy; bloco 3a.2): AUC, captura no top 20%, baseline
   aleatório, bootstrap das diferenças, Brier, log-loss e `beats` (o helper do critério pré-registrado).
2. Backtest (bloco 3b): `evaluate_cut`, `check_criterion`, o teste de atributos, as auditorias e
   `run_backtest`, que grava `data/processed/backtest_metrics.json` e `backtest_tables.md`.

Correção após revisão do Rafael (mudança pós-backtest): o produto passou a usar a curva v2 (faixas isotônicas,
fotos da mesma fase do trimestre). `run_backtest` avalia a v2 e a v1 ("platô") lado a lado nos mesmos cortes e
acrescenta a métrica de ordem DENTRO do Foque (`intra_foque`) e o diagnóstico por fase do trimestre.

Uso: `python -m scorer.validate` (imprime a tabela principal e PASSOU/FALHOU).
Tudo é determinístico: sementes fixas, sem `now()`.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata

from . import config, features
from .score import (  # noqa: F401 - BinnedCurve, fit_binned_curve e pava_nonincreasing moraram aqui (testes e docs os usam)
    CURVE_V1, CURVE_V2, BinnedCurve, FitConfig, LogisticFit, age_design, fit_binned_curve, fit_model,
    pava_nonincreasing, score_deals,
)

# Folga numérica para a comparação do critério: 0,61 - 0,60 vale 0,010000000000000009 em ponto
# flutuante e, sem folga, passaria como "mais de 0,01".
_FLOAT_EPS = 1e-12
_PROB_CLIP = 1e-12


def _vec(x, name: str) -> np.ndarray:
    """Converte para vetor float 1-D."""
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} deve ser unidimensional (recebeu {arr.ndim} dimensões)")
    return arr


def _pair(a, b, name_a: str, name_b: str) -> tuple[np.ndarray, np.ndarray]:
    va, vb = _vec(a, name_a), _vec(b, name_b)
    if len(va) != len(vb):
        raise ValueError(f"{name_a} e {name_b} têm tamanhos diferentes ({len(va)} e {len(vb)})")
    return va, vb


# --- AUC e captura no topo -----------------------------------------------------------------
def auc(score, y) -> float:
    """AUC por Mann-Whitney com posto médio: 1 = ordem perfeita, 0,5 = sem poder, 0 = invertida.

    `y` é binário (0/1 ou bool). Com uma classe só, a AUC não existe: devolve NaN.
    """
    s, yv = _pair(score, y, "score", "y")
    pos = yv != 0
    n1 = int(pos.sum())
    n0 = len(yv) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = rankdata(s)  # método "average": empates recebem o posto médio
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def top_share(score, gain, frac: float = config.TOP_FRAC) -> float:
    """Fração do total de `gain` capturada pelo top `frac` do `score` (por contagem, K = frac*n).

    Ordena o score de forma decrescente. Empates são tratados pelo valor esperado sob desempate
    aleatório: cada grupo de valores iguais entra inteiro se cabe em K; o grupo que cruza K entra
    na fração (K - acumulado)/tamanho do grupo, levando essa fração do ganho do grupo.
    Total de `gain` igual a zero (ou nenhum deal): NaN.

    Com `gain` = y binário é a "captura de ganhos"; com `gain` = close_value dos Won (0 nos
    demais) é a "receita capturada".
    """
    s, g = _pair(score, gain, "score", "gain")
    n = len(s)
    total = g.sum()
    if n == 0 or total == 0:
        return float("nan")
    k = frac * n
    _, inverse, counts = np.unique(s, return_inverse=True, return_counts=True)
    group_gain = np.bincount(inverse.ravel(), weights=g, minlength=len(counts))
    counts = counts[::-1]  # np.unique ordena de forma crescente; queremos do maior score ao menor
    group_gain = group_gain[::-1]
    before = np.cumsum(counts) - counts
    taken = np.clip((k - before) / counts, 0.0, 1.0)
    return float((taken * group_gain).sum() / total)


# --- Baseline aleatório e bootstrap ----------------------------------------------------------
def _summary(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(arr.mean()),
        "p5": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
    }


def random_baseline(
    gain,
    y,
    n_seeds: int = config.RANDOM_SEEDS,
    frac: float = config.TOP_FRAC,
) -> dict:
    """Baseline aleatório: scores sorteados com sementes 0..n_seeds-1 (`default_rng(seed)`).

    `gain` é o ganho monetário (close_value dos Won, 0 nos demais) e `y` o desfecho binário.
    Para cada sorteio calcula a AUC, a captura de ganhos (top_share com gain = y) e a receita
    capturada (top_share com gain = `gain`) no top `frac`.

    Devolve {"auc": ..., "capture": ..., "revenue": ...}, cada um com "mean", "p5" e "p95"
    sobre os sorteios.
    """
    g, yv = _pair(gain, y, "gain", "y")
    y_gain = (yv != 0).astype(float)
    n = len(g)
    aucs, captures, revenues = [], [], []
    for seed in range(n_seeds):
        rnd = np.random.default_rng(seed).random(n)
        aucs.append(auc(rnd, yv))
        captures.append(top_share(rnd, y_gain, frac))
        revenues.append(top_share(rnd, g, frac))
    return {"auc": _summary(aucs), "capture": _summary(captures), "revenue": _summary(revenues)}


def bootstrap_diff(
    score_a,
    score_b,
    gain,
    reps: int = config.BOOTSTRAP_REPS,
    seed: int = 0,
    frac: float = config.TOP_FRAC,
) -> dict:
    """Diferença `top_share(a) - top_share(b)` com IC de 2,5% a 97,5% por bootstrap.

    Reamostra os deals com reposição, com os mesmos índices para os dois métodos (pareado).
    Reamostras sem ganho total (top_share indefinido) são descartadas do IC; "n_valid" diz
    quantas sobraram.

    Devolve {"diff": observada, "ci_low": ..., "ci_high": ..., "n_valid": ...}.
    """
    a, b = _pair(score_a, score_b, "score_a", "score_b")
    g = _vec(gain, "gain")
    if len(g) != len(a):
        raise ValueError(f"gain tem tamanho diferente de score_a ({len(g)} e {len(a)})")
    n = len(a)
    diff = top_share(a, g, frac) - top_share(b, g, frac)
    rng = np.random.default_rng(seed)
    diffs = np.empty(reps)
    for i in range(reps):
        idx = rng.integers(0, n, n)
        diffs[i] = top_share(a[idx], g[idx], frac) - top_share(b[idx], g[idx], frac)
    valid = diffs[~np.isnan(diffs)]
    if len(valid) == 0:
        lo = hi = float("nan")
    else:
        lo, hi = (float(v) for v in np.percentile(valid, [2.5, 97.5]))
    return {"diff": float(diff), "ci_low": lo, "ci_high": hi, "n_valid": int(len(valid))}


# --- Calibração ----------------------------------------------------------------------------
def brier(p, y) -> float:
    """Erro quadrático médio entre a probabilidade `p` e o desfecho binário `y` (menor é melhor)."""
    pv, yv = _pair(p, y, "p", "y")
    if len(pv) == 0:
        return float("nan")
    return float(np.mean((pv - (yv != 0)) ** 2))


def log_loss(p, y) -> float:
    """Log-loss médio (natural); `p` é cortada em [1e-12, 1 - 1e-12] para evitar log(0)."""
    pv, yv = _pair(p, y, "p", "y")
    if len(pv) == 0:
        return float("nan")
    pc = np.clip(pv, _PROB_CLIP, 1 - _PROB_CLIP)
    pos = yv != 0
    return float(-np.mean(np.where(pos, np.log(pc), np.log1p(-pc))))


# --- Critério pré-registrado -----------------------------------------------------------------
def beats(score_value: float, others, tie_tol: float = 0.01) -> bool:
    """True só se `score_value` supera CADA valor de `others` por mais de `tie_tol`.

    Diferença menor ou igual a `tie_tol` é empate, e empate não bate. NaN em qualquer lado não
    bate. `others` vazio é erro (um critério sem baselines passaria sem provar nada).
    """
    values = [float(v) for v in others]
    if not values:
        raise ValueError("beats exige ao menos um valor em `others`")
    return all(float(score_value) - v - tie_tol > _FLOAT_EPS for v in values)


# =============================================================================================
# Backtest (bloco 3b)
# =============================================================================================
METHOD_LABELS = {
    "score": "Score v2 (valor esperado, curva por faixas)",
    "score_v1": "Score v1 (platô, antes da correção)",
    "p_only": "Só a chance v2 (diagnóstico)",
    "valor": "Ordenar por valor",
    "recencia": "Mais recentes primeiro",
    "aleatorio": "Aleatório (média de sorteios)",
}
BASELINES = ("valor", "recencia", "aleatorio")
METRIC_KEYS = ("auc", "ganhos_top20", "receita_top20")
PRIMARY_METRIC = "receita_top20"
INTRA_METHODS = ("score_v2", "score_v1", "valor", "recencia")  # métodos da ordem dentro do Foque, mais o sorteio de referência
INTRA_LABELS = {
    "score_v2": "Score v2 (curva por faixas)",
    "score_v1": "Score v1 (platô)",
    "valor": "Ordenar por valor",
    "recencia": "Mais recentes primeiro",
    "aleatorio": "Aleatório (referência)",
}
SIZE_LABELS = ("pequena", "média", "grande")
CALIBRATION_BANDS = ((0, 30), (31, 60), (61, 90), (91, 120), (121, 150), (151, None))
RULE_TEXT = (
    "O score vence se, nos 4 cortes, a receita capturada no top 20% for maior que a de ordenar por valor, "
    "maior que a de ordenar pelos mais recentes e maior que a média e o percentil 95 de 200 sorteios "
    "aleatórios. Diferença de até 1 ponto percentual é empate, e empate não vence."
)


def _py(obj):
    """Converte para tipos Python puros (NaN vira None), pronto para `json.dump`."""
    if isinstance(obj, dict):
        return {str(k): _py(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_py(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if math.isnan(float(obj)) else float(obj)
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def _band_label(lo, hi) -> str:
    return f"{lo} dias ou mais" if hi is None else f"{lo} a {hi} dias"


def _band_mask(age: np.ndarray, lo, hi) -> np.ndarray:
    return (age >= lo) if hi is None else ((age >= lo) & (age <= hi))


def _mean_or_none(values) -> float | None:
    return float(np.mean(values)) if len(values) else None


# --- logística com penalização seletiva (teste de atributos) -----------------------------------
def fit_logistic_masked(X, y, l2: float, penalized, bounds=None) -> LogisticFit:
    """Como `score.fit_logistic`, mas o L2 vale só para as colunas listadas em `penalized`.

    Com `penalized` = todas as colunas menos o intercepto, dá o mesmo resultado de `fit_logistic(l2=l2)`.
    """
    X = np.asarray(X, dtype="float64")
    y = np.asarray(y, dtype="float64")
    pen = np.zeros(X.shape[1])
    pen[list(penalized)] = 1.0

    def nll_and_grad(b):
        z = X @ b
        nll = np.logaddexp(0.0, z).sum() - y @ z + 0.5 * l2 * np.sum((b * pen) ** 2)
        return nll, X.T @ (expit(z) - y) + l2 * b * pen

    start = np.zeros(X.shape[1])
    base = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
    start[0] = math.log(base / (1 - base))
    result = minimize(
        nll_and_grad, start, jac=True, method="L-BFGS-B", bounds=bounds,
        options={"ftol": 1e-13, "gtol": 1e-9, "maxiter": 1000},
    )
    return LogisticFit(coef=tuple(float(c) for c in result.x), nll=float(result.fun))


# --- um corte: ajuste, população e desfecho ------------------------------------------------------
@dataclass
class _Cut:
    T: pd.Timestamp
    cfg: FitConfig
    kind: str
    model: object
    p_fn: Callable
    train: pd.DataFrame
    pop: pd.DataFrame
    curve: object | None = None


def _population(deals: pd.DataFrame, T: pd.Timestamp, model, cfg: FitConfig) -> pd.DataFrame:
    """Engaging abertos em T (zumbis incluídos) com o desfecho vindo dos dados completos.

    `y`: ganho até o fim dos dados; `gain`: close_value dos ganhos (0 nos demais); `y_h`: ganho até T + H;
    `resolved`: o deal fechou (Won ou Lost) até o fim dos dados.
    """
    scored = score_deals(deals, T, model)
    outcome = deals[["opportunity_id", "deal_stage", "close_date", "close_value"]].rename(
        columns={"deal_stage": "final_stage", "close_date": "final_close_date", "close_value": "final_close_value"}
    )
    pop = scored.merge(outcome, on="opportunity_id", how="left", validate="one_to_one")
    assert len(pop) == len(scored)
    won = pop["final_stage"].eq("Won")
    horizon_end = T + pd.Timedelta(days=cfg.horizon_days)
    pop["y"] = won.astype("int64")
    pop["gain"] = np.where(won, pop["final_close_value"], 0.0)
    pop["y_h"] = (won & (pop["final_close_date"] <= horizon_end)).astype("int64")
    pop["resolved"] = pop["final_stage"].isin(config.CLOSED_STAGES)
    return pop


def _build_cut(deals: pd.DataFrame, T, cfg: FitConfig | None = None, kind: str = "v2") -> _Cut:
    """Um corte T avaliado com a curva `kind`: "v2" (produto), "plateau" (v1) ou "binned" (o ajuste único pré-registrado,
    faixas de 15 dias com pseudo-contagem e todas as fotos; as listas continuam as do modelo v1)."""
    cfg = cfg or FitConfig()
    T = pd.Timestamp(T)
    if kind not in ("v2", "plateau", "binned"):
        raise ValueError(f"curva desconhecida: {kind}")
    model = fit_model(deals, T, replace(cfg, curve=CURVE_V2 if kind == "v2" else CURVE_V1))
    train = features.training_set(features.as_of(deals, T), T, cfg.horizon_days, cfg.first_snapshot)
    pop = _population(deals, T, model, cfg)
    age = pop["age_days"].to_numpy(dtype="float64")
    curve = None
    if kind in ("v2", "plateau"):
        p_fn = model.curve.p_win
        assert np.allclose(p_fn(age), pop["p_win"].to_numpy(dtype="float64")), "p_win do score_deals difere da curva"
    else:
        curve = fit_binned_curve(train["age_days"], train["y"])
        p_fn = curve.p_win
    return _Cut(T, cfg, kind, model, p_fn, train, pop, curve)


def _mm(score_vec, y, gain) -> dict:
    """Os três números de um método: AUC, captura de ganhos e receita capturada no top 20%."""
    yf = np.asarray(y, dtype=float)
    return {"auc": auc(score_vec, yf), "ganhos_top20": top_share(score_vec, yf), "receita_top20": top_share(score_vec, gain)}


def _random_block(gain, y) -> dict:
    rb = random_baseline(gain, y)
    mapping = {"auc": "auc", "ganhos_top20": "capture", "receita_top20": "revenue"}
    out = {k: rb[v]["mean"] for k, v in mapping.items()}
    out["p5"] = {k: rb[v]["p5"] for k, v in mapping.items()}
    out["p95"] = {k: rb[v]["p95"] for k, v in mapping.items()}
    return out


def _model_dict(model) -> dict:
    """Parâmetros do modelo de um corte. Chaves comuns às duas curvas; as da v1 (intercepto, inclinação, meia-vida)
    e as da v2 (fase, pontos da curva, regra do Limpe) só existem na respectiva curva."""
    curve = model.curve
    out = {
        "as_of": model.as_of_date,
        "horizon_days": model.horizon_days,
        "versao": model.version,
        "knot_days": curve.knot_days,
        "p_fresh": curve.p_fresh,
        "limpe_after_days": model.limpe_after_days,
        "max_won_cycle_days": model.max_won_cycle_days,
        "limpe_rule": model.limpe_rule,
        "train_rows": curve.train_rows,
        "train_snapshots": list(curve.train_snapshots),
        "n_snapshots": len(curve.train_snapshots),
        "base_rate": curve.base_rate,
    }
    if model.version == CURVE_V1:
        out.update(intercept=curve.intercept, slope_per_30d=curve.slope_per_30d, halving_days=curve.halving_days)
    else:
        out.update(
            fase=curve.phase,
            fallback=curve.fallback,
            p_cauda=float(curve.p_win(config.AGE_SCAN_MAX_DAYS)),
            curva_pontos=[{"idade": a, "p": float(curve.p_win(a))} for a in config.CURVE_TABLE_AGES],
            faixas={
                "pontos_medios": list(curve.binned.midpoints), "taxas": list(curve.binned.rates),
                "casos": list(curve.binned.counts),
            },
        )
    return out


def _prop_diff_ci(a, b, reps: int = config.BOOTSTRAP_REPS, seed: int = 0) -> dict:
    """Diferença de taxas (b - a) com IC 2,5%-97,5% por bootstrap (cada grupo reamostrado à parte)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) == 0 or len(b) == 0:
        return {"diff": None, "ci_low": None, "ci_high": None}
    rng = np.random.default_rng(seed)
    diffs = np.empty(reps)
    for i in range(reps):
        diffs[i] = b[rng.integers(0, len(b), len(b))].mean() - a[rng.integers(0, len(a), len(a))].mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"diff": float(b.mean() - a.mean()), "ci_low": float(lo), "ci_high": float(hi)}


def _foque_by_age(c: _Cut) -> dict:
    """Dentro do Foque do corte: a chance cai com a idade? (risco levantado na 3a para fins de trimestre)."""
    foque = c.pop.loc[c.pop["category"] == "Foque"]
    age = foque["age_days"].to_numpy(dtype=float)
    yh = foque["y_h"].to_numpy(dtype=float)
    y = foque["y"].to_numpy(dtype=float)
    p = c.p_fn(age)
    rows, masks = [], []
    for lo, hi in config.FOQUE_AGE_BANDS:
        m = _band_mask(age, lo, hi)
        masks.append(m)
        rows.append({
            "faixa": _band_label(lo, hi), "idade_min": lo, "idade_max": hi, "n": int(m.sum()),
            "p_modelo": _mean_or_none(p[m]), "taxa_ganho_90d": _mean_or_none(yh[m]), "taxa_ganho_final": _mean_or_none(y[m]),
        })
    first, last = masks[0], masks[-1]
    return {
        "n_foque": int(len(foque)),
        "faixas": rows,
        "diferenca_ultima_menos_primeira_90d": _prop_diff_ci(yh[first], yh[last]),
    }


def _calibration(c: _Cut) -> list[dict]:
    pop = c.pop
    age = pop["age_days"].to_numpy(dtype=float)
    p = c.p_fn(age)
    yh = pop["y_h"].to_numpy(dtype=float)
    rows = []
    for lo, hi in CALIBRATION_BANDS:
        m = _band_mask(age, lo, hi)
        rows.append({
            "faixa": _band_label(lo, hi), "idade_min": lo, "idade_max": hi, "n": int(m.sum()),
            "p_modelo": _mean_or_none(p[m]), "taxa_observada_90d": _mean_or_none(yh[m]),
        })
    return rows


def _categories(c: _Cut) -> dict:
    pop = c.pop
    total_gain = float(pop["gain"].sum())
    out = {}
    for cat in ("Foque", "Reative", "Limpe"):
        part = pop.loc[pop["category"] == cat]
        gain = float(part["gain"].sum())
        out[cat] = {
            "n": int(len(part)),
            "ganhos": int(part["y"].sum()),
            "pct_ganhos": _mean_or_none(part["y"].to_numpy(dtype=float)),
            "receita_ganha": gain,
            "pct_receita": gain / total_gain if total_gain else None,
            "valor_tabela": float(part["sales_price"].sum()),
            "valor_esperado": float(c.p_fn(part["age_days"].to_numpy(dtype=float)) @ part["sales_price"].to_numpy(dtype=float)),
        }
    return out


def _resolved(c: _Cut, vecs: dict) -> dict:
    """Sensibilidade "só resolvidos": tira os deals ainda abertos em 31/12/2017 (censura à direita)."""
    pop = c.pop
    res = pop["resolved"].to_numpy(dtype=bool)
    ref = pd.Timestamp(config.DEFAULT_REFERENCE_DATE)
    open_age_at_ref = (ref - pop.loc[~pop["resolved"], "engage_date"]).dt.days
    y, gain = pop["y"].to_numpy()[res], pop["gain"].to_numpy(dtype=float)[res]
    out = {
        "n_abertos_em_t": int(len(pop)),
        "n_resolvidos": int(res.sum()),
        "n_abertos_em_31_12": int((~res).sum()),
        "n_abertos_em_31_12_que_ainda_podem_fechar": int((open_age_at_ref <= c.model.max_won_cycle_days).sum()),
        "metodos": {m: _mm(vecs[m][res], y, gain) for m in ("score", "valor", "recencia")},
    }
    out["metodos"]["aleatorio"] = _random_block(gain, y)
    return out


def evaluate_cut(deals: pd.DataFrame, T, cfg: FitConfig | None = None, curve_kind: str = "v2") -> dict:
    """Todas as métricas de um corte T (modelo ajustado só com dados até T; desfecho dos dados completos)."""
    return _evaluate(_build_cut(deals, T, cfg, curve_kind))


def _vectors(c: _Cut) -> dict:
    price = c.pop["sales_price"].to_numpy(dtype=float)
    age = c.pop["age_days"].to_numpy(dtype=float)
    p = c.p_fn(age)
    return {"score": p * price, "p_only": p, "valor": price, "recencia": -age}


def _evaluate(c: _Cut) -> dict:
    pop = c.pop
    y = pop["y"].to_numpy(dtype=int)
    gain = pop["gain"].to_numpy(dtype=float)
    yh = pop["y_h"].to_numpy(dtype=float)
    vecs = _vectors(c)
    metodos = {m: _mm(v, y, gain) for m, v in vecs.items()}
    metodos["aleatorio"] = _random_block(gain, y)
    p = vecs["p_only"]
    base = c.model.curve.base_rate
    constant = np.full(len(yh), base)
    return {
        "cut": c.T.strftime("%Y-%m-%d"),
        "curva": c.kind,
        "modelo": _model_dict(c.model),
        "modelo_faixas": None if c.curve is None else {
            "pontos_medios": list(c.curve.midpoints), "taxas": list(c.curve.rates), "casos": list(c.curve.counts)
        },
        "populacao": {
            "n": int(len(pop)), "ganhos": int(y.sum()), "pct_ganhos": float(y.mean()),
            "receita_ganha": float(gain.sum()), "ganhos_em_90d": int(yh.sum()), "pct_ganhos_em_90d": float(yh.mean()),
            "valor_tabela": float(pop["sales_price"].sum()),
        },
        "metodos": metodos,
        "brier": {
            "modelo": brier(p, yh), "constante": brier(constant, yh),
            "log_loss_modelo": log_loss(p, yh), "log_loss_constante": log_loss(constant, yh), "n": int(len(yh)),
        },
        "bootstrap": {
            "score_menos_valor": bootstrap_diff(vecs["score"], vecs["valor"], gain),
            "score_menos_recencia": bootstrap_diff(vecs["score"], vecs["recencia"], gain),
        },
        "categorias": _categories(c),
        "calibracao": _calibration(c),
        "resolvidos": _resolved(c, vecs),
        "foque_por_idade": _foque_by_age(c),
    }


# --- critério pré-registrado ---------------------------------------------------------------------
def check_criterion(cuts: list[dict], tie_tol: float = config.CRITERION_TIE_TOL) -> dict:
    """Aplica o critério às métricas dos cortes (as mesmas chaves de `evaluate_cut`). Passa só se todos passarem."""
    per_cut = []
    for c in cuts:
        m = c["metodos"]
        s = m["score"][PRIMARY_METRIC]
        rnd = m["aleatorio"]
        checks = {
            "bate_valor": beats(s, [m["valor"][PRIMARY_METRIC]], tie_tol),
            "bate_recencia": beats(s, [m["recencia"][PRIMARY_METRIC]], tie_tol),
            "bate_aleatorio_media": beats(s, [rnd[PRIMARY_METRIC]], tie_tol),
            "bate_aleatorio_p95": beats(s, [rnd["p95"][PRIMARY_METRIC]], tie_tol),
        }
        per_cut.append({
            "cut": c["cut"], "score": s, "valor": m["valor"][PRIMARY_METRIC], "recencia": m["recencia"][PRIMARY_METRIC],
            "aleatorio_media": rnd[PRIMARY_METRIC], "aleatorio_p95": rnd["p95"][PRIMARY_METRIC],
            **checks, "passa": all(checks.values()),
        })
    return {"passed": bool(per_cut) and all(r["passa"] for r in per_cut), "per_cut": per_cut}


def _mean_metrics(cuts: list[dict]) -> dict:
    out = {}
    for method in ("score", "p_only", "valor", "recencia", "aleatorio"):
        out[method] = {k: float(np.mean([c["metodos"][method][k] for c in cuts])) for k in METRIC_KEYS}
    return out


# --- teste de atributos ----------------------------------------------------------------------------
def _size_cuts(deals: pd.DataFrame) -> tuple[float, float]:
    emp = deals.dropna(subset=["account"]).drop_duplicates("account")["employees"].to_numpy(dtype=float)
    lo, hi = np.quantile(emp, [1 / 3, 2 / 3])
    return float(lo), float(hi)


def _add_size(df: pd.DataFrame, size_cuts: tuple[float, float]) -> pd.DataFrame:
    emp = df["employees"].to_numpy(dtype=float)
    idx = np.digitize(emp, size_cuts, right=True)
    label = np.where(np.isnan(emp), None, np.array(SIZE_LABELS, dtype=object)[idx])
    return df.assign(porte=label)


ATTRIBUTES = (
    {"nome": "produto", "coluna": "product", "so_com_conta": False},
    {"nome": "região", "coluna": "regional_office", "so_com_conta": False},
    {"nome": "setor", "coluna": "sector", "so_com_conta": True},
    {"nome": "porte", "coluna": "porte", "so_com_conta": True},
)


def _attribute_cut(c: _Cut, attr: dict, size_cuts) -> dict:
    train = _add_size(c.train, size_cuts)
    pop = _add_size(c.pop, size_cuts)
    if attr["so_com_conta"]:
        train = train.loc[train["has_account"].astype(bool)]
        pop = pop.loc[pop["has_account"].astype(bool)]
    col = attr["coluna"]
    knot = c.model.knot_days
    X0_tr = age_design(train["age_days"].to_numpy(dtype=float), knot)
    X0_ev = age_design(pop["age_days"].to_numpy(dtype=float), knot)
    age_bounds = [(None, None), (None, 0.0)]
    base_fit = _fit_masked_age(X0_tr, train["y"], age_bounds)
    counts = train[col].value_counts()
    reference = sorted(counts[counts == counts.max()].index)[0]
    levels = sorted(v for v in counts.index if v != reference)

    def dummies(values):
        arr = values.to_numpy(dtype=object)
        return np.column_stack([(arr == lv).astype(float) for lv in levels])

    X_tr = np.hstack([X0_tr, dummies(train[col])])
    X_ev = np.hstack([X0_ev, dummies(pop[col])])
    fit = fit_logistic_masked(
        X_tr, train["y"], config.ATTRIBUTE_L2, penalized=range(2, X_tr.shape[1]),
        bounds=age_bounds + [(None, None)] * len(levels),
    )
    p_base = expit(X0_ev @ np.asarray(base_fit.coef))
    p_attr = expit(X_ev @ np.asarray(fit.coef))
    price = pop["sales_price"].to_numpy(dtype=float)
    gain = pop["gain"].to_numpy(dtype=float)
    yh = pop["y_h"].to_numpy(dtype=float)
    ll_base, ll_attr = log_loss(p_base, yh), log_loss(p_attr, yh)
    # diagnóstico (não decide): o mesmo log-loss dentro da amostra de treino, para mostrar se o atributo "parecia" ajudar
    y_tr = train["y"].to_numpy(dtype=float)
    tr_delta = log_loss(expit(X_tr @ np.asarray(fit.coef)), y_tr) - log_loss(expit(X0_tr @ np.asarray(base_fit.coef)), y_tr)
    rev_base, rev_attr = top_share(p_base * price, gain), top_share(p_attr * price, gain)
    return {
        "cut": c.T.strftime("%Y-%m-%d"), "n_treino": int(len(train)), "n_avaliacao": int(len(pop)),
        "log_loss_base": ll_base, "log_loss_atributo": ll_attr, "delta_log_loss": ll_attr - ll_base,
        "delta_log_loss_treino": tr_delta,
        "receita_top20_base": rev_base, "receita_top20_atributo": rev_attr, "delta_receita_top20": rev_attr - rev_base,
        "n_niveis": len(levels) + 1, "referencia": str(reference),
    }


def _fit_masked_age(X0, y, bounds) -> LogisticFit:
    return fit_logistic_masked(X0, y, 0.0, penalized=[], bounds=bounds)


def run_attribute_tests(deals: pd.DataFrame, cuts: list[_Cut]) -> list[dict]:
    """Um atributo por vez sobre a curva de idade (joelho fixo). Entra só se melhorar o log-loss em todos os cortes
    e não piorar a receita no top 20% em nenhum (regra pré-registrada)."""
    size_cuts = _size_cuts(deals)
    out = []
    for attr in ATTRIBUTES:
        per_cut = [_attribute_cut(c, attr, size_cuts) for c in cuts]
        better_ll = all(r["delta_log_loss"] < 0 for r in per_cut)
        not_worse = all(r["delta_receita_top20"] >= -_FLOAT_EPS for r in per_cut)
        out.append({
            "atributo": attr["nome"], "coluna": attr["coluna"],
            "subconjunto": "só deals com conta" if attr["so_com_conta"] else "todos os deals",
            "por_corte": per_cut,
            "melhora_log_loss_em_todos": bool(better_ll),
            "nao_piora_receita_em_nenhum": bool(not_worse),
            "entra": bool(better_ll and not_worse),
        })
    return out


# --- auditorias ---------------------------------------------------------------------------------------
def _audit(deals: pd.DataFrame, cuts: list[_Cut]) -> dict:
    """(i) modelo com o futuro (VAZADO, nunca é resultado); (ii) `has_account` sozinho."""
    ref = config.DEFAULT_REFERENCE_DATE
    vazado, conta = [], []
    for c in cuts:
        # o modelo vazado vê os dados até 31/12/2017, mas com a mesma fase do trimestre do corte (só o futuro difere)
        leaked = fit_model(deals, ref, FitConfig(phase=features.quarter_phase(c.T)))
        pop = c.pop
        y, gain = pop["y"].to_numpy(dtype=int), pop["gain"].to_numpy(dtype=float)
        price = pop["sales_price"].to_numpy(dtype=float)
        age = pop["age_days"].to_numpy(dtype=float)
        honest = _mm(c.model.curve.p_win(age) * price, y, gain)
        leak = _mm(leaked.curve.p_win(age) * price, y, gain)
        vazado.append({
            "cut": c.T.strftime("%Y-%m-%d"), "rotulo": "VAZADO — modelo ajustado com dados até 31/12/2017; não é resultado",
            "knot_days": leaked.curve.knot_days, "p_fresh": leaked.curve.p_fresh, "score_vazado": leak,
            "score_honesto": honest,
            "delta_receita_top20": leak["receita_top20"] - honest["receita_top20"],
            "delta_auc": leak["auc"] - honest["auc"],
        })
        has = pop["has_account"].to_numpy(dtype=bool)
        y_f = y.astype(float)
        conta.append({
            "cut": c.T.strftime("%Y-%m-%d"), "n": int(len(pop)), "n_com_conta": int(has.sum()), "n_sem_conta": int((~has).sum()),
            "auc_has_account": auc(has.astype(float), y_f),
            "ganhos_top20_has_account": top_share(has.astype(float), y_f),
            "receita_top20_has_account": top_share(has.astype(float), gain),
            "taxa_ganho_com_conta": _mean_or_none(y_f[has]), "taxa_ganho_sem_conta": _mean_or_none(y_f[~has]),
            "ganhos_sem_conta": int(y[~has].sum()),
        })
    return {"vazado": vazado, "has_account": conta}


def _sensitivity(deals: pd.DataFrame, main_cuts: list[dict], cfg: FitConfig) -> dict:
    """Mesmas métricas do score v2 com outro desenho de ajuste (`cfg`): sensibilidade, não alternativa."""
    rows, as_cuts = [], []
    for main in main_cuts:
        c = _build_cut(deals, main["cut"], cfg, "v2")
        pop = c.pop
        vecs = _vectors(c)
        y, gain = pop["y"].to_numpy(dtype=int), pop["gain"].to_numpy(dtype=float)
        mm = {m: _mm(vecs[m], y, gain) for m in ("score", "p_only")}
        rows.append({
            "cut": main["cut"], "modelo": _model_dict(c.model), "score": mm["score"], "p_only": mm["p_only"],
            "delta_receita_top20_vs_principal": mm["score"]["receita_top20"] - main["metodos"]["score"]["receita_top20"],
            "delta_auc_vs_principal": mm["score"]["auc"] - main["metodos"]["score"]["auc"],
        })
        as_cuts.append({"cut": main["cut"], "metodos": {**main["metodos"], "score": mm["score"]}})
    crit = check_criterion(as_cuts)
    return {
        "por_corte": rows,
        "media": {k: float(np.mean([r["score"][k] for r in rows])) for k in METRIC_KEYS},
        "criterio": crit,
    }


def _sensitivity_first_snapshot(deals: pd.DataFrame, main_cuts: list[dict]) -> dict:
    """Primeira foto de treino em 28/02/2017."""
    out = _sensitivity(deals, main_cuts, FitConfig(first_snapshot=config.SENSITIVITY_FIRST_SNAPSHOT))
    return {"first_snapshot": config.SENSITIVITY_FIRST_SNAPSHOT, **out}


def _sensitivity_pseudo_count(deals: pd.DataFrame, main_cuts: list[dict]) -> dict:
    """Curva v2 com a pseudo-contagem do ajuste único (20 deals rumo à taxa base em cada faixa)."""
    out = _sensitivity(deals, main_cuts, FitConfig(pseudo_count=config.ADJUST_PSEUDO_COUNT))
    return {"pseudo_count": config.ADJUST_PSEUDO_COUNT, **out}


# --- ordem dentro do Foque -----------------------------------------------------------------------------------
def _intra_foque(c_v1: _Cut, c_v2: _Cut) -> dict:
    """Quem ordena melhor os deals "frescos"? População igual para todos os métodos: os Engaging abertos em T com
    idade <= `config.INTRA_FOQUE_MAX_AGE` dias (independente da categoria que cada curva atribui)."""
    ids = c_v2.pop["opportunity_id"].to_numpy()
    assert (ids == c_v1.pop["opportunity_id"].to_numpy()).all(), "as duas curvas devem pontuar os mesmos deals na mesma ordem"
    mask = (c_v2.pop["age_days"] <= config.INTRA_FOQUE_MAX_AGE).to_numpy()
    sub = c_v2.pop.loc[mask]
    age = sub["age_days"].to_numpy(dtype=float)
    price = sub["sales_price"].to_numpy(dtype=float)
    y = sub["y"].to_numpy(dtype=int)
    gain = sub["gain"].to_numpy(dtype=float)
    vecs = {
        "score_v2": c_v2.p_fn(age) * price,
        "score_v1": c_v1.p_fn(age) * price,
        "valor": price,
        "recencia": -age,
    }
    metodos = {m: {"auc": auc(v, y), "receita_top20": top_share(v, gain)} for m, v in vecs.items()}
    rnd = _random_block(gain, y)
    metodos["aleatorio"] = {"auc": rnd["auc"], "receita_top20": rnd["receita_top20"]}
    return {
        "cut": c_v2.T.strftime("%Y-%m-%d"),
        "n": int(mask.sum()), "ganhos": int(y.sum()), "pct_ganhos": float(y.mean()), "receita_ganha": float(gain.sum()),
        "metodos": metodos,
        "bootstrap": {
            "v2_menos_v1": bootstrap_diff(vecs["score_v2"], vecs["score_v1"], gain),
            "v2_menos_valor": bootstrap_diff(vecs["score_v2"], vecs["valor"], gain),
        },
    }


def _intra_foque_section(cuts_v1: list[_Cut], cuts_v2: list[_Cut]) -> dict:
    per_cut = [_intra_foque(a, b) for a, b in zip(cuts_v1, cuts_v2)]
    methods = [*INTRA_METHODS, "aleatorio"]
    media = {m: {k: float(np.mean([c["metodos"][m][k] for c in per_cut])) for k in ("auc", "receita_top20")} for m in methods}
    return {
        "regra": "Engaging abertos em T com idade de até {} dias; mesma população para todos os métodos.".format(config.INTRA_FOQUE_MAX_AGE),
        "idade_max": config.INTRA_FOQUE_MAX_AGE,
        "labels": INTRA_LABELS,
        "por_corte": per_cut,
        "media": media,
        "v2_vence_v1_em_auc": int(sum(c["metodos"]["score_v2"]["auc"] > c["metodos"]["score_v1"]["auc"] for c in per_cut)),
        "v2_vence_v1_em_receita": int(sum(c["metodos"]["score_v2"]["receita_top20"] > c["metodos"]["score_v1"]["receita_top20"] for c in per_cut)),
    }


# --- diagnóstico por fase do trimestre ----------------------------------------------------------------------------
def _band_rates(age: np.ndarray, y: np.ndarray) -> list[dict]:
    rows = []
    for lo, hi in config.DIAGNOSTIC_AGE_BANDS:
        m = _band_mask(age, lo, hi)
        rows.append({
            "faixa": _band_label(lo, hi), "idade_min": lo, "idade_max": hi, "n": int(m.sum()),
            "ganhos": int(y[m].sum()), "taxa_ganho_90d": _mean_or_none(y[m]),
        })
    return rows


def _diagnostico_fases(deals: pd.DataFrame) -> dict:
    """Por que a curva v1 ficou plana: taxa de ganho em 90 dias por idade, nas fotos de treino de hoje,
    separando fotos de fim de trimestre (mar, jun, set) das de meio de trimestre e de cada fase."""
    T = pd.Timestamp(config.DEFAULT_REFERENCE_DATE)
    train = features.training_set(features.as_of(deals, T), T)
    phase = features.quarter_phase_series(train["snapshot_date"])
    age, y = train["age_days"].to_numpy(dtype=float), train["y"].to_numpy(dtype=float)

    def group(mask: np.ndarray) -> dict:
        dates = sorted({d.strftime("%Y-%m-%d") for d in train.loc[mask, "snapshot_date"]})
        return {"fotos": dates, "linhas": int(mask.sum()), "por_faixa": _band_rates(age[mask], y[mask])}

    end = (phase == config.QUARTER_END_PHASE)
    return {
        "as_of": config.DEFAULT_REFERENCE_DATE,
        "grupos": {
            "fim_de_trimestre": group(end),
            "meio_de_trimestre": group(~end),
            "todas": group(np.ones(len(train), dtype=bool)),
        },
        "fases": {str(p): group(phase == p) for p in (1, 2, 3)},
    }


# --- hoje -------------------------------------------------------------------------------------------------
def _hoje(deals: pd.DataFrame, cfg: FitConfig | None = None) -> dict:
    ref = config.DEFAULT_REFERENCE_DATE
    model = fit_model(deals, ref, cfg)
    scored = score_deals(deals, ref, model, include_prospecting=True)
    cats = {}
    for cat in config.CATEGORIES:
        part = scored.loc[scored["category"] == cat]
        cats[cat] = {
            "n": int(len(part)), "valor_tabela": float(part["sales_price"].sum()),
            "valor_esperado": None if cat == "Qualifique" else float(part["expected_value"].sum()),
        }
    eng = scored.loc[scored["category"] != "Qualifique"]
    age = eng["age_days"].to_numpy(dtype=float)
    foque = eng.loc[eng["category"] == "Foque"]
    fage = foque["age_days"].to_numpy(dtype=float)
    limpe = eng.loc[eng["category"] == "Limpe"]
    above_cycle = limpe["age_days"].to_numpy(dtype=float) > model.max_won_cycle_days
    return {
        "as_of": ref,
        "modelo": _model_dict(model),
        "categorias": cats,
        "limpe_detalhe": {
            "acima_do_maior_ciclo": {"n": int(above_cycle.sum()), "valor_tabela": float(limpe.loc[above_cycle, "sales_price"].sum())},
            "so_pela_chance": {"n": int((~above_cycle).sum()), "valor_tabela": float(limpe.loc[~above_cycle, "sales_price"].sum())},
        },
        "faixas_fixas_do_briefing": {
            "ate_90": int((age <= config.BRIEFING_FRESH_DAYS).sum()),
            "de_91_a_138": int(((age > config.BRIEFING_FRESH_DAYS) & (age <= 138)).sum()),
            "acima_de_138": int((age > 138).sum()),
        },
        "foque_por_idade": [
            {"faixa": _band_label(lo, hi), "idade_min": lo, "idade_max": hi,
             "n": int(_band_mask(fage, lo, hi).sum())}
            for lo, hi in config.FOQUE_AGE_BANDS
        ],
        "sem_conta": {cat: int((~scored.loc[scored["category"] == cat, "has_account"].astype(bool)).sum()) for cat in config.CATEGORIES},
    }


# --- orquestração ---------------------------------------------------------------------------------------
def _run_kind(deals, kind: str) -> tuple[list[_Cut], list[dict]]:
    cuts = [_build_cut(deals, T, FitConfig(), kind) for T in config.BACKTEST_CUTS]
    return cuts, [_evaluate(c) for c in cuts]


def headline_metrics(backtest: dict) -> dict:
    """O dict que `explain.how_it_works` espera (frações da média dos cortes)."""
    return dict(backtest["headline"])


def _brier_mean(evals: list[dict]) -> dict:
    return {k: float(np.mean([c["brier"][k] for c in evals])) for k in ("modelo", "constante", "log_loss_modelo", "log_loss_constante")}


def run_backtest(deals: pd.DataFrame | None = None, write: bool = True) -> dict:
    """Roda o backtest completo e grava `backtest_metrics.json` e `backtest_tables.md`.

    Mudança pós-backtest, pedida pelo Rafael depois de usar a ferramenta como vendedor: o produto usa a curva v2
    (faixas isotônicas, fotos da mesma fase do trimestre). O critério pré-registrado é reportado para a v2
    (`criterion`) e para a v1 (`criterion.runs.v1`), nos mesmos cortes e contra os mesmos baselines.
    """
    from . import clean

    deals = clean.load_deals() if deals is None else deals
    cuts2, eval2 = _run_kind(deals, "v2")
    cuts1, eval1 = _run_kind(deals, "plateau")
    crit2, crit1 = check_criterion(eval2), check_criterion(eval1)
    media2, media1 = _mean_metrics(eval2), _mean_metrics(eval1)

    def run(crit, media):
        return {"passed": crit["passed"], "per_cut": crit["per_cut"], "media_receita_top20_score": media["score"][PRIMARY_METRIC]}

    result = {
        "config": {
            "horizon_days": config.HORIZON_DAYS, "first_snapshot": config.FIRST_SNAPSHOT,
            "reference_date": config.DEFAULT_REFERENCE_DATE, "cuts": list(config.BACKTEST_CUTS),
            "top_frac": config.TOP_FRAC, "random_seeds": config.RANDOM_SEEDS, "bootstrap_reps": config.BOOTSTRAP_REPS,
            "tie_tol": config.CRITERION_TIE_TOL, "attribute_l2": config.ATTRIBUTE_L2,
            "adjust_bin_days": config.ADJUST_BIN_DAYS, "adjust_pseudo_count": config.ADJUST_PSEUDO_COUNT,
            "v2_pseudo_count": config.V2_PSEUDO_COUNT, "foque_half_fraction": config.FOQUE_HALF_FRACTION,
            "limpe_min_chance": config.LIMPE_MIN_CHANCE, "intra_foque_max_age": config.INTRA_FOQUE_MAX_AGE,
            "methods": list(METHOD_LABELS), "method_labels": METHOD_LABELS, "primary_metric": PRIMARY_METRIC,
        },
        "criterion": {
            "rule": RULE_TEXT, "metric": PRIMARY_METRIC, "tie_tol": config.CRITERION_TIE_TOL,
            "passed": crit2["passed"], "adjustment_applied": False, "final_curve": CURVE_V2,
            "post_backtest_change": True, "v1_passed": crit1["passed"],
            "per_cut": crit2["per_cut"], "runs": {CURVE_V1: run(crit1, media1), CURVE_V2: run(crit2, media2)},
        },
        "headline": {
            "n_cortes": len(eval2), "receita_score": media2["score"][PRIMARY_METRIC],
            "receita_valor": media2["valor"][PRIMARY_METRIC], "receita_recencia": media2["recencia"][PRIMARY_METRIC],
        },
        "headline_v1": {"n_cortes": len(eval1), "receita_score": media1["score"][PRIMARY_METRIC]},
        "cuts": eval2,
        "cuts_v1": eval1,
        "media_cortes": {"metodos": media2, "brier": _brier_mean(eval2)},
        "media_cortes_v1": {"metodos": media1, "brier": _brier_mean(eval1)},
        "intra_foque": _intra_foque_section(cuts1, cuts2),
        "diagnostico_fases": _diagnostico_fases(deals),
        "sensibilidade_2017-02-28": _sensitivity_first_snapshot(deals, eval2),
        "sensibilidade_pseudo_contagem": _sensitivity_pseudo_count(deals, eval2),
        "auditoria": _audit(deals, cuts2),
        "atributos": run_attribute_tests(deals, cuts1),  # sobre a curva v1 (joelho fixo): não repetido na v2 (limitação)
        "hoje": _hoje(deals),
        "hoje_v1": _hoje(deals, FitConfig(curve=CURVE_V1)),
    }
    result = _py(result)
    if write:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.BACKTEST_JSON, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        write_tables(result)
    return result


TABLE_BLOCKS = (
    ("Diagnóstico: taxa de ganho por idade e fase do trimestre", "scoring-diagnostico"),
    ("Critério pré-registrado, corte a corte", "scoring-criterio"),
    ("Backtest: corte × método", "scoring-backtest"),
    ("Média dos cortes", "scoring-media"),
    ("Ordem dentro do Foque", "scoring-foque-ordem"),
    ("Categorias por corte", "scoring-categorias"),
    ("Calibração", "scoring-calibracao"),
    ("Bootstrap", "scoring-bootstrap"),
    ("Foque por idade", "scoring-foque-idade"),
    ("Sensibilidades", "scoring-sensibilidade"),
    ("Auditoria", "scoring-auditoria"),
    ("Atributos", "scoring-atributos"),
    ("Modelos por corte (v2)", "scoring-modelos"),
    ("Curva por idade (v2)", "scoring-curva"),
    ("Modelos por corte (v1)", "scoring-modelos-v1"),
    ("Hoje", "scoring-hoje"),
    ("Hoje: antes e depois da correção", "scoring-hoje-antes-depois"),
)


def write_tables(result: dict, path=None) -> None:
    """Grava `backtest_tables.md` com os mesmos renderizadores dos blocos AUTO do SCORING.md."""
    from . import docs

    sources = {"facts": None, "backtest": result}
    parts = ["# Tabelas do backtest\n", "Gerado por `python -m scorer.validate`; não editar à mão.\n"]
    for title, name in TABLE_BLOCKS:
        parts.append(f"## {title}\n\n{docs.BLOCKS[name](sources).strip(chr(10))}\n")
    with open(path or config.BACKTEST_TABLES_MD, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(parts))


def main(argv=None) -> int:
    from .fmt import fmt_date, fmt_dec, fmt_pct

    sys.stdout.reconfigure(encoding="utf-8")
    result = run_backtest()
    print(f"{'corte':<12}{'método':<46}{'AUC':>7}{'ganhos top20':>14}{'receita top20':>15}")
    for cut, cut_v1 in zip(result["cuts"], result["cuts_v1"]):
        rows = [(m, cut["metodos"][m]) for m in ("score", "valor", "recencia", "aleatorio", "p_only")]
        rows.insert(1, ("score_v1", cut_v1["metodos"]["score"]))
        for method, m in rows:
            print(
                f"{fmt_date(cut['cut']):<12}{METHOD_LABELS[method]:<46}{fmt_dec(m['auc'], 2):>7}"
                f"{fmt_pct(m['ganhos_top20'], 1):>14}{fmt_pct(m['receita_top20'], 1):>15}"
            )
    print("média dos cortes:")
    for method, m in result["media_cortes"]["metodos"].items():
        print(
            f"{'':<12}{METHOD_LABELS[method]:<46}{fmt_dec(m['auc'], 2):>7}"
            f"{fmt_pct(m['ganhos_top20'], 1):>14}{fmt_pct(m['receita_top20'], 1):>15}"
        )
    m1 = result["media_cortes_v1"]["metodos"]["score"]
    print(f"{'':<12}{METHOD_LABELS['score_v1']:<46}{fmt_dec(m1['auc'], 2):>7}{fmt_pct(m1['ganhos_top20'], 1):>14}{fmt_pct(m1['receita_top20'], 1):>15}")
    print("\nordem dentro do Foque (Engaging abertos em T com idade <= {} dias), média dos cortes:".format(config.INTRA_FOQUE_MAX_AGE))
    for method, m in result["intra_foque"]["media"].items():
        print(f"{'':<12}{INTRA_LABELS[method]:<46}{fmt_dec(m['auc'], 2):>7}{'':>14}{fmt_pct(m['receita_top20'], 1):>15}")
    crit = result["criterion"]
    print(f"\ncurva final: {crit['final_curve']} (mudança pós-backtest); v1: {'PASSOU' if crit['v1_passed'] else 'FALHOU'}")
    print("CRITÉRIO (v2): " + ("PASSOU" if crit["passed"] else "FALHOU"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
