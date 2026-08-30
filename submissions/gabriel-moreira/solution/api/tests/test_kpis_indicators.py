"""Requirement "Indicadores agregados do funil" (task 3.19): filtro
derivado (estado) só afeta o funil aberto; filtro de organização afeta
ambas as famílias de indicador."""


def test_derived_filter_estado_changes_open_funnel_tiles_not_historical(client):
    sem_filtro = client.get("/kpis").json()
    com_filtro = client.get("/kpis", params={"estado": "prioritize"}).json()

    assert com_filtro["total_oportunidades"] != sem_filtro["total_oportunidades"]
    assert com_filtro["receita_ganha"] == sem_filtro["receita_ganha"]
    assert com_filtro["maior_negocio_fechado"] == sem_filtro["maior_negocio_fechado"]


def test_org_filter_changes_both_open_and_historical_tiles(client):
    sem_filtro = client.get("/kpis").json()
    com_filtro = client.get("/kpis", params={"sales_agent": "Anna Snelling"}).json()

    assert com_filtro["total_oportunidades"] != sem_filtro["total_oportunidades"]
    assert com_filtro["receita_ganha"] != sem_filtro["receita_ganha"]
