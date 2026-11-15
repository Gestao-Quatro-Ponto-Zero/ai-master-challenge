"""Servidor HTTP do Lead Scorer: API JSON e arquivos da interface (pasta web), só com a biblioteca padrão.

Uso: python3 server.py  (porta pela variável PORT, padrão 8000; interface pela variável HOST, padrão 127.0.0.1).
"""
from __future__ import annotations

import gzip
import json
import mimetypes
import os
import signal
import sys
import threading
import time
import traceback
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlsplit

from engine import accounts, core, model_page, proof, quality, seller, team

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")
GZIP_MIN_BYTES = 512
CACHE_SIZE = 256
IDLE_TIMEOUT = 30  # segundos que uma conexão parada segura uma thread
JSON_TYPE = "application/json; charset=utf-8"
ERROR_TEXTS = {
    HTTPStatus.BAD_REQUEST: "Requisição inválida.",
    HTTPStatus.REQUEST_URI_TOO_LONG: "Endereço longo demais.",
    HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE: "Cabeçalhos grandes demais.",
    HTTPStatus.HTTP_VERSION_NOT_SUPPORTED: "Versão de HTTP não suportada.",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}
COMPRESSIBLE = (".html", ".css", ".js", ".mjs", ".svg", ".json", ".txt")
MISSING_UI = ("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><title>Lead Scorer</title></head>"
              "<body><h1>Interface não encontrada</h1><p>O arquivo web/index.html não existe. "
              "A API continua disponível em /api/meta.</p></body></html>").encode("utf-8")


# ---------------------------------------------------------------- rotas da API

Params = Dict[str, Optional[str]]


def _date(ds: core.Dataset, p: Params):
    return core.parse_date(ds, p.get("date"))


def _required(p: Params, key: str) -> str:
    value = p.get(key)
    if not value:
        raise core.InputError("Informe o parâmetro \"%s\"." % key)
    return value


# Cada rota: (parâmetros aceitos, função que recebe a base e os parâmetros).
ROUTES: Dict[str, Tuple[Tuple[str, ...], Callable[[core.Dataset, Params], Any]]] = {
    "/api/meta": ((), lambda ds, p: quality.meta(ds)),
    "/api/login": (("date",), lambda ds, p: quality.login(ds, _date(ds, p))),
    "/api/seller": (("name", "date"), lambda ds, p: seller.focus(ds, _date(ds, p), _required(p, "name"))),
    "/api/pipeline": (("name", "date"), lambda ds, p: seller.pipeline(ds, _date(ds, p), _required(p, "name"))),
    "/api/team": (("date", "manager", "region", "seller"), lambda ds, p: team.team(
        ds, _date(ds, p), manager=p.get("manager"), region=p.get("region"), seller=p.get("seller"))),
    "/api/accounts": (("date", "region"), lambda ds, p: accounts.listing(ds, _date(ds, p), p.get("region"))),
    "/api/account": (("date", "name", "viewer"), lambda ds, p: accounts.detail(
        ds, _date(ds, p), _required(p, "name"), viewer=p.get("viewer"))),
    "/api/time-machine": (("date", "name"), lambda ds, p: proof.time_machine(
        ds, _date(ds, p), _required(p, "name"))),
    "/api/proof": ((), lambda ds, p: proof.proof(ds)),
    "/api/score-model": (("date", "viewer"), lambda ds, p: model_page.score_model(
        ds, _date(ds, p), viewer=p.get("viewer"))),
    "/api/data-quality": (("date",), lambda ds, p: quality.data_quality(ds, _date(ds, p))),
    "/api/sources": ((), lambda ds, p: quality.sources(ds)),
}


class ResponseCache:
    """Corpos JSON já serializados (e comprimidos), por rota e parâmetros. As respostas são determinísticas."""

    def __init__(self, size: int = CACHE_SIZE) -> None:
        self._items: "OrderedDict[tuple, Dict[str, bytes]]" = OrderedDict()
        self._size = size
        self._lock = threading.Lock()

    def get(self, key: tuple) -> Optional[Dict[str, bytes]]:
        with self._lock:
            item = self._items.get(key)
            if item is not None:
                self._items.move_to_end(key)
            return item

    def put(self, key: tuple, item: Dict[str, bytes]) -> None:
        with self._lock:
            self._items[key] = item
            self._items.move_to_end(key)
            while len(self._items) > self._size:
                self._items.popitem(last=False)


