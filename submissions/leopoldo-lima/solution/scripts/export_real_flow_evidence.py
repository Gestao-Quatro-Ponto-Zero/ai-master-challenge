"""Exporta respostas HTTP do fluxo com dataset oficial para `artifacts/process-log/test-runs/`.

CRP-REAL-09: evidência reproduzível sem depender de capturas manuais nem do modo `demo_dataset`.
Executar: `python scripts/export_real_flow_evidence.py`
Ou: `python .\\scripts\\tasks.py export-real-flow-evidence`
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from src.api.app import app  # noqa: E402
from src.serving.opportunity_pipeline import clear_serving_cache  # noqa: E402

DEFAULT_OUT = ROOT / "artifacts" / "process-log" / "test-runs"


def main() -> None:
    os.environ.pop("LEAD_SCORER_DATA_SOURCE_MODE", None)

    clear_serving_cache()
    client = TestClient(app)

    out_dir = DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshots: dict[str, tuple[str, dict[str, str] | None]] = {
        "crp-real-09-ranking-limit3.json": ("/api/ranking", {"limit": "3"}),
        "crp-real-09-opportunities-limit2.json": ("/api/opportunities", {"limit": "2"}),
        "crp-real-09-dashboard-kpis.json": ("/api/dashboard/kpis", None),
        "crp-real-09-filter-options.json": ("/api/dashboard/filter-options", None),
    }
    for filename, (path, params) in snapshots.items():
        r = client.get(path, params=params or {})
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        (out_dir / filename).write_text(
            json.dumps(r.json(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    detail_path = "/api/opportunities/1C1I7A6R"
    d = client.get(detail_path)
    assert d.status_code == 200, detail_path
    detail_json = json.dumps(d.json(), indent=2, ensure_ascii=False) + "\n"
    (out_dir / "crp-real-09-detail-1C1I7A6R.json").write_text(detail_json, encoding="utf-8")

    # Atualiza amostras históricas REAL-01/02 (schema atual: deal_stage, campos explícitos).
    r01 = client.get("/api/ranking", params={"limit": "2"})
    assert r01.status_code == 200
    (out_dir / "crp-real-01-sample-ranking-real.json").write_text(
        json.dumps(r01.json(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "crp-real-02-detail-1C1I7A6R.json").write_text(detail_json, encoding="utf-8")

    clear_serving_cache()
    print(f"Wrote evidence JSON under {out_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
