import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import triagem  # noqa: E402
from comum import OUT_DIR, SEED, ler_ds1, ler_ds2  # noqa: E402
from f5_injecao import carregar_ataques, montar_pares  # noqa: E402

GOLDEN = {c["caso"]: c for c in map(json.loads, (Path(__file__).parent / "golden" / "golden_v1.jsonl").read_text(encoding="utf-8").splitlines())}


@pytest.fixture(autouse=True)
def runtime_isolado(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGEM_RUNTIME_DIR", str(tmp_path))
    monkeypatch.delenv("TRIAGEM_MODO", raising=False)
    return tmp_path


def log(tmp):
    p = tmp / "decisoes.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


@pytest.mark.parametrize("caso", ["texto_vazio", "duas_palavras"])
def test_texto_insuficiente(caso):
    g = GOLDEN[caso]
    r = triagem.triar(g["entrada"])
    assert r["faixa"] == g["esperado"]["faixa"] and r["motivo"] == g["esperado"]["motivo"]


def test_idempotencia(runtime_isolado):
    g = GOLDEN["duplicado"]
    r1, r2 = triagem.triar(g["entrada"]), triagem.triar(g["entrada"])
    assert r1["duplicado"] is False and r2["duplicado"] is g["esperado"]["duplicado_no_reenvio"]
    assert len(log(runtime_isolado)) == g["esperado"]["decisoes_no_log"]


def test_idempotencia_sem_event_id_usa_hash(runtime_isolado):
    e = {"texto": "Laptop   screen BROKEN need new monitor", "canal": "Email"}
    triagem.triar(e)
    assert triagem.triar({"texto": "laptop screen broken need new monitor", "canal": "Email"})["duplicado"]
    assert not triagem.triar({"texto": "laptop screen broken need new monitor", "canal": "Chat"})["duplicado"]


def test_mascaramento_golden(runtime_isolado):
    g = GOLDEN["dado_pessoal"]
    triagem.triar(g["entrada"])
    bruto = (runtime_isolado / "decisoes.jsonl").read_text(encoding="utf-8")
    for s in g["esperado"]["ausente_no_log"]:
        assert s.lower() not in bruto.lower(), s


def test_mascaramento_20_clientes_ds1(runtime_isolado):
    # nomes e e-mails do DS1 (sintéticos) usados só em tempo de teste; nada é gravado no repositório
    ds1 = ler_ds1().sample(20, random_state=SEED)
    for i, (nome, email) in enumerate(zip(ds1["Customer Name"], ds1["Customer Email"])):
        triagem.triar({"event_id": f"pii-{i}", "nome_cliente": nome,
                       "texto": f"hello my name is {nome} email {email} phone (21) 99876-5432 cpf 98765432100 please reset password"})
    bruto = (runtime_isolado / "decisoes.jsonl").read_text(encoding="utf-8").lower()
    for nome, email in zip(ds1["Customer Name"], ds1["Customer Email"]):
        assert email.lower() not in bruto
        assert nome.lower() not in bruto
        for parte in nome.split():
            if len(parte) >= 3:
                assert f" {parte.lower()} " not in bruto, parte
    assert "99876-5432" not in bruto and "98765432100" not in bruto


def test_regra_de_acao_reembolso():
    g = GOLDEN["reembolso_alta_confianca"]
    sem = triagem.triar({"texto": g["entrada"]["texto"], "event_id": "sem-regra"})
    com = triagem.triar(g["entrada"])
    assert sem["faixa"] == g["esperado"]["faixa_sem_regra_de_acao"]
    assert com["faixa"] == g["esperado"]["faixa"]


def test_fallback_classificador(monkeypatch, runtime_isolado):
    def quebra(_):
        raise RuntimeError("modelo não carregado")
    monkeypatch.setattr(triagem, "classificar", quebra)
    g = GOLDEN["falha_classificador"]
    r = triagem.triar(g["entrada"])
    assert r["faixa"] == g["esperado"]["faixa"] and r["motivo"] == g["esperado"]["motivo"]
    assert "RuntimeError" in log(runtime_isolado)[0]["erro"]


def test_nunca_lanca_excecao(monkeypatch):
    monkeypatch.setattr(triagem, "_db", lambda: (_ for _ in ()).throw(OSError("disco cheio")))
    r = triagem.triar({"texto": "hi please reset my password"})
    assert r["faixa"] == "humano decide" and "OSError" in r["erro"]


def test_modo_sombra(monkeypatch, runtime_isolado):
    monkeypatch.setenv("TRIAGEM_MODO", "sombra")
    g = GOLDEN["modo_sombra"]
    r = triagem.triar(g["entrada"])
    assert r["faixa"] == g["esperado"]["faixa"]
    assert log(runtime_isolado)[0]["faixa_sem_sombra"] == g["esperado"]["faixa_sem_sombra"]


@pytest.mark.parametrize("caso", ["portugues_1", "portugues_2", "portugues_3"])
def test_portugues_nao_cai_em_ia_decide(caso):
    g = GOLDEN[caso]
    assert triagem.triar(g["entrada"])["faixa"] != g["esperado"]["faixa_diferente_de"]


@pytest.fixture(scope="module")
def holdout():
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    return df[df["split_grupo"] == "holdout"]


def test_injecao_classico_nao_vai_para_alvo(holdout):
    # 3 tickets fixos: os 3 primeiros do sorteio seed 42 usado em f5_injecao.py
    tickets = holdout.sample(20, random_state=SEED).head(3)
    m = triagem.carregar_modelo()["pipeline"]
    limpa = dict(zip(tickets["id"], m.predict(tickets["Document"])))
    pares = montar_pares(tickets, limpa, sorted(m.classes_))
    assert len(pares) == 3 * len(carregar_ataques())
    for p, pred in zip(pares, m.predict([p["texto"] for p in pares])):
        assert pred != p["alvo"], (p["id"], p["ataque"])


def test_portao_de_qualidade(holdout):
    g = GOLDEN["portao_qualidade"]["esperado"]
    m = triagem.carregar_modelo()["pipeline"]
    proba = m.predict_proba(holdout["Document"])
    pred, pmax = m.classes_[proba.argmax(1)], proba.max(1)
    acerto = pred == holdout["Topic_group"].values
    faixa = np.array([triagem.faixa_para(c, p) for c, p in zip(pred, pmax)])
    assert acerto.mean() >= g["acuracia_min"]
    assert acerto[faixa == "IA decide"].mean() >= g["precisao_ia_decide_min"]
