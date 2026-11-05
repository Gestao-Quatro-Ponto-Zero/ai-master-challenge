"""Compara a regra de palavras e modelos do OpenRouter nas frases congeladas.

Uso: OPENROUTER_API_KEY=... python3 analysis/avalia_sugestao.py modelo1 modelo2 ...
As frases e os rótulos foram escritos antes de qualquer modelo ver as frases.
"""
import csv
import json
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from prova.estatistica import wilson  # noqa: E402
from prova.sugestao import ErroDaSugestao, Sugestor, regra_de_palavras  # noqa: E402

LIMITE_DE_GASTO = 0.05
EM_PARALELO = 8


def medir(previstos, rotulos):
    acertos = sum(p == r for p, r in zip(previstos, rotulos))
    baixo, alto = wilson(acertos, len(rotulos))
    return {
        "acertos": acertos,
        "total": len(rotulos),
        "acuracia": acertos / len(rotulos),
        "ic95": [baixo, alto],
        # O erro mais caro: dar por encerrado um negócio que ainda existe.
        "vivos_ou_depois_marcados_como_encerrados": sum(
            r in ("vivo", "depois") and p in ("perdido", "errado") for p, r in zip(previstos, rotulos)
        ),
        "encerrados_marcados_como_vivos": sum(
            r in ("perdido", "errado") and p in ("vivo", "depois") for p, r in zip(previstos, rotulos)
        ),
        "confusao": dict(Counter(f"{r}>{p}" for p, r in zip(previstos, rotulos) if p != r)),
    }


def main():
    linhas = list(csv.DictReader(open(RAIZ / "analysis" / "notas_teste.csv", encoding="utf-8")))
    rotulos = [l["rotulo"] for l in linhas]
    saida = {"frases": len(linhas), "regra_de_palavras": medir([regra_de_palavras(l["texto"]) for l in linhas], rotulos), "modelos": {}}
    gasto = 0.0
    destino = RAIZ / "analysis" / "resultados_sugestao.json"

    for modelo in sys.argv[1:]:
        if gasto > LIMITE_DE_GASTO:
            raise SystemExit(f"Limite de gasto atingido em ${gasto:.4f}")

        def classificar(linha, modelo=modelo):
            sugestor = Sugestor.do_ambiente()
            sugestor.modelo = modelo
            inicio = time.monotonic()
            try:
                r = sugestor.sugerir(linha["texto"])
                return r["resposta"], time.monotonic() - inicio, float(r["uso"].get("cost") or 0), None
            except ErroDaSugestao as erro:
                return "falha", time.monotonic() - inicio, 0.0, str(erro)

        with ThreadPoolExecutor(EM_PARALELO) as grupo:
            respostas = list(grupo.map(classificar, linhas))
        custo = sum(r[2] for r in respostas)
        gasto += custo
        saida["modelos"][modelo] = {
            **medir([r[0] for r in respostas], rotulos),
            "falhas": sum(r[3] is not None for r in respostas),
            "erros": dict(Counter(r[3] for r in respostas if r[3])),
            "tempo_mediano_s": statistics.median(r[1] for r in respostas),
            "custo_total_usd": custo,
            "previstos": [r[0] for r in respostas],
        }
        destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    saida["gasto_total_usd"] = gasto
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in saida.items() if k != "modelos"}, ensure_ascii=False))
    for modelo, r in saida["modelos"].items():
        print(modelo, {k: v for k, v in r.items() if k != "previstos"})


if __name__ == "__main__":
    main()
