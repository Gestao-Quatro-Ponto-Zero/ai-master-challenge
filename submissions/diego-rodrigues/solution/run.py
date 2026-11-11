"""Um comando: resolve e imprime a data, roda o build, roda o briefing, serve app/ e grava ações."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd

from build import construir

RAIZ = Path(__file__).parent
ACOES_VALIDAS = {"feito", "adiar", "nao_vivo"}


def resolver_hoje(config: dict, hoje_cli: str | None) -> pd.Timestamp:
    valor = hoje_cli or config.get("hoje")
    if valor is None:
        raise SystemExit("hoje é obrigatório: passe --hoje AAAA-MM-DD ou defina config.hoje")
    return pd.Timestamp(valor)


def fabrica_manipulador(diretorio_app: Path, arquivo_acoes: Path):
    """Cria a classe Manipulador fechada sobre `diretorio_app` e `arquivo_acoes` (SimpleHTTPRequestHandler usa classe, não instância)."""

    class _Manipulador(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(diretorio_app), **kwargs)

        def _escrever_json(self, status: int, corpo: dict | list) -> None:
            dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)

        def _ids_validos(self) -> set[str]:
            scored_path = diretorio_app / "data" / "scored.json"
            if not scored_path.exists():
                return set()
            scored = json.loads(scored_path.read_text(encoding="utf-8"))
            return {d["opportunity_id"] for d in scored["deals"]}

        def do_GET(self):
            if self.path == "/acoes":
                linhas = []
                if arquivo_acoes.exists():
                    for linha in arquivo_acoes.read_text(encoding="utf-8").splitlines():
                        if linha.strip():
                            linhas.append(json.loads(linha))
                self._escrever_json(200, linhas)
                return
            super().do_GET()

        def do_POST(self):
            if self.path != "/acao":
                self._escrever_json(404, {"erro": "rota não encontrada"})
                return

            tamanho = int(self.headers.get("Content-Length", 0))
            corpo_bruto = self.rfile.read(tamanho)
            try:
                corpo = json.loads(corpo_bruto)
            except json.JSONDecodeError:
                self._escrever_json(400, {"erro": "corpo não é JSON válido"})
                return

            if not isinstance(corpo, dict):
                self._escrever_json(400, {"erro": "corpo precisa ser um objeto JSON"})
                return

            vendedor = corpo.get("vendedor")
            opportunity_id = corpo.get("opportunity_id")
            acao = corpo.get("acao")

            if not vendedor or not opportunity_id or acao not in ACOES_VALIDAS:
                self._escrever_json(400, {"erro": "esperado {vendedor, opportunity_id, acao}", "acoes_validas": sorted(ACOES_VALIDAS)})
                return

            if opportunity_id not in self._ids_validos():
                self._escrever_json(400, {"erro": f"opportunity_id desconhecido: {opportunity_id}"})
                return

            registro = {
                "vendedor": vendedor,
                "opportunity_id": opportunity_id,
                "acao": acao,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
            arquivo_acoes.parent.mkdir(parents=True, exist_ok=True)
            with open(arquivo_acoes, "a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")

            self._escrever_json(201, registro)

        def log_message(self, fmt, *args):
            pass  # silencioso: process-log guarda o que importa, não o acesso HTTP

    return _Manipulador


# Mantido para o Review Focus 5 / Tarefa 10: "Classe Manipulador exportada para teste".
# A classe real é criada por fabrica_manipulador, fechada sobre diretorio_app/arquivo_acoes.
Manipulador = fabrica_manipulador(RAIZ / "app", RAIZ / "app" / "data" / "acoes.jsonl")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Constrói, gera briefings e serve a demo local.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--sem-build", action="store_true")
    p.add_argument("--sem-ia", action="store_true")
    p.add_argument("--hoje")
    a = p.parse_args(argv)

    config = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    hoje = resolver_hoje(config, a.hoje)
    semana = int((hoje - pd.Timestamp(hoje.year, 3 * ((hoje.month - 1) // 3) + 1, 1)).days // 7 + 1)
    print(f"hoje = {hoje.date()} (semana {semana} do trimestre)")

    app_dir = RAIZ / "app"
    if not a.sem_build:
        construir(RAIZ / "data", config, saida=app_dir / "data", hoje=hoje)
        print("build gravado em", app_dir / "data")

    if not a.sem_ia:
        from ia.briefing import gerar
        scored = json.loads((app_dir / "data" / "scored.json").read_text(encoding="utf-8"))
        b = gerar(scored, sem_ia=True)  # chamada real ainda não implementada (Tarefa 9)
        (app_dir / "data" / "briefings.json").write_text(
            json.dumps(b, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        print("briefings gravados (origem: template)")

    acoes = app_dir / "data" / "acoes.jsonl"
    handler = fabrica_manipulador(app_dir, acoes)
    httpd = ThreadingHTTPServer(("0.0.0.0", a.port), handler)
    print(f"servindo em http://localhost:{a.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
