"""Orquestra o treino: dados -> backtest -> modelo final -> calibração -> pontuação -> artefatos -> portão."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from lead_core.bands import duration_thresholds
from lead_core.bundle import SCORED_FILE, ModelBundle
from lead_core.calibration import apply_calibration
from lead_core.constants import (
    CAT_FEATURES, EXCLUDED_FROM_MODEL, FOCUS_SCORE, FOLLOW_UP_SCORE, HORIZON_DAYS, NUM_FEATURES,
)
from lead_core.features import build_history_tables, apply_tables, open_snapshot

from .calibration import fit_calibration
from .evaluation import backtest, quality_gate, rolling_snapshots
from .registry import ModelRegistry
from .repository import CsvDealRepository, DealRepository
from .training import build_train, fit_gbm

LIMITATIONS = [
    "Poucas variáveis; sem registro de atividades (e-mails, reuniões, último contato)",
    "O score ordena a receita esperada nos próximos 30 dias; não é a chance de ganhar o deal inteiro",
    "Poder de previsão moderado: a ordenação ajuda, mas não substitui o julgamento do vendedor",
    "Mais da metade dos deals abertos são zumbis (sem desfecho observável)",
]


@dataclass
class TrainConfig:
    data_dir: Path
    artifact_dir: Path
    db_path: Path
    reference_date: str | None = None
    snapshots: list[str] = field(default_factory=list)   # vazio = datas móveis (últimas fotos com desfecho conhecido)
    skip_backtest: bool = False
    force_promote: bool = False
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)


def infer_reference_date(df: pd.DataFrame) -> pd.Timestamp:
    return max(df["engage_date"].max(), df["close_date"].max())


def closed_durations(df: pd.DataFrame, T: pd.Timestamp) -> pd.Series:
    closed = df[df["won"].notna() & (df["close_date"] <= T)]
    return (closed["close_date"] - closed["engage_date"]).dt.days


def score_open_deals(df: pd.DataFrame, T: pd.Timestamp, bundle: ModelBundle) -> pd.DataFrame:
    """Pontua Engaging com o modelo e Prospecting com a taxa base do produto."""
    snap = open_snapshot(df, T)
    feats = apply_tables(snap, bundle.tables)
    engaging = _frame(feats, bundle.score(feats), "Engaging")

    # Prospecting ainda não tem engajamento: o valor esperado é o do deal "se engajar hoje" (idade 0), na mesma
    # unidade dos demais (receita esperada em 30 dias). Sem score nem motivos; a idade exibida continua vazia.
    prosp = df[df["deal_stage"] == "Prospecting"].copy()
    prosp["age_days"] = 0.0
    pf = apply_tables(prosp, bundle.tables)
    p_raw, p_win, ev = bundle.expected(pf)
    pf["age_days"] = np.nan
    scored_p = pd.DataFrame({
        "p_win_raw": p_raw, "p_win": p_win, "expected_value": ev, "score": None,
        "band": "prospecting", "confidence": "low", "reasons": [[] for _ in range(len(pf))],
    }, index=pf.index)
    return pd.concat([engaging, _frame(pf, scored_p, "Prospecting")], ignore_index=True)


def _flags(band: str, account_missing: bool) -> list[str]:
    out = {"stale_risk": ["stale"], "review": ["zombie"], "prospecting": ["prospecting"]}.get(band, [])
    return out + (["account_missing"] if account_missing else [])


def _frame(feats: pd.DataFrame, scored: pd.DataFrame, stage: str) -> pd.DataFrame:
    missing = feats["account"].isna()
    out = pd.DataFrame({
        "opportunity_id": feats["opportunity_id"], "seller": feats["sales_agent"], "manager": feats["manager"],
        "office": feats["regional_office"], "stage": stage, "product": feats["product"], "series": feats["series"],
        "account": feats["account"].where(~missing, None), "account_missing": missing,
        "list_price": feats["price"].astype(float),
        "engage_date": feats["engage_date"].dt.strftime("%Y-%m-%d").where(feats["engage_date"].notna(), None),
        "age_days": feats["age_days"],
    })
    for col in ["p_win_raw", "p_win", "expected_value", "band", "confidence"]:
        out[col] = scored[col].to_numpy()
    out["score"] = pd.array(scored["score"].to_numpy(), dtype="Int64")
    out["flags"] = [json.dumps(_flags(b, m)) for b, m in zip(scored["band"], missing)]
    out["reasons"] = [json.dumps(r, ensure_ascii=False) for r in scored["reasons"]]
    return out.reset_index(drop=True)


def _make_bundle(fit, calibration: dict, tables: dict, card: dict) -> ModelBundle:
    return ModelBundle(
        version=card["version"], booster=fit.model.booster_, num=list(NUM_FEATURES), cat=list(CAT_FEATURES),
        cats=fit.cats, calibration=calibration, tables=tables, ref_ev=np.array([]), card=card,
    )


def _reference_distribution(bundle: ModelBundle, feats: pd.DataFrame) -> np.ndarray:
    """Valores esperados (ordenados) dos deals NÃO zumbis: base do score em percentil."""
    ok = feats["age_days"] <= bundle.thresholds["review_days"]
    p = apply_calibration(bundle.predict_raw(feats[ok]), bundle.calibration)
    return np.sort(p * feats.loc[ok, "price"].to_numpy(dtype=float))


def run_training(cfg: TrainConfig, repository: DealRepository | None = None) -> dict:
    repo = repository or CsvDealRepository(cfg.data_dir)
    df = repo.load()
    ref = pd.Timestamp(cfg.reference_date) if cfg.reference_date else infer_reference_date(df)
    now = cfg.clock()
    registry = ModelRegistry(cfg.artifact_dir, cfg.db_path)
    version = registry.next_version(now)

    snapshots = [pd.Timestamp(s) for s in cfg.snapshots] or rolling_snapshots(ref)
    bt = ({"per_snapshot": [], "auc": None, "auc_ci95": None} if cfg.skip_backtest else backtest(df, snapshots))

    train = build_train(df, ref)
    fit = fit_gbm(train)
    calibration = fit_calibration(fit.validation_y, fit.validation_p, fit.train_base_rate)

    snap = open_snapshot(df, ref)
    tables = build_history_tables(df, ref, snap)
    thresholds = {**duration_thresholds(closed_durations(df, ref)),
                  "focus_score": FOCUS_SCORE, "follow_up_score": FOLLOW_UP_SCORE}

    card = {
        "version": version, "engine": "gbm", "trained_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reference_date": ref.date().isoformat(), "features": NUM_FEATURES + CAT_FEATURES,
        "target": f"won_within_{HORIZON_DAYS}d", "horizon_days": HORIZON_DAYS, "score_basis": f"expected_revenue_{HORIZON_DAYS}d",
        "excludes": EXCLUDED_FROM_MODEL, "backtest": bt, "thresholds": thresholds,
        "calibration": {k: calibration[k] for k in ("method", "shift", "brier_calibrated", "brier_constant", "useful", "evaluated")},
        "training": {"rows": int(len(train)), "best_iteration": fit.best_iteration,
                     "closed_deals": int(df["won"].notna().sum())},
        "limitations": LIMITATIONS,
    }
    bundle = _make_bundle(fit, calibration, tables, card)
    bundle.ref_ev = _reference_distribution(bundle, apply_tables(snap, tables))

    scored = score_open_deals(df, ref, bundle)
    bundle.card["training"]["open_deals_scored"] = int(len(scored))

    out_dir = registry.version_dir(version)
    bundle.save(out_dir)
    scored.to_parquet(out_dir / SCORED_FILE, index=False)

    registry.register(version, "gbm", card["trained_at"], card["reference_date"], bt)
    passed, reason = quality_gate(bt, (registry.active() or {}).get("metrics"))
    if cfg.skip_backtest:
        passed, reason = cfg.force_promote, "backtest ignorado (use --force para promover)"
    if passed or cfg.force_promote:
        registry.promote(version)
        status, reason = "active", "promovida" + (" (forçada)" if not passed else "")
    else:
        registry.reject(version, reason)
        status = "rejected"
    return {"version": version, "status": status, "reason": reason, "auc": bt.get("auc"),
            "auc_ci95": bt.get("auc_ci95"), "open_deals_scored": int(len(scored)),
            "artifact_dir": str(out_dir)}
