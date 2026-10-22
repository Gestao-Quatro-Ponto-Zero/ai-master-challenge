"""Página local pra preencher o gabarito no navegador.

Lê casos_teste.csv, mostra um ticket por cartão e salva cada resposta
na hora em gabarito_preenchido.csv (mesma pasta).

Uso: python3 gabarito_servidor.py   e abrir http://localhost:8765
"""
import csv
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AQUI = Path(__file__).parent
CASOS = AQUI / "casos_teste.csv"
SAIDA = AQUI / "gabarito_preenchido.csv"
CAMPOS = ["acao", "nunca_dizer", "observacao"]


def ler_casos():
    with open(CASOS, encoding="utf-8-sig") as f:
        return [{k: v for k, v in r.items() if not k.startswith("GABARITO")} for r in csv.DictReader(f)]


def ler_respostas():
    if not SAIDA.exists():
        return {}
    with open(SAIDA, encoding="utf-8-sig") as f:
        return {r["id"]: {c: r[c] for c in CAMPOS} for r in csv.DictReader(f)}


def salvar(respostas):
    with open(SAIDA, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", *CAMPOS])
        for id_ in sorted(respostas):
            w.writerow([id_, *(respostas[id_].get(c, "") for c in CAMPOS)])


class Handler(BaseHTTPRequestHandler):
    def _json(self, dado):
        corpo = json.dumps(dado, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path == "/dados":
            return self._json({"casos": ler_casos(), "respostas": ler_respostas()})
        corpo = (AQUI / "gabarito.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        if self.path != "/salvar":
            self.send_error(404)
            return
        tamanho = int(self.headers.get("Content-Length", 0))
        item = json.loads(self.rfile.read(tamanho))
        respostas = ler_respostas()
        respostas[item["id"]] = {c: item.get(c, "") for c in CAMPOS}
        salvar(respostas)
        self._json({"ok": True})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Gabarito em http://localhost:8765")
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
