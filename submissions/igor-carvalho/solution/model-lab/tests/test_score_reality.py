"""Teste de realidade do score. Rode sempre que entrarem dados novos:  pytest -q tests/
Cada critério é um teste separado: o relatório mostra exatamente o que passou e o que falhou.
Não altera o backend: usa cópias dos CSVs num diretório temporário e o código original só para leitura."""
from __future__ import annotations

import os

import pandas as pd
import pytest

from model_lab import backtest_real, simulate
from model_lab.backend import source_data_dir
from model_lab.mockgen import MockWorld
from model_lab.verdict import CRITERIA
from lead_trainer.repository import CsvDealRepository

DAYS = int(os.environ.get("G4_LAB_DAYS", "7"))


@pytest.fixture(scope="session")
def sim(tmp_path_factory):
    return simulate.run(tmp_path_factory.mktemp("ws"), days=DAYS, log=lambda *a: None)


@pytest.fixture(scope="session")
def backtest():
    df = CsvDealRepository(source_data_dir()).load()
    return backtest_real.summarize(backtest_real.run(df, log=lambda *a: None))


# ------------------------------------------------------------------ mocks seguem a estrutura real
def test_mock_preserva_estrutura(tmp_path):
    real = pd.read_csv(source_data_dir() / "sales_pipeline.csv", dtype=str)
    w = MockWorld(source_data_dir(), seed=1)
    for _ in range(2):
        w.step()
    w.write(tmp_path)
    mock = pd.read_csv(tmp_path / "sales_pipeline.csv", dtype=str)
    assert list(mock.columns) == list(real.columns)
    assert set(mock["deal_stage"]) <= set(real["deal_stage"])
    assert set(mock["product"]) <= set(real["product"])
    assert set(mock["sales_agent"]) <= set(real["sales_agent"])
    assert mock["opportunity_id"].is_unique and len(mock) > len(real)
    (tmp_path / "sales_teams.csv").write_bytes((source_data_dir() / "sales_teams.csv").read_bytes())
    (tmp_path / "products.csv").write_bytes((source_data_dir() / "products.csv").read_bytes())
    CsvDealRepository(tmp_path).load()        # passa na validação do próprio backend


# ------------------------------------------------------------------ rotina diária
def test_dados_e_backend_intactos(sim):
    assert sim["source_untouched"], "os CSVs de origem mudaram durante o teste"


def test_retreino_diario_roda_todos_os_dias(sim):
    d = sim["daily"]
    assert len(d) == DAYS + 1
    assert d["status"].isin(["active", "rejected"]).all()
    assert d["auc_backtest"].notna().all()


def test_regras_de_negocio(sim):
    d = sim["daily"]
    assert d["regra_zumbi_sem_score"].all()
    assert d["regra_score_0_100"].all()
    assert d["regra_prospecting_sem_score"].all()


def test_score_estavel_entre_dias(sim):
    psis = sim["daily"]["psi_score_vs_ontem"].dropna()
    assert (psis <= CRITERIA["psi_max"]).all(), psis.tolist()


# ------------------------------------------------------------------ o score condiz com a realidade?
def test_score_acompanha_receita_real_30d(sim):
    rho = sim["daily"]["spearman_atual_vs_verdade"].mean()
    assert rho >= CRITERIA["spearman_min"], f"correlação score x receita real em 30d = {rho:.2f}"


def test_score_alto_nao_e_deal_parado(sim):
    """Falha com o modelo atual (achado da análise): deals parados mantêm score >= 80."""
    d = sim["daily"]
    share = d["score>=80_parados(>p90)"].sum() / max(d["score>=80_total"].sum(), 1)
    assert share <= CRITERIA["stale_in_top_max"], f"{share:.0%} dos deals com score >= 80 estão parados"


# ------------------------------------------------------------------ desafiante (só informa a decisão)
@pytest.mark.slow
def test_desafiante_captura_mais_receita(backtest):
    now = backtest.loc["atual_score_lista", "rev_capture_top20"]
    new = backtest.loc["novo_receita_30d", "rev_capture_top20"]
    assert new / now - 1 >= CRITERIA["challenger_gain_min"], f"ganho {new / now - 1:.1%}"


@pytest.mark.slow
def test_desafiante_nao_prioriza_parados(backtest):
    assert backtest.loc["novo_receita_30d", "stale_share_top20"] <= backtest.loc["atual_score_lista", "stale_share_top20"]
    assert backtest.loc["novo_receita_30d", "zombie_share_top20"] <= 0.01
