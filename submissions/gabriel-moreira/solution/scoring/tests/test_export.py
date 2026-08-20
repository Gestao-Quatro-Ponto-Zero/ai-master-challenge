"""Requirement "Exportação do dataset processado" — CSV consolidado."""

import pandas as pd

from scoring.export import EXPORT_COLUMNS, export_processed_dataset


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
