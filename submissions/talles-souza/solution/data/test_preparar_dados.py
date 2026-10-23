"""Testes de contagem da camada de dados, contra os números medidos na E2.

Uso: CRM_DADOS=<pasta crm-sales-predictive-analytics> python -m pytest test_preparar_dados.py
"""
import os
from pathlib import Path

import pytest

from preparar_dados import FORMATO, carregar, gravar, para_json, preparar, vendedores

PASTA = Path(os.environ.get("CRM_DADOS", ""))
pytestmark = pytest.mark.skipif(not (PASTA / "sales_pipeline.csv").exists(), reason="defina CRM_DADOS")


@pytest.fixture(scope="module")
def tabelas():
    return carregar(PASTA)


@pytest.fixture(scope="module")
def dados(tabelas):
    return preparar(tabelas)


def test_nao_perde_nem_duplica_deals(dados):
    df, _ = dados
    assert len(df) == 8800
    assert df.opportunity_id.is_unique


def test_estagios(dados):
    df, _ = dados
    assert df.deal_stage.value_counts().to_dict() == {"Won": 4238, "Lost": 2473, "Engaging": 1589, "Prospecting": 500}
    assert int(df.aberto.sum()) == 2089


def test_referencia_e_o_ultimo_fechamento(dados):
    _, ref = dados
    assert ref.strftime("%Y-%m-%d") == "2017-12-31"


def test_todo_produto_casa_com_o_catalogo(dados):
    df, _ = dados
    assert df.sales_price.notna().all()
    assert int(df.produto_normalizado.sum()) > 0          # "GTXPro" existia e foi normalizado
    assert "GTXPro" not in set(df["product"])


def test_todo_vendedor_tem_manager_e_escritorio(dados):
    df, _ = dados
    assert df.manager.notna().all() and df.regional_office.notna().all()


def test_lacunas_marcadas(dados):
    df, _ = dados
    sem_conta = df[df.sem_conta].deal_stage.value_counts().to_dict()
    assert sem_conta == {"Engaging": 1088, "Prospecting": 337}
    assert int(df[df.deal_stage == "Prospecting"].sem_engage_date.sum()) == 500
    assert not df[df.deal_stage != "Prospecting"].sem_engage_date.any()


def test_idade_so_nos_abertos_com_engajamento(dados):
    df, _ = dados
    eng = df[df.deal_stage == "Engaging"]
    assert eng.idade_dias.notna().all()
    assert (int(eng.idade_dias.min()), int(eng.idade_dias.max())) == (9, 423)
    assert df[~df.aberto].idade_dias.isna().all()
    assert df[df.deal_stage == "Prospecting"].idade_dias.isna().all()


def test_duracao_maxima_dos_fechados(dados):
    df, _ = dados
    assert int(df.duracao_dias.max()) == 138


def test_json_serializavel(dados, tabelas):
    df, ref = dados
    j = para_json(df, ref, tabelas["team"])
    assert j["total"] == 8800 and j["referencia"] == "2017-12-31"
    assert all(v is None or not (isinstance(v, float) and v != v) for v in j["deals"][0].values())  # sem NaN


def test_vendedores_sao_os_35_do_time_com_5_sem_negocio(dados, tabelas):
    df, _ = dados
    v = vendedores(tabelas["team"])
    assert len(v) == 35
    assert set(v[0]) == {"sales_agent", "manager", "regional_office"}
    assert [x["sales_agent"] for x in v] == sorted(x["sales_agent"] for x in v)
    sem_negocio = {x["sales_agent"] for x in v} - set(df.sales_agent)
    assert len(sem_negocio) == 5


def test_grava_formato_e_checksum(dados, tabelas, tmp_path):
    import hashlib
    df, ref = dados
    saida = tmp_path / "deals.json"
    hash_hex = gravar(df, ref, tabelas["team"], saida)
    assert hashlib.sha256(saida.read_bytes()).hexdigest() == hash_hex
    assert (tmp_path / "deals.json.sha256").read_text(encoding="utf-8") == f"{hash_hex}  deals.json\n"
    j = para_json(df, ref, tabelas["team"])
    assert j["formato"] == FORMATO == 2
    assert len(j["vendedores"]) == 35