def encode_json(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def compress(body: bytes) -> bytes:
    return gzip.compress(body, compresslevel=6, mtime=0)


def accepts_gzip(header: Optional[str]) -> bool:
    """True se Accept-Encoding aceita gzip (respeita "gzip;q=0")."""
    for part in (header or "").split(","):
        token, _, params = part.strip().partition(";")
        if token.strip().lower() not in ("gzip", "*"):
            continue
        q = params.replace(" ", "").lower()
        if not q.startswith("q="):
            return True
        try:
            return float(q[2:]) > 0
        except ValueError:
            return False
    return False


# ---------------------------------------------------------------- handler

class Handler(BaseHTTPRequestHandler):
    server_version = "LeadScorer/1.0"
    protocol_version = "HTTP/1.1"
    timeout = IDLE_TIMEOUT

    def version_string(self) -> str:
        return self.server_version  # sem a versão do Python no cabeçalho Server

    # -- métodos
    def do_GET(self) -> None:
        self._dispatch()

    do_HEAD = do_GET

    def _not_allowed(self) -> None:
        # o corpo da requisição não é lido: fechar a conexão evita que ele vire o começo da próxima
        self.close_connection = True
        self._send(HTTPStatus.METHOD_NOT_ALLOWED, encode_json({"error": "Método não permitido. Use GET."}),
                   JSON_TYPE, "no-store", extra={"Allow": "GET, HEAD", "Connection": "close"})

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _not_allowed

    def send_error(self, code: int, message: Optional[str] = None, explain: Optional[str] = None) -> None:
        """Erros da própria biblioteca (linha inválida, endereço longo, verbo desconhecido) em JSON."""
        if code == HTTPStatus.NOT_IMPLEMENTED:  # verbo sem do_X: mesmo contrato dos outros métodos
            self._not_allowed()
            return
        self.close_connection = True
        self._send(code, encode_json({"error": ERROR_TEXTS.get(code, ERROR_TEXTS[HTTPStatus.BAD_REQUEST])}),
                   JSON_TYPE, "no-store", extra={"Connection": "close"})

    # -- roteamento
    def _dispatch(self) -> None:
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
        elif path == "/api" or path.startswith("/api/"):
            self._api(path)
        else:
            self._static(path)

    def _api(self, path: str) -> None:
        started = time.perf_counter()
        route = ROUTES.get(path.rstrip("/") or path)
        if route is None:
            status = self._send_json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada: %s" % core.echo(path)})
            self._log_api(path, status, started)
            return
        accepted, func = route
        query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
        params: Params = {k: (query[k][-1].strip() or None) if k in query else None for k in accepted}
        key = (path.rstrip("/"),) + tuple(params[k] for k in accepted)
        cached = self.server.cache.get(key)
        if cached is None:
            try:
                body = encode_json(func(self.server.dataset(), params))
            except core.InputError as exc:
                status = self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                self._log_api(path, status, started)
                return
            except Exception:  # noqa: BLE001  (inclusive ValueError interno: log completo só no stderr)
                traceback.print_exc(file=sys.stderr)
                status = self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                         {"error": "Erro interno. Tente de novo em instantes."})
                self._log_api(path, status, started)
                return
            cached = {"plain": body}
            self.server.cache.put(key, cached)
        self._send_bytes(HTTPStatus.OK, cached, JSON_TYPE, "no-store")
        self._log_api(path, HTTPStatus.OK, started)

    def _static(self, path: str) -> None:
        web = self.server.web_dir
        target = self._resolve_static(web, path)
        if target is None and os.path.splitext(path)[1]:
            # arquivo (com extensão) que não existe: 404, e não o index.html no lugar de um .js
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Arquivo não encontrado."})
            return
        if target is None:
            target = os.path.join(web, "index.html")
            if not os.path.isfile(target):
                self._send(HTTPStatus.NOT_FOUND, MISSING_UI, CONTENT_TYPES[".html"], "no-cache")
                return
        ext = os.path.splitext(target)[1].lower()
        ctype = CONTENT_TYPES.get(ext) or mimetypes.guess_type(target)[0] or "application/octet-stream"
        with open(target, "rb") as f:
            body = f.read()
        item = {"plain": body}
        if ext in COMPRESSIBLE:
            self._send_bytes(HTTPStatus.OK, item, ctype, "no-cache")
        else:
            self._send(HTTPStatus.OK, body, ctype, "no-cache")

    @staticmethod
    def _resolve_static(web: str, path: str) -> Optional[str]:
        """Arquivo existente dentro de web/; None se não existir, for oculto ou escapar da pasta."""
        rel = unquote(path).lstrip("/")
        if not rel or "\x00" in rel or rel.endswith("/"):
            return None
        if any(part.startswith(".") for part in rel.replace("\\", "/").split("/") if part):
            return None
        root = os.path.realpath(web)
        full = os.path.realpath(os.path.join(root, rel))
        if os.path.commonpath([root, full]) != root or not os.path.isfile(full):
            return None
        return full

    # -- envio
    def _send_json(self, status: int, data: Any) -> int:
        self._send_bytes(status, {"plain": encode_json(data)}, JSON_TYPE, "no-store")
        return status

    def _send_bytes(self, status: int, item: Dict[str, bytes], ctype: str, cache: str) -> None:
        """Envia item["plain"], ou a versão gzip (guardada no próprio item) quando o cliente aceita."""
        body, extra = item["plain"], {"Vary": "Accept-Encoding"}
        headers = getattr(self, "headers", None)  # ausente quando a linha da requisição é inválida
        if len(body) >= GZIP_MIN_BYTES and headers is not None and accepts_gzip(headers.get("Accept-Encoding")):
            if "gzip" not in item:
                item["gzip"] = compress(body)
            body = item["gzip"]
            extra["Content-Encoding"] = "gzip"
        self._send(status, body, ctype, cache, extra)

    def _send(self, status: int, body: bytes, ctype: str, cache: str,
              extra: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # -- log
    def _log_api(self, path: str, status: int, started: float) -> None:
        if self.server.quiet:
            return
        sys.stderr.write("%s %s %d %.0f ms\n" % (self.command, self.path[:200], int(status),
                                                 (time.perf_counter() - started) * 1000))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002  (assinatura da biblioteca)
        pass  # o log de acesso padrão é substituído por _log_api

    def log_error(self, format: str, *args: Any) -> None:  # noqa: A002
        if not self.server.quiet:
            sys.stderr.write("erro: %s\n" % (format % args))


class LeadScorerServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: Tuple[str, int], web_dir: str = WEB_DIR, quiet: bool = False) -> None:
        super().__init__(address, Handler)
        self.web_dir = web_dir
        self.quiet = quiet
        self.cache = ResponseCache()

    @staticmethod
    def dataset() -> core.Dataset:
        return core.get_dataset()


