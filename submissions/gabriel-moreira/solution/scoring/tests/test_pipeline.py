"""Pipeline de ponta a ponta — SCORE/CONFIANÇA/ESTADO sobre o funil real."""

import dataclasses

from scoring.pipeline import build_scoring_context, score_row
from scoring.reference import build_reference_distribution


def test_reference_scenario_gtx_plus_pro_upper_122_dias(scored_pipeline):
    """PRIORIDADE sobe com a remoção do expurgo de 200 dias: p̂_produto
    passa a valer a taxa global sobre desfecho observado (0,632) em vez da
    taxa deprimida pela calibração expurgada — BREAKING, ver
    docs/decisions-log.md, entrada 2026-08-29."""
    sp = scored_pipeline
    r = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Plus Pro", stage="Engaging", age_days=122,
        has_account=True, porte="Upper", has_sector=True, has_team=True,
    )
    assert abs(r["prioridade"] - 4405.17) < 5.00


def test_reference_scenario_idade_377_dias_sem_precedente(scored_pipeline):
    sp = scored_pipeline
    r = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Plus Pro", stage="Engaging", age_days=377,
        has_account=True, porte="Upper", has_sector=True, has_team=True,
    )
    assert r["p_hat"] == 0.632
    assert r["urgencia"] == 0.15
    assert r["sem_precedente"] is True
    assert r["estado"] == "revisao_lote"


def test_reference_population_has_4238_won_deals(scored_pipeline):
    assert scored_pipeline.ref.n == 4238


