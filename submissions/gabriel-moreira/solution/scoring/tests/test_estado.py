"""Requirement "Atribuição de estado" — árvore de decisão sobre SCORE e CONFIANÇA."""

from scoring.estado import estado


def test_alto_valor_com_confianca_maxima():
    assert estado(score=97.0, confianca_valor=100.0, sem_precedente=False) == "prioritize"


def test_mesmo_score_confianca_menor_ainda_prioriza():
    assert estado(score=97.0, confianca_valor=40.0, sem_precedente=False) == "prioritize"


def test_confianca_maxima_nao_basta_sem_valor():
    assert estado(score=30.0, confianca_valor=100.0, sem_precedente=False) == "acompanhar"


def test_confianca_minima_com_valor_potencial_vira_qualificar():
    assert estado(score=65.0, confianca_valor=20.0, sem_precedente=False) == "qualificar"


def test_confianca_minima_e_valor_baixo():
    assert estado(score=20.0, confianca_valor=20.0, sem_precedente=False) == "qualificar"


def test_estado_dos_sem_precedente_independe_do_score_e_confianca():
    assert estado(score=99.9, confianca_valor=100.0, sem_precedente=True) == "revisao_lote"
    assert estado(score=0.0, confianca_valor=0.0, sem_precedente=True) == "revisao_lote"


def test_ausencia_de_precedente_domina_o_score():
    assert estado(score=99.0, confianca_valor=100.0, sem_precedente=True) == "revisao_lote"


def test_falta_informacao_nao_valor():
    assert estado(score=60.0, confianca_valor=40.0, sem_precedente=False) == "qualificar"


def test_fundamento_solido_prioridade_intermediaria():
    assert estado(score=60.0, confianca_valor=80.0, sem_precedente=False) == "acompanhar"


def test_boundary_score_95_e_inclusivo():
    assert estado(score=95.0, confianca_valor=100.0, sem_precedente=False) == "prioritize"
    assert estado(score=94.9, confianca_valor=100.0, sem_precedente=False) != "prioritize"


def test_boundary_confianca_50_qualifica_abaixo_dele():
    assert estado(score=60.0, confianca_valor=49.9, sem_precedente=False) == "qualificar"
    assert estado(score=60.0, confianca_valor=50.0, sem_precedente=False) == "acompanhar"
