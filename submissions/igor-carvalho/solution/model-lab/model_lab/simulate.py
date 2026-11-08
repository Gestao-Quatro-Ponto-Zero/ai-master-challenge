"""Simulação de N dias (padrão 7) da rotina diária: novos leads mockados -> retreino com o pipeline REAL
de produção (lead_trainer.pipeline.run_training, mesmo portão de qualidade) -> checagens de realidade.
Tudo num workspace temporário; os dados e artefatos do backend nunca são tocados."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from .backend import fingerprint, make_workspace, source_data_dir, use_backend_code
from .metrics import psi
from .mockgen import MockWorld, WorldParams
from .scorers import Challenger

use_backend_code()
from lead_trainer.pipeline import TrainConfig, run_training  # noqa: E402
from lead_trainer.repository import CsvDealRepository  # noqa: E402


def _train_prod(ws: Path, day: pd.Timestamp) -> tuple[dict, pd.DataFrame, dict]:
    clock = lambda: datetime(day.year, day.month, day.day, 2, 0, tzinfo=timezone.utc)  # noqa: E731
    cfg = TrainConfig(data_dir=ws / "data", artifact_dir=ws / "artifacts", db_path=ws / "app.db", clock=clock)
    res = run_training(cfg)
    folder = Path(res["artifact_dir"])
    scored = pd.read_parquet(folder / "scored_deals.parquet").set_index("opportunity_id")
    card = json.loads((folder / "model_card.json").read_text())
    return res, scored, card


def run(ws: Path, days: int = 7, seed: int = 7, params: WorldParams | None = None, log=print) -> dict:
    src = source_data_dir()
    before = fingerprint(src)
    data = make_workspace(ws)
    world = MockWorld(data, seed=seed, params=params)
    daily, prev_scores, preds = [], None, {}
    for d in range(days + 1):                       # dia 0 = dados reais sem mocks (linha de base)
        if d > 0:
            world.step()
            world.write(data)
        day = world.today
        res, sc, card = _train_prod(ws, day)
        df = CsvDealRepository(data).load()
        ch = Challenger().fit(df, day).score(df, day)
        truth = world.true_ev(world.pipe, day)
        thr = card["thresholds"]
        eng = sc[sc["stage"] == "Engaging"]
        live = eng[eng["band"] != "review"]
        t_live = truth.reindex(live.index)
        hi = live[live["score"].astype(float) >= thr["focus_score"]]
        row = {
            "dia": d, "data": day.date().isoformat(), "versao": res["version"], "status": res["status"],
            "motivo": res["reason"], "auc_backtest": res["auc"], "deals_pontuados": res["open_deals_scored"],
            "novos_eventos": sum(1 for e in world.events if e["date"] == day.strftime("%Y-%m-%d")),
            "psi_score_vs_ontem": psi(prev_scores, eng["score"].astype(float).to_numpy()) if prev_scores is not None else None,
            "score>=80_total": int(len(hi)), "score>=80_parados(>p90)": int((hi["age_days"] > thr["stale_days"]).sum()),
            "zumbis_sem_score": int((eng["band"] == "review").sum()),
            # realidade: correlação entre o score e a receita esperada VERDADEIRA em 30 dias (dos não-zumbis)
            "spearman_atual_vs_verdade": float(spearmanr(live["score"].astype(float), t_live).statistic),
            "spearman_novo_vs_verdade": float(spearmanr(ch["ev_h"].reindex(live.index), t_live).statistic),
            "spearman_novo_vs_verdade_todos": float(spearmanr(ch["ev_h"].reindex(truth.index), truth).statistic),
            # regras de negócio
            "regra_zumbi_sem_score": bool(eng.loc[eng["band"] == "review", "score"].isna().all()),
            "regra_score_0_100": bool(live["score"].dropna().between(0, 100).all()),
            "regra_prospecting_sem_score": bool(sc.loc[sc["stage"] == "Prospecting", "score"].isna().all()),
        }
        daily.append(row)
        preds[d] = {"atual": live["score"].astype(float), "novo": ch["ev_h"].reindex(live.index)}
        prev_scores = eng["score"].astype(float).to_numpy()
        log(f"  dia {d} ({row['data']}): {res['status']} AUC={res['auc']:.3f} "
            f"rho atual={row['spearman_atual_vs_verdade']:.2f} novo={row['spearman_novo_vs_verdade']:.2f}")
    # realidade observada: quem ganhou nos dias seguintes estava no topo de ontem?
    ev = pd.DataFrame(world.events)
    won = ev[ev["event"] == "won"]
    realized = []
    for d in range(days):
        later = set(won.loc[won["date"] > daily[d]["data"], "opportunity_id"])
        for name, s in preds[d].items():
            y = s.index.isin(later).astype(int)
            k = max(1, int(len(s) * 0.2))
            top = s.sort_values(ascending=False).index[:k]
            realized.append({"dia": d, "abordagem": name, "ganhos_depois": int(y.sum()),
                             "auc_ganhou_depois": float(roc_auc_score(y, s.fillna(-1))) if 0 < y.sum() < len(y) else None,
                             "ganhos_no_top20": int(pd.Index(top).isin(later).sum())})
    after = fingerprint(src)
    return {"daily": pd.DataFrame(daily), "realized": pd.DataFrame(realized), "events": ev,
            "source_untouched": before == after}
