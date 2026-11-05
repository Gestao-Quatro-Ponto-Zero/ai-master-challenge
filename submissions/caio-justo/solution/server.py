#!/usr/bin/env python3
"""Servidor da ferramenta. Uso: python3 server.py  (abre em http://localhost:8000)"""
import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from prova.banco import Banco  # noqa: E402
from prova.servico import ErroDeEntrada, Servico  # noqa: E402

WEB = RAIZ / "web"
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".woff2": "font/woff2"}
TAMANHO_MAXIMO = 64 * 1024


class Aplicacao:
    def __init__(self, pasta_estado: Path):
        pasta_estado.mkdir(parents=True, exist_ok=True)
        self.servico = Servico(RAIZ / "analysis" / "resultados.json")
        self.bancos = {
            "real": Banco(pasta_estado / "respostas.db"),
            "demo": Banco(pasta_estado / "demonstracao.db"),
        }

    def banco(self, modo: str) -> Banco:
        if modo not in self.bancos:
            raise ErroDeEntrada("Modo inválido")
        return self.bancos[modo]


def criar_manipulador(app: Aplicacao):
    class Manipulador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):
            pass

        def _json(self, dados, estado=HTTPStatus.OK):
            corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self.send_response(estado)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def _estatico(self, caminho: str):
            alvo = (WEB / (caminho.lstrip("/") or "index.html")).resolve()
            if WEB.resolve() not in alvo.parents or not alvo.is_file():
                return self._json({"erro": "Não encontrado"}, HTTPStatus.NOT_FOUND)
            corpo = alvo.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", TIPOS.get(alvo.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(corpo)

        def _tratar(self, funcao):
            try:
                funcao()
            except ErroDeEntrada as erro:
                self._json({"erro": str(erro)}, HTTPStatus.BAD_REQUEST)
            except (KeyError, ValueError, TypeError):
                self._json({"erro": "Pedido inválido"}, HTTPStatus.BAD_REQUEST)

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            modo = q.get("modo", "real")
            rotas = {
                "/api/filtros": lambda: self._json(app.servico.filtros()),
                "/api/semana": lambda: self._json(app.servico.semana(q["vendedor"], app.banco(modo))),
                "/api/head": lambda: self._json(
                    app.servico.visao_head(app.banco(modo), q.get("manager"), q.get("regiao"))
                ),
                "/api/limpeza.csv": lambda: self._csv(app.servico.limpeza_csv(app.banco(modo))),
            }
            if url.path in rotas:
                return self._tratar(rotas[url.path])
            return self._estatico(url.path)

        def _csv(self, texto: str):
            corpo = texto.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="negocios-parados.csv"')
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_POST(self):
            def executar():
                tamanho = int(self.headers.get("Content-Length", 0))
                if tamanho > TAMANHO_MAXIMO:
                    raise ErroDeEntrada("Pedido grande demais")
                d = json.loads(self.rfile.read(tamanho) or b"{}")
                caminho = urlparse(self.path).path
                modo = d.get("modo", "real")
                banco = app.banco(modo)
                s = app.servico
                if caminho == "/api/checagem":
                    s.responder_checagem(banco, d["negocio"], d.get("resposta"), d["vendedor"])
                elif caminho == "/api/resultado":
                    s.registrar_resultado(banco, d["negocio"], d.get("resultado"), d["vendedor"])
                elif caminho == "/api/adiar":
                    s.adiar(banco, d["negocio"], bool(d["adiado"]), d["vendedor"])
                elif caminho == "/api/demo/simular":
                    s.simular(app.banco("demo"), float(d.get("viva", 0.2)), float(d.get("efeito", 0.1)))
                elif caminho == "/api/demo/limpar":
                    app.banco("demo").limpar()
                else:
                    return self._json({"erro": "Não encontrado"}, HTTPStatus.NOT_FOUND)
                self._json({"ok": True})

            self._tratar(executar)

    return Manipulador


def main():
    parser = argparse.ArgumentParser(description="Lead Scorer que se prova")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--estado", type=Path, default=RAIZ / ".estado", help="pasta dos bancos de respostas")
    args = parser.parse_args()
    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), criar_manipulador(Aplicacao(args.estado)))
    print(f"Lead Scorer que se prova em http://localhost:{args.porta}")
    servidor.serve_forever()


if __name__ == "__main__":
    main()
