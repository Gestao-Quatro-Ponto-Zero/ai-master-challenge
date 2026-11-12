import json
import socket
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from run import Manipulador, fabrica_manipulador


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def servidor(tmp_path, dados_dir, config):
    from build import construir
    app_data = tmp_path / "app" / "data"
    construir(dados_dir, config, saida=app_data, hoje="2018-01-01")
    acoes = tmp_path / "acoes.jsonl"

    porta = _porta_livre()
    handler = fabrica_manipulador(diretorio_app=tmp_path / "app", arquivo_acoes=acoes)
    httpd = ThreadingHTTPServer(("127.0.0.1", porta), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{porta}", acoes, app_data
    finally:
        httpd.shutdown()


def _post(url, corpo: bytes, content_type="application/json"):
    req = urllib.request.Request(url, data=corpo, method="POST", headers={"Content-Type": content_type})
    try:
        r = urllib.request.urlopen(req)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_post_valido_grava_e_responde_201(servidor):
    base, acoes, app_data = servidor
    scored = json.loads((app_data / "scored.json").read_text())
    oid = scored["deals"][0]["opportunity_id"]
    status, _ = _post(f"{base}/acao", json.dumps({
        "vendedor": scored["deals"][0]["vendedor"], "opportunity_id": oid, "acao": "feito",
    }).encode())
    assert status == 201
    linhas = acoes.read_text().strip().splitlines()
    assert len(linhas) == 1
    gravado = json.loads(linhas[0])
    assert gravado["opportunity_id"] == oid and "ts" in gravado


def test_opportunity_id_inexistente_responde_400_sem_gravar(servidor):
    base, acoes, _ = servidor
    status, _ = _post(f"{base}/acao", json.dumps({
        "vendedor": "Alguém", "opportunity_id": "NAOEXISTE", "acao": "feito",
    }).encode())
    assert status == 400
    assert not acoes.exists() or acoes.read_text() == ""


def test_corpo_nao_json_responde_400(servidor):
    base, acoes, _ = servidor
    status, _ = _post(f"{base}/acao", b"isto nao e json")
    assert status == 400
    assert not acoes.exists() or acoes.read_text() == ""


def test_acao_fora_do_conjunto_responde_400(servidor):
    base, acoes, app_data = servidor
    scored = json.loads((app_data / "scored.json").read_text())
    oid = scored["deals"][0]["opportunity_id"]
    status, _ = _post(f"{base}/acao", json.dumps({
        "vendedor": scored["deals"][0]["vendedor"], "opportunity_id": oid, "acao": "qualquer_coisa",
    }).encode())
    assert status == 400
    assert not acoes.exists() or acoes.read_text() == ""


def test_get_acoes_devolve_o_que_foi_gravado(servidor):
    base, acoes, app_data = servidor
    scored = json.loads((app_data / "scored.json").read_text())
    oid = scored["deals"][0]["opportunity_id"]
    _post(f"{base}/acao", json.dumps({
        "vendedor": scored["deals"][0]["vendedor"], "opportunity_id": oid, "acao": "adiar",
    }).encode())
    r = urllib.request.urlopen(f"{base}/acoes")
    corpo = json.loads(r.read())
    assert len(corpo) == 1 and corpo[0]["opportunity_id"] == oid and corpo[0]["acao"] == "adiar"
