"""Requirement "Explicabilidade do score e plano de ação"."""

from scoring import constants
from scoring.explicacao import (
    fatores_score,
    fracao_vitorias_ate,
    plano_de_acao,
    plano_de_acao_passos,
)
from scoring.model import Componentes


def test_fracao_vitorias_ate_is_percentage():
    ages = [10.0, 20.0, 30.0, 40.0]
    assert fracao_vitorias_ate(ages, 30.0) == 75.0
    assert fracao_vitorias_ate(ages, 100.0) == 100.0
    assert fracao_vitorias_ate(ages, 0.0) == 0.0


def test_explicacao_revisao_lote_recommends_batch_review():
    componentes = Componentes(p_hat=0.632, preco_tabela=1096.0, valor=1000.0, urgencia=0.15, prioridade=94.8)
    razao = "confiança limitada por ausência de precedente: nenhum negócio ganho fechou nesta faixa de idade"
    texto = plano_de_acao("revisao_lote", razao, age_days=200, componentes=componentes)
    assert "revisão em lote" in texto
    assert "precedente histórico" in texto


def test_explicacao_qualificar_nomeia_campos_ausentes():
    componentes = Componentes(p_hat=0.637, preco_tabela=550.0, valor=550.0, urgencia=0.47, prioridade=164.71)
    campos = ["conta", "funcionários", "setor"]
    razao = "confiança limitada pela completude do cadastro: faltam conta, funcionários, setor"
    texto = plano_de_acao(
        "qualificar", razao, age_days=None, componentes=componentes, campos_ausentes=campos
    )
    assert "conta" in texto and "funcionários" in texto and "setor" in texto


def test_explicacao_prioritize_mentions_fraction_of_wins():
    componentes = Componentes(p_hat=0.764, preco_tabela=5865.74, valor=5865.74, urgencia=1.0, prioridade=4482.0)
    razao = "completude e suporte equivalentes — nenhuma metade domina o mínimo"
    texto = plano_de_acao(
        "prioritize", razao, age_days=122, componentes=componentes,
        ages_won_ordenadas=[10.0, 50.0, 100.0, 130.0],
    )
    assert "%" in texto
    assert "priorize contato" in texto.lower()


def test_acompanhar_e_qualificar_nao_convergem():
    componentes = Componentes(p_hat=0.6, preco_tabela=1000.0, valor=1000.0, urgencia=0.5, prioridade=300.0)
    razao = "irrelevante para este teste"
    texto_acompanhar = plano_de_acao("acompanhar", razao, age_days=30.0, componentes=componentes)
    texto_qualificar = plano_de_acao(
        "qualificar", razao, age_days=30.0, componentes=componentes, campos_ausentes=["conta"]
    )
    assert texto_acompanhar != texto_qualificar
    assert "obtenha essa informação" in texto_qualificar.lower()
    assert "obtenha essa informação" not in texto_acompanhar.lower()


def _todos_estados_variacoes():
    for estado_key in constants.ESTADOS:
        for has_account in (True, False):
            for campos in ([], ["conta"], ["conta", "setor", "funcionários"]):
                yield estado_key, has_account, campos


def test_plano_de_acao_passos_quantidade_dentro_do_limite():
    for estado_key, has_account, campos in _todos_estados_variacoes():
        passos = plano_de_acao_passos(estado_key, has_account, campos)
        assert 2 <= len(passos) <= 4


def test_plano_de_acao_passos_enriquecimento_apenas_sem_conta():
    for estado_key in constants.ESTADOS:
        com_conta = plano_de_acao_passos(estado_key, has_account=True, campos_ausentes=[])
        sem_conta = plano_de_acao_passos(estado_key, has_account=False, campos_ausentes=[])
        assert not any("enriqueça o cadastro" in p.lower() for p in com_conta)
        assert any("enriqueça o cadastro" in p.lower() for p in sem_conta)
        assert sem_conta[0].lower().startswith("enriqueça o cadastro")


def test_plano_de_acao_passos_qualificar_contem_passo_de_informacao():
    passos_qualificar = plano_de_acao_passos("qualificar", has_account=True, campos_ausentes=["setor"])
    passos_acompanhar = plano_de_acao_passos("acompanhar", has_account=True, campos_ausentes=[])
    assert any("dados ausentes" in p.lower() for p in passos_qualificar)
    assert not any("dados ausentes" in p.lower() for p in passos_acompanhar)


def test_plano_de_acao_passos_revisao_lote_direciona_gestor():
    passos = plano_de_acao_passos("revisao_lote", has_account=True, campos_ausentes=[])
    assert any("lote de revisão" in p.lower() for p in passos)


def test_plano_de_acao_passos_determinismo():
    for estado_key, has_account, campos in _todos_estados_variacoes():
        primeira = plano_de_acao_passos(estado_key, has_account, campos)
        segunda = plano_de_acao_passos(estado_key, has_account, campos)
        assert primeira == segunda


def test_plano_de_acao_passos_sem_separador_do_csv(scored_pipeline):
    for passos in scored_pipeline.scored["plano_de_acao_passos"]:
        for passo in passos:
            assert "|" not in passo


