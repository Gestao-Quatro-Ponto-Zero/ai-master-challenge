#!/usr/bin/env python3
"""Churn Platform — Entry Point (SPEC-1).

Uso:
  python run.py --config config/ravenstack.yaml --output ./output
  python run.py --help
"""

import logging
import sys
from pathlib import Path

import click

from churn_platform.pipeline import loader, cleaner, merger, validator
from churn_platform.datamodel import account_view as dv
from churn_platform.analysis import segmentation, descriptive
from churn_platform.scoring import health_score
from churn_platform.report import html_report
from churn_platform.predictive import train as pred_train
from churn_platform.predictive import predict as pred_predict
from churn_platform.predictive import explain as pred_explain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("churn")


def _load_yaml(path: str) -> dict:
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


@click.command()
@click.option("--config", default="config/ravenstack.yaml", help="Caminho do arquivo de config YAML")
@click.option("--output", default="output", help="Diretório de saída")
@click.option("--stage", default="all", help="Estágio: all | pipeline | analyze | score | predict | report")
@click.option("--verbose", is_flag=True, help="Log detalhado")
def run(config: str, output: str, stage: str, verbose: bool):
    """Churn Platform — Diagnóstico, Predição e Prescrição de Churn."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cfg = _load_yaml(config)
    base_dir = str(Path(config).resolve().parent.parent)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)

    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  Churn Platform v0.1.0                       ║")
    logger.info("║  SPEC-Driven Churn Diagnostic Engine         ║")
    logger.info("╚══════════════════════════════════════════════╝")
    logger.info("Config: %s", config)
    logger.info("Output: %s", out.resolve())

    # ── STAGE 1: Pipeline ──────────────────────────────────────
    if stage in ("all", "pipeline"):
        logger.info("")
        logger.info("━" * 50)
        logger.info("STAGE 1: Pipeline de Dados (SPEC-2)")

        sources = loader.load_all_sources(cfg, base_dir)
        sources = cleaner.run(sources)

        schemas = _load_yaml("config/schemas/ravenstack_schema.yaml")
        dqr = validator.run(sources, schemas, str(out))

        merged = merger.run(sources, cfg.get("merges", {}))
        df = dv.build(sources, merged)

        df.to_parquet(out / "account_view.parquet", index=False)
        logger.info("Account View salva: %s", out / "account_view.parquet")
        logger.info("Pipeline concluído: %s contas, %s colunas", len(df), len(df.columns))
    else:
        if (out / "account_view.parquet").exists():
            import pandas as pd
            df = pd.read_parquet(out / "account_view.parquet")
            logger.info("Account View carregada do cache: %s", out / "account_view.parquet")
        else:
            logger.error("Account View não encontrada. Execute o stage 'pipeline' primeiro.")
            sys.exit(1)

    # ── STAGE 2: Análise ───────────────────────────────────────
    if stage in ("all", "analyze"):
        logger.info("")
        logger.info("━" * 50)
        logger.info("STAGE 2: Análise (SPEC-4)")

        stats = descriptive.overall_stats(df)
        seg_results = segmentation.run(df, cfg)
        desc_results = descriptive.run(df, cfg)

        with open(out / "analysis_results.json", "w") as f:
            import json
            json.dump({
                "overall_stats": stats,
                "segments": seg_results,
                "descriptive": desc_results,
            }, f, indent=2, default=str)
        logger.info("Análise salva: %s", out / "analysis_results.json")

    # ── STAGE 3: Scoring ───────────────────────────────────────
    if stage in ("all", "score"):
        logger.info("")
        logger.info("━" * 50)
        logger.info("STAGE 3: Health Score (SPEC-5)")

        scored = health_score.run(df, cfg)
        scored.to_parquet(out / "scored_accounts.parquet", index=False)

        # Summarize
        tier_dist = scored["health_tier"].value_counts()
        for tier in ["Critical", "At Risk", "Neutral", "Healthy", "Champion"]:
            n = tier_dist.get(tier, 0)
            logger.info("  %-12s: %s contas", tier, n)

    # ── STAGE 4: Predict ───────────────────────────────────────
    if stage in ("all", "predict"):
        logger.info("")
        logger.info("━" * 50)
        logger.info("STAGE 4: Modelagem Preditiva (SPEC-6)")

        merged_df = df.merge(
            scored[["account_id", "health_score", "pillar_usage", "pillar_support", "pillar_engagement", "pillar_financial"]],
            on="account_id",
        )
        pred_train.train_model(merged_df, output_dir=str(out))
        pred_results = pred_predict.predict_churn(merged_df, output_dir=str(out))
        pred_results.to_parquet(out / "predictions.parquet", index=False)

        pred_explain.explain_model(merged_df, output_dir=str(out), top_n=50)

        high_risk = pred_results[pred_results["churn_risk_label"] == "High"]
        logger.info("  Alto risco: %s contas", len(high_risk))
        logger.info("  Predições salvas: %s", out / "predictions.parquet")

    # ── STAGE 5: Report ────────────────────────────────────────
    if stage in ("all", "report"):
        logger.info("")
        logger.info("━" * 50)
        logger.info("STAGE 4: Relatório (SPEC-10)")

        import json
        with open(out / "analysis_results.json") as f:
            analysis_data = json.load(f)

        report_path = html_report.build_report(
            account_view=df,
            stats=analysis_data["overall_stats"],
            segments=analysis_data["segments"],
            descriptive=analysis_data["descriptive"],
            scored=scored if "scored" in dir() else df,
            output_path=str(out / "report.html"),
        )
        logger.info("")
        logger.info("✓ Pipeline completo!")
        logger.info("  Relatório: %s", report_path)
        logger.info("  Dados:     %s", out / "account_view.parquet")

    logger.info("")
    logger.info("Done.")


if __name__ == "__main__":
    run()
