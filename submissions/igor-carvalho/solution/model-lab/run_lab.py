"""Uso:
    python run_lab.py                 # backtest real + simulação de 7 dias, relatório em ./out/<data-hora>/
    python run_lab.py --days 3 --skip-backtest
Variáveis: G4_LAB_BACKEND (pasta backend/, padrão ../backend), G4_LAB_DATA (CSVs, padrão backend/data).
O backend e seus dados são só lidos; tudo é gravado em ./out/ e num diretório temporário."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_lab import backtest_real, simulate  # noqa: E402
from model_lab.backend import source_data_dir  # noqa: E402
from model_lab.verdict import verdict  # noqa: E402
from lead_trainer.repository import CsvDealRepository  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--skip-backtest", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    a = ap.parse_args(argv)
    out = Path(a.out) / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    if not a.skip_backtest:
        print("Backtest em dados reais...")
        bt = backtest_real.run(CsvDealRepository(source_data_dir()).load())
        bt.to_csv(out / "backtest_real.csv", index=False)
        summ = backtest_real.summarize(bt)
        summ.to_csv(out / "backtest_real_resumo.csv")
        report["backtest"] = summ.round(4).to_dict(orient="index")
    print(f"Simulação de {a.days} dias com mocks e retreino diário...")
    with tempfile.TemporaryDirectory(prefix="g4-lab-") as tmp:
        sim = simulate.run(Path(tmp), days=a.days, seed=a.seed)
    sim["daily"].to_csv(out / "simulacao_diaria.csv", index=False)
    sim["realized"].to_csv(out / "simulacao_realizado.csv", index=False)
    sim["events"].to_csv(out / "mock_eventos.csv", index=False)
    report["simulacao"] = sim["daily"].to_dict(orient="records")
    report["dados_originais_intactos"] = sim["source_untouched"]
    report["veredito"] = verdict(report)
    (out / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(sim["daily"].drop(columns=["motivo"]).to_string(index=False))
    print(json.dumps(report["veredito"], ensure_ascii=False, indent=2))
    print(f"\nRelatório: {out}")
    return 0 if report["veredito"]["score_atual_condizente"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
