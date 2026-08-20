"""Task 2.9.1 — SCORE como percentil contra a distribuição de referência."""

from scoring.reference import ReferenceDistribution


def test_percentil_of_minimum_is_near_zero():
    ref = ReferenceDistribution(prioridades_ordenadas=[10.0, 20.0, 30.0, 40.0])
    assert ref.percentil(10.0) < 20.0


def test_percentil_of_maximum_is_near_hundred():
    ref = ReferenceDistribution(prioridades_ordenadas=[10.0, 20.0, 30.0, 40.0])
    assert ref.percentil(40.0) > 80.0


def test_percentil_rounded_to_one_decimal():
    ref = ReferenceDistribution(prioridades_ordenadas=[1.0, 2.0, 3.0])
    result = ref.percentil(2.0)
    assert result == round(result, 1)


def test_mediana_matches_score_cutoff_semantics(scored_pipeline):
    # SCORE=50 é, por definição, a mediana da própria distribuição de
    # referência — o corte de ESTADO não precisa de uma constante à parte.
    # Tolerância folgada porque a distribuição de PRIORIDADE tem muitos
    # empates (poucos produtos, poucos portes), o que desloca ligeiramente
    # o percentil exato da mediana dentro de um platô de valores repetidos.
    ref = scored_pipeline.ref
    assert abs(ref.percentil(ref.mediana) - 50.0) <= 2.0
