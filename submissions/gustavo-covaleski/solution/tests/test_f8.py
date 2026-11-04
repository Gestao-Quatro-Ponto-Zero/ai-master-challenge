import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import pytest

SOLUTION = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, SOLUTION)
import triagem  # noqa: E402

N_PROC, N_EVENTOS = 6, 10


@pytest.fixture(autouse=True)
def runtime_isolado(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGEM_RUNTIME_DIR", str(tmp_path))
    monkeypatch.delenv("TRIAGEM_MODO", raising=False)
    return tmp_path


def decisoes(tmp):
    linhas = [json.loads(l) for l in (tmp / "decisoes.jsonl").read_text(encoding="utf-8").splitlines()]
    return [l for l in linhas if l.get("tipo") != "duplicado"], [l for l in linhas if l.get("tipo") == "duplicado"]


# ---- Parte A: idempotência ----

def test_sem_colisao_de_digitos(runtime_isolado):
    a = triagem.triar({"texto": "pedido 1111 notebook nao liga", "canal": "Email"})
    b = triagem.triar({"texto": "pedido 2222 notebook nao liga", "canal": "Email"})
    assert a["chave"] != b["chave"] and not a["duplicado"] and not b["duplicado"]
    assert len(decisoes(runtime_isolado)[0]) == 2


def test_mesmo_texto_mesmo_canal_duplicado():
    e = {"texto": "pedido 1111 notebook nao liga", "canal": "Chat"}
    assert not triagem.triar(e)["duplicado"]
    assert triagem.triar(dict(e))["duplicado"]


def test_janela_anterior_conta_como_duplicado(monkeypatch):
    e = {"texto": "pedido 3333 monitor quebrado", "canal": "Phone"}
    agora = 1_000_000 * triagem.JANELA_S + triagem.JANELA_S - 1  # último segundo da janela
    monkeypatch.setattr(triagem.time, "time", lambda: agora)
    assert not triagem.triar(e)["duplicado"]
    monkeypatch.setattr(triagem.time, "time", lambda: agora + 2)  # virou a janela
    assert triagem.triar(e)["duplicado"]


def _trabalhador(runtime, barreira, fila, idx):
    # nível do módulo: precisa ser importável no spawn do Windows
    os.environ["TRIAGEM_RUNTIME_DIR"] = runtime
    sys.path.insert(0, SOLUTION)
    import triagem as t
    t.carregar_modelo(); t.carregar_politica()
    barreira.wait()
    out = [t.triar({"event_id": f"corrida-{i}", "texto": "hi please reset my password account locked cannot login"})
           for i in range(N_EVENTOS)]
    fila.put([(r.get("duplicado"), r.get("motivo")) for r in out])


def test_corrida_multiprocesso(runtime_isolado):
    ctx = mp.get_context("spawn")
    barreira, fila = ctx.Barrier(N_PROC), ctx.Queue()
    procs = [ctx.Process(target=_trabalhador, args=(str(runtime_isolado), barreira, fila, i)) for i in range(N_PROC)]
    for p in procs:
        p.start()
    res = [r for _ in procs for r in fila.get(timeout=300)]
    for p in procs:
        p.join(timeout=60)
    assert len(res) == N_PROC * N_EVENTOS
    assert sum(1 for _, m in res if m == "falha interna") == 0
    assert sum(1 for d, _ in res if not d) == N_EVENTOS
    dec, dup = decisoes(runtime_isolado)
    por_evento = {}
    for l in dec:
        por_evento[l["event_id"]] = por_evento.get(l["event_id"], 0) + 1
    assert por_evento == {f"corrida-{i}": 1 for i in range(N_EVENTOS)}
    assert len(dup) == N_PROC * N_EVENTOS - N_EVENTOS


def test_falha_no_log_libera_reserva(monkeypatch, runtime_isolado):
    original = triagem._log

    def quebra(linha, arquivo="decisoes.jsonl"):
        raise OSError("disco cheio")
    monkeypatch.setattr(triagem, "_log", quebra)
    e = {"event_id": "falha-log-1", "texto": "hi please reset my password account locked cannot login"}
    r1 = triagem.triar(e)
    assert r1["motivo"] == "falha interna"
    monkeypatch.setattr(triagem, "_log", original)
    r2 = triagem.triar(e)
    assert not r2["duplicado"] and r2["faixa"] != "" and r2["motivo"] != "falha interna"
    assert len(decisoes(runtime_isolado)[0]) == 1


def test_duplicado_grava_linha_no_log(runtime_isolado):
    e = {"event_id": "dup-log-1", "texto": "hi please reset my password account locked cannot login"}
    triagem.triar(e)
    triagem.triar(e)
    dec, dup = decisoes(runtime_isolado)
    assert len(dec) == 1 and len(dup) == 1
    assert dup[0]["chave"] == "evt:dup-log-1" and "texto_mascarado" not in dup[0] and dup[0]["timestamp_utc"]


# ---- Parte C: versão do modelo e rollback ----

class _PipelineFalso:
    pass


def test_versao_escolhida_pela_variavel(tmp_path, monkeypatch):
    import joblib
    cache = tmp_path / "cache"
    cache.mkdir()
    for v in ("aaaaaaaaaaaa", "bbbbbbbbbbbb"):
        joblib.dump({"pipeline": _PipelineFalso(), "versao": v}, cache / f"modelo_{v}.joblib")
    monkeypatch.setenv("TRIAGEM_CACHE_DIR", str(cache))
    monkeypatch.setenv("TRIAGEM_MODELO_VERSAO", "aaaaaaaaaaaa")
    assert triagem.carregar_modelo()["versao"] == "aaaaaaaaaaaa"
    monkeypatch.setenv("TRIAGEM_MODELO_VERSAO", "bbbbbbbbbbbb")
    assert triagem.carregar_modelo()["versao"] == "bbbbbbbbbbbb"
    assert sorted(p.name for p in cache.iterdir()) == ["modelo_aaaaaaaaaaaa.joblib", "modelo_bbbbbbbbbbbb.joblib"]


def test_versao_inexistente_vira_fallback(tmp_path, monkeypatch, runtime_isolado):
    monkeypatch.setenv("TRIAGEM_CACHE_DIR", str(tmp_path / "vazio"))
    monkeypatch.setenv("TRIAGEM_MODELO_VERSAO", "000000000000")
    r = triagem.triar({"event_id": "rollback-1", "texto": "hi please reset my password account locked cannot login"})
    assert r["faixa"] == "humano decide" and r["motivo"] == "falha do classificador"
    assert "FileNotFoundError" in r["erro"]
    assert not (tmp_path / "vazio").exists() or not any((tmp_path / "vazio").iterdir())  # não treinou


def test_versao_atual_depende_dos_splits_e_parametros():
    v = triagem.versao_atual()
    assert len(v) == 12 and v == triagem.versao_atual()
