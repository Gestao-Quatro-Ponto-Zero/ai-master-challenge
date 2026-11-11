import json
import shutil

import pandas as pd
import pytest

from drift import aprendido, conferir, main

HOJE = "2018-01-01"


@pytest.fixture
def guardado(dados_dir, config):
    return aprendido(dados_dir, config, pd.Timestamp(HOJE))


def _copia(dados_dir, destino):
    destino.mkdir(parents=True, exist_ok=True)
    for f in ["sales_pipeline.csv", "products.csv", "sales_teams.csv", "accounts.csv"]:
        shutil.copy(dados_dir / f, destino / f)
    return destino


def _pipeline(pasta):
    return pd.read_csv(pasta / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])


def test_nada_mudou_com_os_mesmos_csvs(dados_dir, config, guardado):
    r = conferir(dados_dir, guardado, config)
    assert r["mudou"] is False


def test_deal_ganho_aos_200_dias_muda_o_ciclo(tmp_path, dados_dir, config, guardado):
    pasta = _copia(dados_dir, tmp_path)
    p = _pipeline(pasta)
    i = p[(p.deal_stage == "Won") & (p.engage_date < "2017-06-01")].index[0]
    p.loc[i, "close_date"] = p.loc[i, "engage_date"] + pd.Timedelta(days=200)
    p.to_csv(pasta / "sales_pipeline.csv", index=False)

    r = conferir(pasta, guardado, config)
    mudaram = [x["item"] for x in r["itens"] if x["mudou"]]
    assert r["mudou"] and "ciclo_max" in mudaram


def test_fechamentos_depois_do_prazo_desligam_a_regra(tmp_path, dados_dir, config, guardado):
    pasta = _copia(dados_dir, tmp_path)
    p = _pipeline(pasta)
    ids = p[(p.deal_stage == "Won") & (p.engage_date >= "2017-06-01") & (p.engage_date <= "2017-06-30")].index[:8]
    p.loc[ids, "close_date"] = pd.Timestamp("2017-10-05")
    p.to_csv(pasta / "sales_pipeline.csv", index=False)

    r = conferir(pasta, guardado, config)
    item = next(x for x in r["itens"] if x["item"] == "usa_prazo_trimestre")
    assert item["mudou"] and item["novo"] is False
    assert "fila" in item["mensagem"]


def test_main_devolve_1_quando_algo_muda_e_0_quando_nao(tmp_path, dados_dir, config, guardado):
    janela = tmp_path / "janela.json"
    janela.write_text(json.dumps(guardado), encoding="utf-8")
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")

    assert main(["--dados", str(dados_dir), "--janela", str(janela), "--config", str(cfg)]) == 0

    pasta = _copia(dados_dir, tmp_path / "alterado")
    p = _pipeline(pasta)
    i = p[(p.deal_stage == "Won") & (p.engage_date < "2017-06-01")].index[0]
    p.loc[i, "close_date"] = p.loc[i, "engage_date"] + pd.Timedelta(days=200)
    p.to_csv(pasta / "sales_pipeline.csv", index=False)

    assert main(["--dados", str(pasta), "--janela", str(janela), "--config", str(cfg)]) == 1
