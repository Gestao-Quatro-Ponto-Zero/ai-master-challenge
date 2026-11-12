import pytest

from ia.validar import validar
from ia.briefing import template_vendedor


@pytest.fixture
def fatos():
    return {
        "nome": "Boris Faz",
        "semana_do_trimestre": 1,
        "n_fechar": 1,
        "n_preparar": 4,
        "n_iniciar": 2,
        "n_encerrar": 3,
        "valor_encerrar": 12000.0,
        "ve_trimestre": 850.5,
        "sem_nada_vivo": False,
        "foco": [
            {"produto": "GTX Pro", "conta": "Cancity", "valor": 4821.0,
             "idade": 10, "dias_restantes": 5, "fila": "fechar"},
            {"produto": "GTX Basic", "conta": None, "valor": 550.0,
             "idade": 40, "dias_restantes": 50, "fila": "preparar"},
        ],
    }


@pytest.fixture
def fatos_sem_fechar(fatos):
    return {**fatos, "n_fechar": 0, "foco": [
        {**fatos["foco"][0], "fila": "preparar"},
        fatos["foco"][1],
    ]}


@pytest.fixture
def fatos_vazios():
    return {
        "nome": "Carl Lin",
        "semana_do_trimestre": 1,
        "n_fechar": 0,
        "n_preparar": 0,
        "n_iniciar": 0,
        "n_encerrar": 0,
        "valor_encerrar": 0.0,
        "ve_trimestre": 0.0,
        "sem_nada_vivo": True,
        "foco": [],
    }


def test_recusa_numero_fora_de_marcador(fatos):
    ok, motivo = validar("Você tem {n_fechar} deals e US$ 12.000 parados.", fatos)
    assert not ok and "número" in motivo


def test_recusa_conta_inventada(fatos):
    assert not validar("Ligue para a Acme Corporation hoje.", {**fatos, "foco": []})[0]


def test_recusa_promessa(fatos):
    assert not validar("O deal {conta_1} vai fechar com certeza.", fatos)[0]


def test_recusa_chance_quando_a_tabela_diz_zero(fatos_sem_fechar):
    ok, motivo = validar("Dois deals devem decidir nas próximas semanas.", fatos_sem_fechar)
    assert not ok and "chance" in motivo


def test_aceita_template(fatos):
    assert validar(template_vendedor(fatos), fatos)[0]


def test_template_do_vendedor_sem_nada_vivo(fatos_vazios):
    t = template_vendedor(fatos_vazios)
    assert "não há" in t.lower() and validar(t, fatos_vazios)[0]
