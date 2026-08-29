"""Self-check da lógica de domínio (probabilidade + priorização).
Roda: python3 test_dominio.py (a partir de solution/src/)
"""
import pandas as pd

from priorizacao import calcular_dias_desde_engajamento, priorizar_pipeline_aberto
from probabilidade import calcular_tabela_sobrevivencia, probabilidade_por_dias


def test_probabilidade_por_dias_usa_faixa_certa():
    tabela = [(10.0, 0.3), (30.0, 0.6), (100.0, 0.9)]
    assert probabilidade_por_dias(5, tabela) == 0.3
    assert probabilidade_por_dias(10, tabela) == 0.3
    assert probabilidade_por_dias(11, tabela) == 0.6
    assert probabilidade_por_dias(999, tabela) == 0.9, "fora do range treinado deve usar a última faixa"


def test_calcular_tabela_sobrevivencia_e_monotona_em_dias():
    fechados = pd.DataFrame(
        {
            "dias_ciclo": [1, 2, 3, 4, 50, 51, 52, 53, 100, 101, 102, 103],
            "ganhou": [0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1],
        }
    )
    tabela = calcular_tabela_sobrevivencia(fechados, n_faixas=3)
    limites = [limite for limite, _taxa in tabela]
    assert limites == sorted(limites), "faixas precisam vir ordenadas por dias crescente"
    assert tabela[0][1] < tabela[-1][1], "faixa de mais dias deve ter taxa de vitória maior nesse fixture"


def test_dias_desde_engajamento_sem_data_e_zero():
    assert calcular_dias_desde_engajamento(pd.NaT) == 0.0


def test_dias_desde_engajamento_calcula_diferenca():
    referencia = pd.Timestamp("2017-12-31")
    dias = calcular_dias_desde_engajamento(pd.Timestamp("2017-12-01"), referencia)
    assert dias == 30


def test_priorizar_pipeline_aberto_ordena_por_valor_esperado_desc():
    df = pd.DataFrame(
        {
            "deal_stage": ["Engaging", "Engaging", "Prospecting", "Won"],
            "engage_date": [pd.Timestamp("2017-01-01"), pd.Timestamp("2017-12-01"), pd.NaT, pd.Timestamp("2017-01-01")],
            "sales_price": [1000.0, 100.0, 500.0, 999.0],
        }
    )
    tabela = [(10.0, 0.2), (400.0, 0.8)]
    resultado = priorizar_pipeline_aberto(df, tabela)

    assert len(resultado) == 3, "Won não é pipeline aberto, não deve entrar"
    assert list(resultado["valor_esperado"]) == sorted(resultado["valor_esperado"], reverse=True)
    assert resultado.iloc[0]["deal_stage"] == "Engaging"  # 800 de valor esperado, o maior do fixture


if __name__ == "__main__":
    testes = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for teste in testes:
        teste()
        print(f"ok  {teste.__name__}")
    print(f"\n{len(testes)} testes passaram")
