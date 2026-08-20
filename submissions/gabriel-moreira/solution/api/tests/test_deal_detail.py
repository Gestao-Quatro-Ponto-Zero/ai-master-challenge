"""Requirement "Detalhe de uma oportunidade" (task 3.17): com conta, sem
conta, inexistente e com data de referência."""


def _find_opportunity(client, *, has_account: bool, deal_stage: str | None = None) -> dict:
    page = 1
    while True:
        resp = client.get("/deals", params={"page_size": 500, "page": page})
        body = resp.json()
        for row in body["items"]:
            if (row["account"] is not None) != has_account:
                continue
            if deal_stage is not None and row["deal_stage"] != deal_stage:
                continue
            return row
        if page >= body["total_pages"]:
            raise AssertionError("nenhuma oportunidade encontrada com o critério pedido")
        page += 1


def test_detail_with_account_returns_full_ficha(client):
    row = _find_opportunity(client, has_account=True)
    resp = client.get(f"/deals/{row['opportunity_id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conta"]["vinculada"] is True
    assert body["conta"]["sector"] is not None
    assert body["conta"]["revenue"] is not None
    assert body["conta"]["employees"] is not None
    assert body["conta"]["year_established"] is not None
    assert body["conta"]["office_location"] is not None
    assert 2 <= len(body["plano_de_acao_passos"]) <= 4


def test_detail_without_account_returns_200_with_null_fields(client):
    row = _find_opportunity(client, has_account=False)
    resp = client.get(f"/deals/{row['opportunity_id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conta"]["vinculada"] is False
    assert body["conta"]["sector"] is None
    assert body["conta"]["revenue"] is None
    assert body["conta"]["employees"] is None
    assert body["conta"]["year_established"] is None
    assert body["conta"]["office_location"] is None


def test_detail_nonexistent_returns_404(client):
    resp = client.get("/deals/ID-QUE-NAO-EXISTE-NUNCA")
    assert resp.status_code == 404


def test_detail_with_as_of_recalculates_age_and_state(client):
    row = _find_opportunity(client, has_account=True, deal_stage="Engaging")

    resp_default = client.get(f"/deals/{row['opportunity_id']}")
    resp_early = client.get(f"/deals/{row['opportunity_id']}", params={"as_of": "2017-06-30"})
    assert resp_default.status_code == 200
    assert resp_early.status_code == 200

    assert resp_default.json()["age_days"] != resp_early.json()["age_days"]
