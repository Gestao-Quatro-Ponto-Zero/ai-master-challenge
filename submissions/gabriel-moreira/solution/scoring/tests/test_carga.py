"""Task 2.4 — motor de carga por vendedor e ESTADO."""

from scoring.carga import compute_carga, index_by_agent_estado, overloaded_pairs


def test_darcel_schlecht_central_qualificar_e_sobrecarga(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    by_key = index_by_agent_estado(carga)
    item = by_key[("Darcel Schlecht", "qualificar")]
    assert item.regional_office == "Central"
    assert item.contagem == 92
    assert round(item.media_escritorio, 2) == 44.30
    assert item.sobrecarregado is True


def test_piso_absoluto_suprime_falso_alarme(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    by_key = index_by_agent_estado(carga)
    item = by_key[("Niesha Huffines", "prioritize")]
    assert item.contagem == 1
    assert round(item.media_escritorio, 2) == 0.10
    assert item.sobrecarregado is False


def test_west_acompanhar_media_inclui_vendedores_sem_deals_no_estado(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    west_acompanhar = [c for c in carga if c.regional_office == "West" and c.estado == "acompanhar"]
    assert len(west_acompanhar) == 10
    assert round(west_acompanhar[0].media_escritorio, 2) == 5.80


def test_abaixo_do_corte_de_razao_nao_e_sobrecarga(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    abaixo = [
        c
        for c in carga
        if c.media_escritorio > 0
        and c.contagem < 1.5 * c.media_escritorio
        and c.contagem >= 5
    ]
    assert abaixo
    assert all(not c.sobrecarregado for c in abaixo)


def test_total_de_pares_e_oportunidades_sobrecarregadas(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    overloaded = overloaded_pairs(carga)
    assert len(overloaded) == 12
    assert len({c.sales_agent for c in overloaded}) == 8
    assert sum(c.contagem for c in overloaded) == 227


def test_revisao_lote_excluida_da_carga(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    assert all(c.estado != "revisao_lote" for c in carga)


def test_escritorio_vem_de_sales_teams_nao_de_conta(scored_pipeline):
    carga = compute_carga(scored_pipeline.scored)
    by_agent = {c.sales_agent: c.regional_office for c in carga}
    scored = scored_pipeline.scored
    real_office = (
        scored[["sales_agent", "regional_office"]].dropna().drop_duplicates("sales_agent")
        .set_index("sales_agent")["regional_office"].to_dict()
    )
    for agent, office in by_agent.items():
        assert office == real_office[agent]
