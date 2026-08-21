"""Task 4.6 — sugestão de redistribuição para vendedor sobrecarregado."""

from scoring.carga import compute_carga, index_by_agent_estado, overloaded_pairs
from scoring.fit import build_fit_context, eligible_pool, suggest_candidate, vendors_with_history
from scoring.pipeline import fechados_calibracao


def _setup(scored_pipeline):
    sp = scored_pipeline
    carga = compute_carga(sp.scored)
    carga_idx = index_by_agent_estado(carga)
    fit_ctx = build_fit_context(sp.dataset, fechados_calibracao(sp.dataset))
    return sp, carga, carga_idx, fit_ctx


def test_candidato_sempre_do_mesmo_escritorio(scored_pipeline):
    sp, carga, carga_idx, fit_ctx = _setup(scored_pipeline)
    overloaded = overloaded_pairs(carga)
    for item in overloaded:
        deal = sp.scored[
            (sp.scored["sales_agent"] == item.sales_agent) & (sp.scored["estado"] == item.estado)
        ].iloc[0]
        candidato = suggest_candidate(
            fit_ctx, carga_idx, item.sales_agent, item.regional_office, item.estado,
            deal["product"], deal.get("sector"),
        )
        if candidato is not None:
            assert fit_ctx.vendor_office[candidato.sales_agent] == item.regional_office
            assert candidato.sales_agent != item.sales_agent


def test_vendedor_sem_historico_nunca_sugerido(scored_pipeline):
    sp, carga, carga_idx, fit_ctx = _setup(scored_pipeline)
    sem_historico = set(fit_ctx.vendor_office) - vendors_with_history(fit_ctx)
    # neste dataset, todo vendedor em vendor_office já tem histórico —
    # confirma que os 5 sem NENHUMA oportunidade nunca entram nesse dict.
    assert sem_historico == set()

    overloaded = overloaded_pairs(carga)
    for item in overloaded:
        deal = sp.scored[
            (sp.scored["sales_agent"] == item.sales_agent) & (sp.scored["estado"] == item.estado)
        ].iloc[0]
        candidato = suggest_candidate(
            fit_ctx, carga_idx, item.sales_agent, item.regional_office, item.estado,
            deal["product"], deal.get("sector"),
        )
        if candidato is not None:
            assert candidato.sales_agent in vendors_with_history(fit_ctx)


def test_ausencia_de_candidato_quando_pool_esgota(scored_pipeline):
    """Constrói um cenário sintético onde todos os elegíveis do escritório
    estão sobrecarregados no ESTADO — a sugestão deve reportar None, sem
    cruzar escritório."""
    from scoring.carga import CargaVendedorEstado

    sp, carga, carga_idx, fit_ctx = _setup(scored_pipeline)
    office = "Central"
    estado = "qualificar"
    agentes_central = [v for v, o in fit_ctx.vendor_office.items() if o == office]

    carga_sintetica = dict(carga_idx)
    for agente in agentes_central:
        carga_sintetica[(agente, estado)] = CargaVendedorEstado(
            sales_agent=agente, regional_office=office, estado=estado,
            contagem=50, media_escritorio=10.0, razao=5.0, sobrecarregado=True,
        )

    candidato = suggest_candidate(
        fit_ctx, carga_sintetica, agentes_central[0], office, estado, "GTX Pro", None
    )
    assert candidato is None


def test_pool_nunca_cruza_escritorio(scored_pipeline):
    sp, carga, carga_idx, fit_ctx = _setup(scored_pipeline)
    pool = eligible_pool(fit_ctx, carga_idx, "Darcel Schlecht", "Central", "qualificar")
    for candidate in pool:
        assert fit_ctx.vendor_office[candidate] == "Central"


def test_sugestao_nao_altera_dono_da_oportunidade(scored_pipeline):
    """A sugestão é informativa — o `sales_agent` da oportunidade no
    dataset processado permanece o vendedor original."""
    sp = scored_pipeline
    original_agents = sp.scored["sales_agent"].copy()
    _setup(scored_pipeline)
    assert (sp.scored["sales_agent"] == original_agents).all()
