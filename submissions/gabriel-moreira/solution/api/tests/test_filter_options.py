"""Requirements "Opções de filtro" e "Exportação de identificadores
filtrados" (task 3.18)."""

import csv
import io


def test_filter_options_returns_hierarchy_and_age_extremes(client):
    resp = client.get("/filter-options")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["vendedores"]) > 0
    assert len(body["gerentes"]) > 0
    assert len(body["escritorios"]) > 0
    assert len(body["produtos"]) > 0
    assert body["idade_min"] is not None
    assert body["idade_max"] is not None
    assert body["idade_min"] <= body["idade_max"]


def test_filter_options_vendedor_associado_a_gerente_e_escritorio(client):
    resp = client.get("/filter-options")
    body = resp.json()

    vendedor = next(v for v in body["vendedores"] if v["nome"] == "Anna Snelling")
    assert vendedor["manager"] == "Dustin Brinkmann"
    assert vendedor["regional_office"] == "Central"

    gerente = next(g for g in body["gerentes"] if g["nome"] == "Dustin Brinkmann")
    assert gerente["regional_office"] == "Central"


def test_filter_options_chaining_resolvable_without_new_request(client):
    resp = client.get("/filter-options")
    body = resp.json()

    vendedores_do_gerente = {
        v["nome"] for v in body["vendedores"] if v["manager"] == "Dustin Brinkmann"
    }
    assert vendedores_do_gerente == {
        "Anna Snelling", "Cecily Lampkin", "Versie Hillebrand", "Lajuana Vencill", "Moses Frase",
    }


def test_filter_options_age_extremes_match_open_funnel(client):
    resp = client.get("/filter-options")
    idade_min, idade_max = resp.json()["idade_min"], resp.json()["idade_max"]

    todas_idades: list[float] = []
    deals = client.get("/deals", params={"page_size": 500}).json()
    for page in range(1, deals["total_pages"] + 1):
        pagina = client.get("/deals", params={"page_size": 500, "page": page}).json()
        todas_idades.extend(row["age_days"] for row in pagina["items"] if row["age_days"] is not None)

    assert idade_min == min(todas_idades)
    assert idade_max == max(todas_idades)


def test_export_deal_ids_covers_whole_filtered_slice_not_just_a_page(client):
    resp = client.get("/export/deal-ids", params={"regional_office": "Central"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    reader = csv.DictReader(io.StringIO(resp.text))
    ids_exportados = [row["opportunity_id"] for row in reader]

    listagem = client.get("/deals", params={"regional_office": "Central"}).json()
    assert len(ids_exportados) == listagem["total"]
    assert len(ids_exportados) > listagem["page_size"]  # confirma que passa de uma página


def test_export_deal_ids_without_filter_covers_all_1436(client):
    resp = client.get("/export/deal-ids")
    reader = csv.DictReader(io.StringIO(resp.text))
    assert len(list(reader)) == 1436