def test_stability_priority_and_score_independent_of_open_funnel(scored_pipeline):
    """PRIORIDADE e SCORE não dependem da composição do funil aberto — só
    de constantes fixas e da distribuição de referência histórica de
    negócios ganhos. Remover metade das oportunidades ABERTAS do dataset
    (sem tocar nos negócios fechados) não pode mudar p̂_produto, a
    distribuição de referência, nem os insumos de suporte — e portanto não
    muda PRIORIDADE nem SCORE de uma oportunidade que não mudou."""
    sp = scored_pipeline
    kwargs = dict(
        product="MG Advanced", stage="Engaging", age_days=45,
        has_account=True, porte="Mid", has_sector=True, has_team=True,
    )
    r1 = score_row(sp.ctx, sp.ref, sp.ages_won_ordenadas, **kwargs)

    pipeline_df = sp.dataset.pipeline
    open_mask = pipeline_df["deal_stage"].isin(["Prospecting", "Engaging"])
    open_idx = pipeline_df[open_mask].index
    dropped_half_open = pipeline_df.drop(index=open_idx[: len(open_idx) // 2])
    shrunk_dataset = dataclasses.replace(sp.dataset, pipeline=dropped_half_open)

    ctx2 = build_scoring_context(shrunk_dataset)
    ref2 = build_reference_distribution(shrunk_dataset, ctx2)
    ages2 = sp.ages_won_ordenadas  # negócios ganhos não foram tocados

    r2 = score_row(ctx2, ref2, ages2, **kwargs)

    assert r1["prioridade"] == r2["prioridade"]
    assert r1["score"] == r2["score"]
    assert r1["confianca"] == r2["confianca"]


def test_feature_exclusion_account_and_agent_do_not_move_score(scored_pipeline):
    """Mesmo produto e mesma idade, contas/vendedores diferentes -> mesmo
    p̂, CONFIANÇA e ESTADO; VALOR só pode diferir pelo porte."""
    sp = scored_pipeline
    kwargs = dict(
        product="GTX Pro", stage="Engaging", age_days=57,
        has_account=True, porte="Mid", has_sector=True, has_team=True,
    )
    r_a = score_row(sp.ctx, sp.ref, sp.ages_won_ordenadas, **kwargs)
    r_b = score_row(sp.ctx, sp.ref, sp.ages_won_ordenadas, **kwargs)
    assert r_a["p_hat"] == r_b["p_hat"]
    assert r_a["confianca"] == r_b["confianca"]
    assert r_a["estado"] == r_b["estado"]
    assert r_a["valor"] == r_b["valor"]


def test_setor_entra_so_na_completude_nunca_no_score(scored_pipeline):
    """Depois da remoção de `mult_setor` (2026-08-29), setor não toca p̂,
    SCORE, suporte nem a explicação — só a completude do cadastro, que
    mede a qualidade do registro, não a previsão. Duas oportunidades
    idênticas que diferem apenas em ter ou não setor cadastrado precisam
    produzir exatamente o mesmo SCORE."""
    sp = scored_pipeline
    kwargs = dict(
        product="GTX Pro", stage="Engaging", age_days=57,
        has_account=True, porte="Mid", has_team=True,
    )
    com_setor = score_row(sp.ctx, sp.ref, sp.ages_won_ordenadas, has_sector=True, **kwargs)
    sem_setor = score_row(sp.ctx, sp.ref, sp.ages_won_ordenadas, has_sector=False, **kwargs)
    for campo in ("p_hat", "prioridade", "score", "suporte", "score_fatores"):
        assert com_setor[campo] == sem_setor[campo]
    assert com_setor["completude"] > sem_setor["completude"]


def test_score_row_nao_aceita_mais_o_valor_do_setor(scored_pipeline):
    """Regressão de assinatura: `has_sector` (booleano de cadastro) segue
    existindo; `sector` (o valor) não — não há caminho de volta para o
    setor entrar no score sem reabrir a decisão."""
    import inspect

    parametros = inspect.signature(score_row).parameters
    assert "has_sector" in parametros
    assert "sector" not in parametros


def test_open_pipeline_covers_all_2089_open_opportunities(scored_pipeline):
    """Funil aberto completo: 2.089 oportunidades, toda linha que o CSV
    registra como Prospecting ou Engaging. Ficou em 1.436 entre 2026-08-21
    e 2026-08-29, quando 653 delas eram convertidas para Lost na carga —
    ver docs/decisions-log.md, entrada 2026-08-29."""
    assert len(scored_pipeline.scored) == 2089


def test_aged_deals_scored_not_purged(scored_pipeline):
    """As 653 oportunidades paradas há ≥200 dias são pontuadas como
    qualquer outra: acima da censura de 138 dias, p̂ reverte ao prior e a
    URGÊNCIA cai ao piso — elas afundam na fila por aritmética, não por
    um rótulo que nós atribuímos."""
    from scoring import constants

    scored = scored_pipeline.scored
    paradas = scored[scored["age_days"] >= 200]
    assert len(paradas) == 653
    assert (paradas["p_hat"] == constants.CENSURA_P_HAT).all()
    assert (paradas["urgencia"] == constants.CENSURA_URGENCIA).all()


def test_open_pipeline_includes_opportunities_without_account(scored_pipeline):
    scored = scored_pipeline.scored
    sem_conta = scored[scored["account"].isna()]
    assert len(sem_conta) == 1425
    assert sem_conta["prioridade"].notna().all()


def test_calibracao_so_tem_desfecho_observado(scored_pipeline):
    """A população de calibração é feita só de negócios que o CRM registra
    como fechados: 6.711 linhas, todas com close_date, idade máxima 138
    dias. Nenhum rótulo atribuído por idade entra aqui — que é o que
    permitia às curvas aprender "velho = perde" da própria régua."""
    from scoring.pipeline import fechados

    closed = fechados(scored_pipeline.dataset)
    assert len(closed) == 6711
    assert closed["close_date"].notna().all()
    idade_max = (closed["close_date"] - closed["engage_date"]).dt.days.max()
    assert idade_max == 138


def test_base_rate_63_15(scored_pipeline):
    """Taxa de vitória global sobre desfecho observado: 4.238 / 6.711 =
    63,15%. Era 57,55% com o expurgo, um valor que aliás caía fora da
    faixa 0,60-0,66 que `constants` declara como gatilho de recalibração
    de emergência."""
    from scoring.pipeline import fechados

    closed = fechados(scored_pipeline.dataset)
    base_rate = (closed["deal_stage"] == "Won").mean()
    assert round(base_rate * 100, 2) == 63.15

def test_prospecting_nunca_cai_em_revisao_lote(scored_pipeline):
    scored = scored_pipeline.scored
    prospecting = scored[scored["deal_stage"] == "Prospecting"]
    assert (prospecting["estado"] != "revisao_lote").all()
    assert (prospecting["sem_precedente"] == False).all()  # noqa: E712


def test_revisao_lote_e_o_passivo_real(scored_pipeline):
    revisao = scored_pipeline.scored
    revisao = revisao[revisao["estado"] == "revisao_lote"]
    assert (revisao["age_days"] > 138).all()
    assert (revisao["deal_stage"] != "Prospecting").all()


def test_estado_distribution_matches_expected(scored_pipeline):
    counts = scored_pipeline.scored["estado"].value_counts().to_dict()
    # revisao_lote encolhe muito com a reclassificação de 200 dias: a maior
    # parte do que antes era ">138d sem precedente" agora já saiu do funil
    # aberto como Lost (add-analise-carga-fit).
    assert counts.get("revisao_lote", 0) > 300
    assert counts.get("prioritize", 0) > 0
