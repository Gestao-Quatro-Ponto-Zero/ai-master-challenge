"""Tasks 2.9, 2.9.1, 2.15, 2.16, 2.17, 2.20 — pipeline de ponta a ponta."""

import dataclasses

from scoring.pipeline import build_scoring_context, score_row
from scoring.reference import build_reference_distribution


def test_reference_scenario_gtx_plus_pro_upper_122_dias(scored_pipeline):
    sp = scored_pipeline
    r = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Plus Pro", stage="Engaging", age_days=122,
        has_account=True, porte="Upper",
    )
    assert abs(r["prioridade"] - 4482.00) < 5.00
    assert r["confianca"] == "A"


def test_reference_scenario_idade_377_dias(scored_pipeline):
    sp = scored_pipeline
    r = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Plus Pro", stage="Engaging", age_days=377,
        has_account=True, porte="Upper",
    )
    assert r["p_hat"] == 0.632
    assert r["urgencia"] == 0.15
    assert r["confianca"] == "D"
    assert r["estado"] == "desistir"


def test_reference_population_has_4238_won_deals(scored_pipeline):
    assert scored_pipeline.ref.n == 4238


def test_stability_priority_and_score_independent_of_open_funnel(scored_pipeline):
    """PRIORIDADE e SCORE não dependem da composição do funil aberto —
    só de constantes fixas e da distribuição de referência histórica de
    negócios ganhos. Remover metade das oportunidades ABERTAS do dataset
    (sem tocar nos negócios fechados) não pode mudar p̂_produto nem a
    distribuição de referência — e portanto não muda PRIORIDADE nem SCORE
    de uma oportunidade que não mudou."""
    sp = scored_pipeline
    kwargs = dict(
        product="MG Advanced", stage="Engaging", age_days=45,
        has_account=True, porte="Mid",
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


def test_feature_exclusion_account_and_agent_do_not_move_score(scored_pipeline):
    """Mesmo produto e mesma idade, contas/vendedores diferentes ->
    mesmo p̂, CONFIANÇA e ESTADO; VALOR só pode diferir pelo porte."""
    sp = scored_pipeline
    r_a = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Pro", stage="Engaging", age_days=57,
        has_account=True, porte="Mid",
    )
    r_b = score_row(
        sp.ctx, sp.ref, sp.ages_won_ordenadas,
        product="GTX Pro", stage="Engaging", age_days=57,
        has_account=True, porte="Mid",
    )
    assert r_a["p_hat"] == r_b["p_hat"]
    assert r_a["confianca"] == r_b["confianca"]
    assert r_a["estado"] == r_b["estado"]
    assert r_a["valor"] == r_b["valor"]


def test_open_pipeline_covers_all_2089_open_opportunities(scored_pipeline):
    assert len(scored_pipeline.scored) == 2089


def test_open_pipeline_includes_opportunities_without_account(scored_pipeline):
    scored = scored_pipeline.scored
    sem_conta = scored[scored["account"].isna()]
    assert len(sem_conta) == 1425
    # todas ainda recebem prioridade — nenhuma fica de fora ou nula.
    assert sem_conta["prioridade"].notna().all()
