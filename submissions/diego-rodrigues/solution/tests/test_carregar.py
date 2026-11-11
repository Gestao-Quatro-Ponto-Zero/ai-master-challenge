import shutil

import pandas as pd

from motor.carregar import carregar, recortar


def test_apelido_de_produto_casa_com_catalogo(dados):
    assert dados.qualidade["apelidos_de_produto"] == {"GTXPro": "GTX Pro"}
    assert dados.qualidade["produtos_sem_par"] == []
    assert dados.pipeline.valor_tabela.isna().sum() == 0
    assert (dados.pipeline.produto_crm != dados.pipeline.produto).sum() == 1480


def test_qualidade_do_export(dados):
    q = dados.qualidade
    assert q["total_linhas"] == 8800 and q["abertos_sem_conta"] == 1425
    assert q["prospecting_sem_data"] == 500
    assert q["maior_data"] == "2017-12-31" and q["primeiro_fechamento"] == "2017-03-01"
    assert q["setores_corrigidos"] == {"technolgy": "technology"}
    assert (q["vendedores_cadastro"], q["vendedores_com_deal"], q["vendedores_com_deal_aberto"]) == (35, 30, 27)


def test_produto_desconhecido_vai_para_qualidade(tmp_path, dados_dir):
    for f in ["sales_pipeline.csv", "products.csv", "sales_teams.csv", "accounts.csv"]:
        shutil.copy(dados_dir / f, tmp_path / f)

    pipeline = pd.read_csv(tmp_path / "sales_pipeline.csv")
    nova = pipeline.iloc[0:1].copy()
    nova["product"] = "ZZZ Novo"
    nova["deal_stage"] = "Engaging"
    nova["close_date"] = None
    nova["close_value"] = None
    pd.concat([pipeline, nova], ignore_index=True).to_csv(tmp_path / "sales_pipeline.csv", index=False)

    d = carregar(tmp_path)
    assert d.qualidade["produtos_sem_par"] == ["ZZZ Novo"]
    assert d.pipeline.loc[d.pipeline.produto_crm == "ZZZ Novo", "valor_tabela"].isna().all()


def test_recortar_nao_vaza_futuro(dados):
    r = recortar(dados, pd.Timestamp("2017-07-01"))
    assert r.pipeline.close_date.max() < pd.Timestamp("2017-07-01")
    assert r.pipeline.engage_date.max() < pd.Timestamp("2017-07-01")
    assert r.pipeline.close_value[r.pipeline.close_date.isna()].isna().all()
    assert len(r.pipeline[r.pipeline.deal_stage == "Prospecting"]) == 0


def test_recortar_no_fim_do_export_preserva_tudo(dados, hoje):
    r = recortar(dados, hoje)
    assert len(r.pipeline) == 8800
    assert (r.pipeline.deal_stage == "Prospecting").sum() == 500
