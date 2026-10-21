"""Testes da API — rodam contra o dataset real em backend/data."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
# Segunda-feira a 27 dias do fim do Q4 — data usada para exercitar o modo emergência
DATA_PRESSAO = "2017-12-04"


def test_saude():
    r = client.get("/saude")
    assert r.status_code == 200
    assert 0.6 < r.json()["auc_calibracao"] <= 1


def test_pipeline_ordenado_por_acao_e_valor_esperado():
    acoes = client.get("/filtros").json()["acoes"]
    deals = client.get("/pipeline?limite=5000").json()["deals"]
    chave = [(acoes.index(d["acao"]), -d["valor_esperado"]) for d in deals]
    assert chave == sorted(chave)


def test_score_explicado():
    deals = client.get("/pipeline?limite=50").json()["deals"]
    for d in deals:
        assert 0 <= d["score"] <= 100
        assert {m["pilar"] for m in d["motivos"]} == {"chance", "valor", "dados"}
        assert round(sum(m["pontos"] for m in d["motivos"])) == d["score"]
        assert 0 <= d["probabilidade"] <= 1


def test_calibracao_monotonica_e_regra_do_teto():
    cal = client.get("/benchmarks").json()["calibracao"]
    calibrado = [f["calibrado"] for f in cal["curva"]]
    assert calibrado == sorted(calibrado)
    # Muito acima de 0,50 (o que vendedor/conta/produto davam). Entre deals vivos o
    # sinal é moderado; somando a regra do teto, o pipeline inteiro fica bem ordenado.
    assert cal["auc"] > 0.6
    assert cal["auc_com_teto"] > 0.7
    # A regra "fora do ciclo = perdido" se sustenta no backtest
    assert cal["zumbis_que_ganharam"] == 0


def test_zumbi_sem_valor_esperado_e_fora_da_fila():
    deals = client.get("/pipeline?stage=Engaging&limite=5000").json()["deals"]
    zumbi = next(d for d in deals if d["fora_do_ciclo"])
    assert zumbi["acao"] in ("Requalificar", "Encerrar")
    assert zumbi["valor_esperado"] == 0
    fila = client.get("/alertas").json()["alertas"]
    assert not any(a["tipo"] == "fora_do_ciclo" for a in fila)
    assert any(a["tipo"] == "limpeza" for a in fila)


def test_teto_de_criticos_por_vendedor():
    fila = client.get(f"/alertas?data={DATA_PRESSAO}").json()["alertas"]
    por_agente = {}
    for a in fila:
        if a["severidade"] == "critico" and a.get("opportunity_id"):
            por_agente[a["agente"]] = por_agente.get(a["agente"], 0) + 1
    assert all(n <= 3 for n in por_agente.values())


def test_alertas_ordenados_por_severidade():
    ordem = {"critico": 0, "atencao": 1, "lembrete": 2}
    sev = [ordem[a["severidade"]] for a in client.get("/alertas").json()["alertas"]]
    assert sev == sorted(sev)


def test_emergencia_lista_de_resgate():
    r = client.get(f"/emergencia?data={DATA_PRESSAO}").json()
    assert r["na_janela"]
    assert r["trimestre"]["dias_restantes"] == 27
    if r["ativa"] and r["resgate"]["n"]:
        valores = [d["valor_esperado"] for d in r["resgate"]["deals"]]
        assert valores == sorted(valores, reverse=True)
        assert all(d["stage"] == "Engaging" for d in r["resgate"]["deals"])


def test_snapshot_nao_vaza_futuro():
    # Em 04/12, nenhum deal aberto pode ter sido engajado depois dessa data
    deals = client.get(f"/pipeline?data={DATA_PRESSAO}&limite=5000").json()["deals"]
    assert deals and all(d["engage_date"] <= DATA_PRESSAO for d in deals)
    assert not any(d["stage"] == "Prospecting" for d in deals)


def test_time_e_cross_sell():
    t = client.get("/time").json()
    assert len(t["vendedores"]) == 35
    cs = client.get("/cross-sell").json()
    assert all(s["serie_sugerida"] not in s["series_compradas"] for s in cs["sugestoes"])


def test_calibracao_rolling_origin_nao_usa_o_futuro():
    from app.main import MOTOR
    import pandas as pd
    t = pd.Timestamp(DATA_PRESSAO)
    cal = MOTOR.backtest.para_data(t)
    # Só observações cujo desfecho já era conhecido em t
    assert cal.n_observacoes == int((MOTOR.backtest.obs.fim <= t).sum())
    assert cal.n_observacoes < MOTOR.calibracao.n_observacoes
    assert all(pd.Timestamp(d) <= t for d in cal.datas)
    # No começo do dataset não há histórico: chance bruta, e a interface avisa
    assert client.get("/benchmarks?data=2017-04-03").json()["calibracao"]["calibrada"] is False


def test_prospecting_tem_trilha_propria_sem_chance():
    deals = client.get("/pipeline?stage=Prospecting&limite=5000").json()["deals"]
    assert deals
    for d in deals:
        assert d["acao"] == "Primeiro contato"
        assert d["probabilidade"] is None and d["valor_esperado"] == 0
        assert next(m for m in d["motivos"] if m["pilar"] == "chance")["texto"].startswith("Chance n/d")


def test_faixa_de_incerteza_contem_a_chance():
    deals = client.get(f"/pipeline?data={DATA_PRESSAO}&acao=Atacar%20agora&limite=50").json()["deals"]
    for d in deals:
        assert d["prob_min"] <= d["probabilidade"] <= d["prob_max"]


def test_filtros_invalidos():
    assert client.get("/pipeline?regiao=Marte").status_code == 400
    assert client.get("/pipeline?data=2010-01-01").status_code == 400