def warm_up() -> None:
    """Carrega a base e calcula a data padrão e a prova, para a primeira visita não esperar."""
    try:
        ds = core.get_dataset()
        core.snapshot(ds, core.DEFAULT_DATE)
        proof.proof(ds)
        model_page.tested_signals(ds)
        quality.meta(ds)
    except Exception:  # noqa: BLE001  (a requisição que precisar refaz o cálculo e devolve o erro)
        traceback.print_exc(file=sys.stderr)


def main() -> None:
    raw_port = os.environ.get("PORT") or "8000"
    if not raw_port.isdigit() or not 0 < int(raw_port) < 65536:
        sys.exit("PORT precisa ser um número de porta (recebi %r). Exemplo: PORT=8001 python3 server.py" % raw_port)
    port = int(raw_port)
    host = os.environ.get("HOST") or "127.0.0.1"
    try:
        server = LeadScorerServer((host, port))
    except OSError as error:
        sys.exit("Não consegui abrir a porta %d (%s). Tente outra: PORT=%d python3 server.py"
                 % (port, error.strerror or error, port + 1))
    threading.Thread(target=warm_up, name="warm-up", daemon=True).start()

    def stop(*_: Any) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    shown = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
    print("Lead Scorer rodando em http://%s:%d (Ctrl+C para encerrar)" % (shown, port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Servidor encerrado.", flush=True)


if __name__ == "__main__":
    main()
