"""Fixtures compartilhadas: dados sintéticos pequenos + um treino completo (uma vez por sessão)."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_trainer.pipeline import TrainConfig, run_training

SYNTH_SNAPSHOTS = ["2017-07-01", "2017-09-15"]
AGENTS = [("Agent 0", "Mgr A", "East"), ("Agent 1", "Mgr A", "East"), ("Agent 2", "Mgr A", "East"),
          ("Agent 3", "Mgr B", "East"), ("Agent 4", "Mgr B", "East"), ("Agent 5", "Mgr B", "East"),
          ("Agent 6", "Mgr C", "West"), ("Agent 7", "Mgr C", "West")]
PRODUCTS = [("Prod Basic", "S1", 500), ("Prod Pro", "S1", 4000), ("Prod Mid", "S2", 1500), ("Prod Top", "S3", 25000)]


def make_synthetic(directory: Path, seed: int = 0, n: int = 1800) -> Path:
    """Gera CSVs no mesmo formato do dataset real (inclui zumbis, Prospecting e contas faltando)."""
    rng = np.random.default_rng(seed)
    directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(AGENTS, columns=["sales_agent", "manager", "regional_office"]).to_csv(directory / "sales_teams.csv", index=False)
    pd.DataFrame(PRODUCTS, columns=["product", "series", "sales_price"]).to_csv(directory / "products.csv", index=False)

    agent_eff = rng.normal(0, 0.10, len(AGENTS))
    prod_eff = np.array([0.02, -0.03, 0.0, 0.05])
    ai, pi = rng.integers(0, len(AGENTS), n), rng.integers(0, len(PRODUCTS), n)
    engage = pd.Timestamp("2016-10-01") + pd.to_timedelta(rng.integers(0, 440, n), unit="D")
    duration = np.clip(rng.lognormal(np.log(40), 0.6, n), 5, 150).astype(int)
    close = engage + pd.to_timedelta(duration, unit="D")
    won = rng.random(n) < np.clip(0.6 + agent_eff[ai] + prod_eff[pi], 0.05, 0.95)

    end = pd.Timestamp("2017-12-31")
    zombie = (engage < pd.Timestamp("2017-06-01")) & (rng.random(n) < 0.12)
    still_open = (close > end) | zombie
    rows = pd.DataFrame({
        "opportunity_id": [f"OPP{i:05d}" for i in range(n)],
        "sales_agent": [AGENTS[i][0] for i in ai],
        "product": [PRODUCTS[i][0] for i in pi],
        "account": [f"Acc{rng.integers(0, 40)}" if rng.random() > 0.4 else None for _ in range(n)],
        "deal_stage": np.where(still_open, "Engaging", np.where(won, "Won", "Lost")),
        "engage_date": engage, "close_date": close.where(~still_open),
    })
    rows["close_value"] = np.where(rows["deal_stage"] == "Won", [PRODUCTS[i][2] for i in pi], np.where(
        rows["deal_stage"] == "Lost", 0, np.nan))
    rows.loc[0, ["deal_stage", "close_date", "close_value"]] = ["Won", end, PRODUCTS[pi[0]][2]]  # fixa a data de referência
    rows.loc[0, "engage_date"] = end - pd.Timedelta(days=30)

    prosp = pd.DataFrame({
        "opportunity_id": [f"PRO{i:04d}" for i in range(80)],
        "sales_agent": [AGENTS[i][0] for i in rng.integers(0, len(AGENTS), 80)],
        "product": [PRODUCTS[i][0] for i in rng.integers(0, len(PRODUCTS), 80)],
        "account": None, "deal_stage": "Prospecting", "engage_date": pd.NaT, "close_date": pd.NaT, "close_value": np.nan,
    })
    pd.concat([rows, prosp], ignore_index=True).to_csv(directory / "sales_pipeline.csv", index=False, date_format="%Y-%m-%d")
    return directory


def make_config(tmp: Path, data_dir: Path, **kw) -> TrainConfig:
    defaults = dict(data_dir=data_dir, artifact_dir=tmp / "artifacts", db_path=tmp / "app.db",
                    snapshots=list(SYNTH_SNAPSHOTS), force_promote=True,
                    clock=lambda: datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc))
    defaults.update(kw)
    return TrainConfig(**defaults)


@pytest.fixture(scope="session")
def synthetic_dir(tmp_path_factory) -> Path:
    return make_synthetic(tmp_path_factory.mktemp("synthetic"))


@pytest.fixture(scope="session")
def trained(tmp_path_factory, synthetic_dir) -> dict:
    """Um treino completo sobre os dados sintéticos (com backtest). Somente leitura nos testes."""
    tmp = tmp_path_factory.mktemp("trained")
    cfg = make_config(tmp, synthetic_dir)
    result = run_training(cfg)
    return {"result": result, "artifact_dir": cfg.artifact_dir, "db_path": cfg.db_path, "data_dir": synthetic_dir}


@pytest.fixture()
def trained_copy(trained, tmp_path) -> dict:
    """Cópia isolada dos artefatos + banco, para testes que escrevem."""
    art, db = tmp_path / "artifacts", tmp_path / "app.db"
    shutil.copytree(trained["artifact_dir"], art)
    shutil.copy(trained["db_path"], db)
    return {"artifact_dir": art, "db_path": db, "data_dir": trained["data_dir"], "tmp": tmp_path}
