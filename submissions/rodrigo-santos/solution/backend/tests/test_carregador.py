"""Testes da carga e limpeza dos dados."""

from app.dados.carregador import CONTA_NAO_INFORMADA, ETAPAS_ABERTAS, carregar_deals


def test_carrega_todos_os_deals():
    assert len(carregar_deals()) == 8800


def test_corrige_nome_de_produto():
    produtos = set(carregar_deals()["product"])
    assert "GTXPro" not in produtos
    assert "GTX Pro" in produtos


def test_todo_deal_tem_preco_e_time():
    deals = carregar_deals()
    assert deals["sales_price"].notna().all()
    assert deals["manager"].notna().all()


def test_corrige_setor_com_erro_de_digitacao():
    setores = set(carregar_deals()["sector"].dropna())
    assert "technolgy" not in setores
    assert "technology" in setores


def test_deals_sem_conta_sao_marcados():
    deals = carregar_deals()
    sem_conta = deals[~deals["conta_informada"]]
    assert (sem_conta["account"] == CONTA_NAO_INFORMADA).all()
    # Nos dados de origem, só deals abertos ficam sem conta.
    assert sem_conta["deal_stage"].isin(ETAPAS_ABERTAS).all()
