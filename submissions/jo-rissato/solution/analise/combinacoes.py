"""Piores combinações de canal, prioridade e tipo, com teste de permutação contra o acaso.

Duas medidas, cada uma na base em que o dado existe:
1. Horas entre 1ª resposta e resolução: só fechados com registro coerente (resolução depois da
   1ª resposta). Pior = maior mediana.
2. % sem resposta (status Open): 100% dos tickets. Pior = maior %.
Para cada cruzamento, os valores do desfecho são embaralhados N vezes; a pior combinação real só
é considerada real se passar do percentil 95 da pior combinação obtida por acaso.

Uso: python combinacoes.py <csv> <saida.md>
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

CRUZAMENTOS = [
    (["Ticket Channel", "Ticket Priority"], "Canal × prioridade", 30),
    (["Ticket Priority", "Ticket Type"], "Prioridade × tipo", 30),
    (["Ticket Channel", "Ticket Type"], "Canal × tipo", 30),
    (["Ticket Channel", "Ticket Priority", "Ticket Type"], "Canal × prioridade × tipo", 8),
]
ROTULOS = {"Phone": "Telefone", "Chat": "Chat", "Email": "E-mail", "Social media": "Redes sociais",
           "Low": "Baixa", "Medium": "Média", "High": "Alta", "Critical": "Crítica",
           "Refund request": "Reembolso", "Cancellation request": "Cancelamento",
           "Billing inquiry": "Cobrança", "Technical issue": "Problema técnico",
           "Product inquiry": "Dúvida de produto"}
N_PERM = 1000


def pior(df: pd.DataFrame, chaves: list[str], alvo: str, minimo: int, agg: str) -> tuple:
    g = df.groupby(chaves)[alvo].agg([agg, "size"])
    g = g[g["size"] >= minimo]
    k = g[agg].idxmax()
    return (k if isinstance(k, tuple) else (k,)), g.loc[k, agg], int(g.loc[k, "size"])


def tabela(df: pd.DataFrame, alvo: str, agg: str, fmt, titulo: str, base: str) -> list[str]:
    rng = np.random.default_rng(0)
    md = [f"## {titulo}", "", base, "",
          "| Cruzamento | Pior combinação real | Tickets | Pior por acaso (mediana) | Limite do acaso (95%) | Real? |",
          "|---|---|---|---|---|---|"]
    for chaves, nome, minimo in CRUZAMENTOS:
        k, v, n = pior(df, chaves, alvo, minimo, agg)
        sim = []
        d = df[chaves].copy()
        for _ in range(N_PERM):
            d[alvo] = rng.permutation(df[alvo].values)
            sim.append(pior(d, chaves, alvo, minimo, agg)[1])
        p95 = float(np.percentile(sim, 95))
        md.append(f"| {nome} | {' / '.join(ROTULOS.get(x, x) for x in k)} | {n} | {fmt(np.median(sim))} | "
                  f"{fmt(p95)} | {'sim' if v > p95 else 'não'} ({fmt(v)}) |")
    return md + [""]


def main(origem: str, saida: str) -> None:
    df = pd.read_csv(origem)
    df["sem_resposta"] = (df["Ticket Status"] == "Open").astype(float) * 100
    f = df[df["Ticket Status"] == "Closed"].copy()
    f["horas"] = (pd.to_datetime(f["Time to Resolution"])
                  - pd.to_datetime(f["First Response Time"])).dt.total_seconds() / 3600
    validos = f[f["horas"] >= 0]
    md = ["# Piores combinações: real ou acaso?", "",
          f"Teste de permutação com {N_PERM} embaralhamentos por cruzamento. Mínimo de 30 tickets por "
          "combinação (8 no cruzamento triplo).", ""]
    md += tabela(validos, "horas", "median", lambda x: f"{x:.1f} h",
                 "1. Tempo até resolver (mediana de horas)",
                 f"Base: {len(validos)} tickets fechados com registro coerente, de {len(df)} no total. "
                 f"Os outros não têm tempo de resolução ({len(df) - len(f)} não fechados) "
                 f"ou têm resolução antes da 1ª resposta ({len(f) - len(validos)}).")
    md += tabela(df, "sem_resposta", "mean", lambda x: f"{x:.1f}%",
                 "2. Tickets sem nenhuma resposta (%)", f"Base: {len(df)} tickets, 100% do Dataset 1.")
    with open(saida, "w", encoding="utf-8") as h:
        h.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
