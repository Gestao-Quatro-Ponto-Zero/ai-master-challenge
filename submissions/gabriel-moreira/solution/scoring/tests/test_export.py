"""Requirement "Exportação do dataset processado" — CSV consolidado."""

import pandas as pd

from scoring.export import EXPORT_COLUMNS, PASSOS_SEPARADOR, export_processed_dataset


def test_export_writes_all_2089_open_opportunities(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    assert len(written) == 2089
    for col in EXPORT_COLUMNS:
        assert col in written.columns


def test_export_includes_opportunities_without_account(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    sem_conta = written[written["account"].isna()]
    assert len(sem_conta) == 1425
    assert sem_conta["prioridade"].notna().all()
    assert sem_conta["estado"].notna().all()


def test_export_confianca_columns_present(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    for col in ("confianca", "completude", "suporte", "sem_precedente"):
        assert col in written.columns
        assert written[col].notna().all()
    assert "plano_de_acao" in written.columns
    assert written["plano_de_acao"].notna().all()


def test_export_score_reproduces_prioridade(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    produto = written["p_hat"] * written["valor"] * written["urgencia"]
    assert (produto.round(2) - written["prioridade"].round(2)).abs().max() < 0.02


def test_export_plano_de_acao_passos_order_recoverable(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)

    original_by_id = dict(
        zip(scored_pipeline.scored["opportunity_id"], scored_pipeline.scored["plano_de_acao_passos"])
    )

    for _, row in written.iterrows():
        original = original_by_id[row["opportunity_id"]]
        recuperado = tuple(row["plano_de_acao_passos"].split(PASSOS_SEPARADOR))
        assert recuperado == original


def test_export_score_fatores_order_recoverable(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)

    original_by_id = dict(
        zip(scored_pipeline.scored["opportunity_id"], scored_pipeline.scored["score_fatores"])
    )

    for _, row in written.iterrows():
        original = original_by_id[row["opportunity_id"]]
        recuperado = row["score_fatores"].split(PASSOS_SEPARADOR)
        assert recuperado == original


def test_export_revisao_lote_all_past_censura_boundary(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    revisao = written[written["estado"] == "revisao_lote"]
    assert (revisao["age_days"] > 138).all()
    assert (revisao["deal_stage"] != "Prospecting").all()