def test_fatores_score_quatro_frases_nao_tecnicas():
    componentes = Componentes(p_hat=0.65, preco_tabela=26768.0, valor=5865.74, urgencia=0.5, prioridade=1906.37)
    fatores = fatores_score(
        componentes, product="GTK 500", porte="Enterprise", has_account=True,
        stage="Engaging", age_days=60,
    )
    assert len(fatores) == 4
    for termo_tecnico in ("p_hat", "p̂", "PRIORIDADE", "URGÊNCIA"):
        assert not any(termo_tecnico in f for f in fatores)


def test_fatores_score_produto_mais_caro_do_catalogo_eleva_prioridade():
    componentes = Componentes(p_hat=0.65, preco_tabela=26768.0, valor=26768.0, urgencia=0.5, prioridade=8699.6)
    fatores = fatores_score(
        componentes, product="GTK 500", porte=None, has_account=False,
        stage="Prospecting", age_days=None,
    )
    assert any("maior valor de tabela" in f for f in fatores)


def test_fatores_score_produto_mais_barato_do_catalogo_nao_eleva():
    componentes = Componentes(p_hat=0.64, preco_tabela=55.0, valor=55.0, urgencia=0.47, prioridade=16.5)
    fatores = fatores_score(
        componentes, product="MG Special", porte=None, has_account=False,
        stage="Prospecting", age_days=None,
    )
    assert any("menor valor de tabela" in f for f in fatores)


def test_fatores_score_sem_conta_nao_favorece_nem_penaliza():
    componentes = Componentes(p_hat=0.632, preco_tabela=550.0, valor=550.0, urgencia=0.47, prioridade=163.5)
    fatores = fatores_score(
        componentes, product="GTX Basic", porte=None, has_account=False,
        stage="Prospecting", age_days=None,
    )
    assert any("sem conta vinculada" in f for f in fatores)


def test_fatores_score_conta_enterprise_eleva_valor():
    componentes = Componentes(p_hat=0.632, preco_tabela=550.0, valor=583.0, urgencia=0.47, prioridade=173.5)
    fatores = fatores_score(
        componentes, product="GTX Basic", porte="Enterprise", has_account=True,
        stage="Prospecting", age_days=None,
    )
    assert any("Enterprise" in f and "eleva" in f for f in fatores)


def test_fatores_score_conta_smb_reduz_valor():
    componentes = Componentes(p_hat=0.632, preco_tabela=550.0, valor=522.5, urgencia=0.47, prioridade=155.6)
    fatores = fatores_score(
        componentes, product="GTX Basic", porte="SMB", has_account=True,
        stage="Prospecting", age_days=None,
    )
    assert any("SMB" in f and "reduz" in f for f in fatores)


def test_fatores_score_idade_dentro_da_janela_menciona_precedente_historico():
    componentes = Componentes(p_hat=0.72, preco_tabela=4821.0, valor=4821.0, urgencia=0.83, prioridade=2879.0)
    fatores = fatores_score(
        componentes, product="GTX Pro", porte="Mid", has_account=True,
        stage="Engaging", age_days=90,
    )
    assert any("chance igual ou maior de fechar" in f for f in fatores)


def test_fatores_score_prospecting_nao_menciona_tempo_decorrido():
    componentes = Componentes(p_hat=0.6484, preco_tabela=4821.0, valor=4821.0, urgencia=0.47, prioridade=1467.9)
    fatores = fatores_score(
        componentes, product="GTX Pro", porte=None, has_account=False,
        stage="Prospecting", age_days=None,
    )
    assert not any("chance igual ou maior de fechar" in f for f in fatores)


def test_fatores_score_determinismo():
    componentes = Componentes(p_hat=0.65, preco_tabela=1096.0, valor=1096.0, urgencia=0.5, prioridade=356.2)
    kwargs = dict(
        componentes=componentes, product="GTX Plus Basic", porte="Upper",
        has_account=True, stage="Engaging", age_days=40,
    )
    assert fatores_score(**kwargs) == fatores_score(**kwargs)


# ---------------------------------------------------------------------------
# Setor fora da explicação — `mult_setor` removido em 2026-08-29
# (`constants.py`). A quinta frase, que descrevia o ajuste de setor, saiu
# junto: explicar um fator que o score não usa seria explicar o número
# errado.
# ---------------------------------------------------------------------------


def test_fatores_score_tem_sempre_quatro_frases_e_nenhuma_de_setor():
    componentes = Componentes(
        p_hat=0.66, preco_tabela=4821.0, valor=4821.0, urgencia=0.5, prioridade=1591.0
    )
    for porte, has_account, stage, age_days in (
        ("Mid", True, "Engaging", 60),
        (None, False, "Prospecting", None),
    ):
        fatores = fatores_score(
            componentes,
            product="GTX Pro",
            porte=porte,
            has_account=has_account,
            stage=stage,
            age_days=age_days,
        )
        assert len(fatores) == 4
        assert not any("setor" in f.lower() for f in fatores)


def test_fatores_score_nao_aceita_mais_setor_como_insumo():
    """Regressão: a assinatura não expõe `ctx`/`sector` — nenhum chamador
    consegue reintroduzir a frase de setor sem reabrir a decisão."""
    import inspect

    parametros = inspect.signature(fatores_score).parameters
    assert "sector" not in parametros
    assert "ctx" not in parametros
