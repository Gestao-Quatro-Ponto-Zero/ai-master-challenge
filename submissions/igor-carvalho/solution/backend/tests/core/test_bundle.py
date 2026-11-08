import numpy as np
import pandas as pd

from lead_core.bundle import ModelBundle
from lead_core.features import what_if_row


def test_bundle_roundtrip_gives_same_predictions(trained, tmp_path):
    version = (trained["artifact_dir"] / "CURRENT").read_text().strip()
    b1 = ModelBundle.load(trained["artifact_dir"] / f"v{version}")
    b1.save(tmp_path / "copy")
    b2 = ModelBundle.load(tmp_path / "copy")

    feats = pd.concat([what_if_row(b1.tables, p, a, age) for p in list(b1.tables["products"])[:3]
                       for a in list(b1.tables["agents"])[:3] for age in (10, 60)], ignore_index=True)
    np.testing.assert_allclose(b1.predict_raw(feats), b2.predict_raw(feats))
    pd.testing.assert_frame_equal(b1.score(feats).drop(columns="reasons"), b2.score(feats).drop(columns="reasons"))


def test_score_output_contract(trained):
    version = (trained["artifact_dir"] / "CURRENT").read_text().strip()
    b = ModelBundle.load(trained["artifact_dir"] / f"v{version}")
    feats = pd.concat([what_if_row(b.tables, "Prod Pro", "Agent 1", a) for a in (5, 110, 300)], ignore_index=True)
    out = b.score(feats)
    assert out["band"].tolist()[1:] == ["stale_risk", "review"]
    assert pd.isna(out["score"].tolist()[2])                     # zumbi não tem score
    assert (out["p_win"].between(0.01, 0.99)).all()
    assert (out["expected_value"] > 0).all()
    assert all(len(r) > 0 for r in out["reasons"])


def test_contributions_sum_matches_logit(trained):
    """pred_contrib + viés = log-odds da predição bruta (garante que a explicação é coerente com o modelo)."""
    version = (trained["artifact_dir"] / "CURRENT").read_text().strip()
    b = ModelBundle.load(trained["artifact_dir"] / f"v{version}")
    feats = pd.concat([what_if_row(b.tables, "Prod Mid", "Agent 4", 30)], ignore_index=True)
    full = b.booster.predict(b.design_matrix(feats), pred_contrib=True)
    p = b.predict_raw(feats)[0]
    assert abs(1 / (1 + np.exp(-full.sum())) - p) < 1e-6
