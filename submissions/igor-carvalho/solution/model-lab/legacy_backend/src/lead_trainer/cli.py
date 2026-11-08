"""CLI do treinamento: python -m lead_trainer {train|evaluate|list|promote}."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

from lead_core.constants import DEFAULT_BACKTEST_SNAPSHOTS

from .evaluation import backtest
from .pipeline import TrainConfig, run_training
from .registry import ModelRegistry
from .repository import CsvDealRepository


def _env(name: str, default: str) -> str:
    return os.environ.get(f"G4_{name}", default)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lead-trainer", description="Treina e versiona o modelo de score de deals.")
    p.add_argument("--data-dir", default=_env("DATA_DIR", "data"))
    p.add_argument("--artifact-dir", default=_env("ARTIFACT_DIR", "artifacts"))
    p.add_argument("--db", default=_env("DB_PATH", "var/app.db"))
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="treina, avalia e (se passar no portão) promove uma nova versão")
    t.add_argument("--reference-date", help="YYYY-MM-DD (padrão: último dia dos dados)")
    t.add_argument("--snapshots", default=",".join(DEFAULT_BACKTEST_SNAPSHOTS), help="datas do backtest, separadas por vírgula")
    t.add_argument("--skip-backtest", action="store_true")
    t.add_argument("--force", action="store_true", help="promove mesmo que o portão rejeite")

    e = sub.add_parser("evaluate", help="só o backtest; não grava nada")
    e.add_argument("--snapshots", default=",".join(DEFAULT_BACKTEST_SNAPSHOTS))

    sub.add_parser("list", help="lista as versões registradas")
    pr = sub.add_parser("promote", help="promove manualmente uma versão já treinada (ex.: rollback)")
    pr.add_argument("version")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "train":
        cfg = TrainConfig(Path(args.data_dir), Path(args.artifact_dir), Path(args.db), args.reference_date,
                          [s for s in args.snapshots.split(",") if s], args.skip_backtest, args.force)
        result = run_training(cfg)
    elif args.cmd == "evaluate":
        df = CsvDealRepository(args.data_dir).load()
        result = backtest(df, [pd.Timestamp(s) for s in args.snapshots.split(",") if s])
    elif args.cmd == "list":
        result = ModelRegistry(args.artifact_dir, args.db).list()
    else:
        ModelRegistry(args.artifact_dir, args.db).promote(args.version)
        result = {"version": args.version, "status": "active"}
    print(json.dumps(result, ensure_ascii=False, default=str))   # última linha = resultado (lida pela API)
    return 0   # versão rejeitada pelo portão não é erro: o resultado ("status") conta o que aconteceu


if __name__ == "__main__":
    sys.exit(main())
