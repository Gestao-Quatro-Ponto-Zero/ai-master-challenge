import json

from build import construir


def test_build_grava_e_soma(tmp_path, dados_dir, config):
    construir(dados_dir, config, saida=tmp_path, hoje="2018-01-01")
    j = json.loads((tmp_path / "scored.json").read_text())
    assert len(j["deals"]) == 2089 and len(j["vendedores"]) == 35
    assert sum(v["por_fila"]["encerrar"] for v in j["vendedores"]) == 1474
    assert round(j["time"]["pct_vencido"], 3) == 0.736
    assert j["time"]["valor_vivo"] == 235930 and j["semana_do_trimestre"] == 1
    assert [v for v in j["vendedores"] if v["vendedor"] == "Carl Lin"][0]["tem_deal"] is False


def test_build_e_deterministico(tmp_path, dados_dir, config):
    a = construir(dados_dir, config, saida=tmp_path / "a", hoje="2018-01-01")
    b = construir(dados_dir, config, saida=tmp_path / "b", hoje="2018-01-01")
    assert (tmp_path / "a/hash.txt").read_text() == (tmp_path / "b/hash.txt").read_text()
    assert a["hash"] == b["hash"]
