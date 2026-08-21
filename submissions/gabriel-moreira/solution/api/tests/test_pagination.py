"""Requirement "Listagem de oportunidades por estado" — paginação e
ordenação sobre o recorte inteiro, com desempate estável (tasks 3.5, 3.6, 3.7)."""


def test_page_beyond_last_returns_empty_not_404(client):
    resp = client.get("/deals", params={"page": 9999})
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 1436


def test_union_of_all_pages_has_exactly_total_distinct_ids_no_dup_no_gap(client):
    first = client.get("/deals", params={"regional_office": "Central", "page": 1})
    body = first.json()
    total = body["total"]
    total_pages = body["total_pages"]
    page_size = body["page_size"]

    vistos: list[str] = []
    for page in range(1, total_pages + 1):
        resp = client.get("/deals", params={"regional_office": "Central", "page": page})
        vistos.extend(row["opportunity_id"] for row in resp.json()["items"])

    assert len(vistos) == total
    assert len(set(vistos)) == total  # sem repetição entre páginas
    assert (total_pages - 1) * page_size < total <= total_pages * page_size  # sem lacuna


def test_first_page_sorted_by_score_desc_matches_global_top(client):
    page_size = 500
    primeira_pagina = client.get(
        "/deals", params={"sort": "score", "order": "desc", "page_size": page_size, "page": 1}
    ).json()
    total = primeira_pagina["total"]
    total_pages = primeira_pagina["total_pages"]

    todas_as_pontuacoes: list[float] = []
    for page in range(1, total_pages + 1):
        pagina = client.get(
            "/deals",
            params={"sort": "score", "order": "desc", "page_size": page_size, "page": page},
        )
        todas_as_pontuacoes.extend(row["score"] for row in pagina.json()["items"])

    assert len(todas_as_pontuacoes) == total
    topo_esperado = sorted(todas_as_pontuacoes, reverse=True)[:page_size]
    topo_obtido = [row["score"] for row in primeira_pagina["items"]]
    assert sorted(topo_obtido, reverse=True) == sorted(topo_esperado, reverse=True)


def test_no_opportunity_appears_on_two_adjacent_pages_with_ties(client):
    pagina_1 = client.get("/deals", params={"sort": "score", "order": "desc", "page": 1}).json()
    pagina_2 = client.get("/deals", params={"sort": "score", "order": "desc", "page": 2}).json()

    ids_1 = {row["opportunity_id"] for row in pagina_1["items"]}
    ids_2 = {row["opportunity_id"] for row in pagina_2["items"]}
    assert ids_1.isdisjoint(ids_2)
