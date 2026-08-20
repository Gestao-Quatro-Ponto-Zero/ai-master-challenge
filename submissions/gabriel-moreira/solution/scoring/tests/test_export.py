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


def test_export_confianca_label_and_plano_de_acao_columns_present(scored_pipeline, tmp_path):
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    written = pd.read_csv(output_path)
    assert "confianca_label" in written.columns
    assert "plano_de_acao" in written.columns
    assert "plano_de_acao_passos" in written.columns
    assert written["confianca_label"].notna().all()
    assert written["plano_de_acao"].notna().all()


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
